"""
CSV parsing utility with flexible column mapping.
Handles various CSV formats from different calendar exports.
"""
import csv
from datetime import datetime
from io import StringIO
from uuid import uuid4
from typing import Any
from pydantic import EmailStr, ValidationError, TypeAdapter
from app.models.schemas import Meeting

# Email validator using TypeAdapter (Pydantic v2 public API)
_email_validator = TypeAdapter(EmailStr)


# Common column name variations
COLUMN_MAPPINGS = {
    "title": ["title", "subject", "summary", "meeting_name", "event_name"],
    "start": ["start", "start_time", "start_datetime", "begin", "from"],
    "end": ["end", "end_time", "end_datetime", "finish", "to"],
    "attendees": ["attendees", "participants", "invitees", "guests"],
    "organizer": ["organizer", "organiser", "owner", "creator", "host"],
    "recurring": ["recurring", "is_recurring", "recurrence", "repeat"],
    "recurrence_rule": ["recurrence_rule", "rrule", "recurrence_pattern"],
    "notes": ["notes", "description", "details", "agenda"],
}


def parse_datetime(value: str) -> datetime:
    """
    Parse datetime from various formats.
    
    Supported formats:
    - ISO 8601: 2026-01-15T10:00:00
    - RFC 2822: Wed, 15 Jan 2026 10:00:00
    - Common: 2026-01-15 10:00:00
    - Date only: 2026-01-15 (assumes 00:00:00)
    """
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse datetime: {value}")


def parse_email_list(value: str) -> list[EmailStr]:
    """
    Parse comma/semicolon-separated email list.
    
    Args:
        value: String like "alice@example.com, bob@example.com"
    
    Returns:
        List of validated email addresses
    """
    if not value or value.strip() == "":
        return []
    
    # Split by comma or semicolon
    separators = [",", ";"]
    for sep in separators:
        if sep in value:
            emails = [e.strip() for e in value.split(sep) if e.strip()]
            break
    else:
        emails = [value.strip()]
    
    # Validate each email
    validated = []
    for email in emails:
        try:
            # Pydantic EmailStr validation
            validated.append(_email_validator.validate_python(email))
        except Exception:
            # Skip invalid emails
            continue
    
    return validated


def find_column(headers: list[str], field: str) -> str | None:
    """
    Find column name in headers using flexible mapping.
    
    Args:
        headers: List of CSV column headers
        field: Field name to find (e.g., "title", "start")
    
    Returns:
        Actual column name from CSV, or None if not found
    """
    headers_lower = [h.lower().strip() for h in headers]
    
    for variant in COLUMN_MAPPINGS.get(field, []):
        if variant.lower() in headers_lower:
            idx = headers_lower.index(variant.lower())
            return headers[idx]
    
    return None


def parse_csv(
    csv_content: str,
    notes_mapping: dict[str, str] | None = None,
) -> tuple[list[Meeting], list[str]]:
    """
    Parse CSV content into Meeting objects.
    
    Args:
        csv_content: Raw CSV string
        notes_mapping: Optional dict mapping meeting titles to notes text
    
    Returns:
        Tuple of (valid_meetings, error_messages)
    """
    meetings: list[Meeting] = []
    errors: list[str] = []
    
    try:
        reader = csv.DictReader(StringIO(csv_content))
        headers = reader.fieldnames or []
        
        # Find required columns
        title_col = find_column(headers, "title")
        start_col = find_column(headers, "start")
        end_col = find_column(headers, "end")
        attendees_col = find_column(headers, "attendees")
        
        if not all([title_col, start_col, end_col, attendees_col]):
            missing = []
            if not title_col:
                missing.append("title")
            if not start_col:
                missing.append("start")
            if not end_col:
                missing.append("end")
            if not attendees_col:
                missing.append("attendees")
            errors.append(f"Missing required columns: {', '.join(missing)}")
            return meetings, errors
        
        # Find optional columns
        organizer_col = find_column(headers, "organizer")
        recurring_col = find_column(headers, "recurring")
        recurrence_rule_col = find_column(headers, "recurrence_rule")
        notes_col = find_column(headers, "notes")
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Parse required fields
                title = row[title_col].strip()
                if not title:
                    errors.append(f"Row {row_num}: Empty title")
                    continue
                
                start_datetime = parse_datetime(row[start_col])
                end_datetime = parse_datetime(row[end_col])
                
                if end_datetime <= start_datetime:
                    errors.append(f"Row {row_num}: End time must be after start time")
                    continue
                
                duration_minutes = int((end_datetime - start_datetime).total_seconds() / 60)
                
                attendee_emails = parse_email_list(row[attendees_col])
                if not attendee_emails:
                    errors.append(f"Row {row_num}: No valid attendee emails")
                    continue
                
                # Parse optional fields
                organizer_email = None
                if organizer_col and row.get(organizer_col):
                    try:
                        organizer_email = _email_validator.validate_python(row[organizer_col].strip())
                    except Exception:
                        pass  # Organizer is optional
                
                is_recurring = False
                if recurring_col and row.get(recurring_col):
                    val = row[recurring_col].strip().lower()
                    is_recurring = val in ("true", "yes", "1", "recurring")
                
                recurrence_rule = None
                if recurrence_rule_col and row.get(recurrence_rule_col):
                    recurrence_rule = row[recurrence_rule_col].strip() or None
                
                notes_text = None
                if notes_col and row.get(notes_col):
                    notes_text = row[notes_col].strip() or None
                
                # Check notes_mapping if provided
                if notes_mapping and title in notes_mapping:
                    notes_text = notes_mapping[title]
                
                # Create Meeting object
                meeting = Meeting(
                    meeting_id=uuid4(),
                    title=title,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    duration_minutes=duration_minutes,
                    attendee_emails=attendee_emails,
                    organizer_email=organizer_email,
                    is_recurring=is_recurring,
                    recurrence_rule=recurrence_rule,
                    notes_text=notes_text,
                )
                
                meetings.append(meeting)
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue
        
    except Exception as e:
        errors.append(f"CSV parsing failed: {str(e)}")
    
    return meetings, errors

# Made with Bob
