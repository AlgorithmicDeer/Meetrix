"""
SQLite database setup and management.
Schema creation, connection handling, and demo data seeding.
"""
import logging
import aiosqlite
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)


async def create_schema() -> None:
    """Create all database tables if they don't exist."""
    schema_sql = """
    -- Sessions table
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        status TEXT NOT NULL CHECK(status IN ('processing', 'complete', 'failed')),
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
    CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);
    
    -- Meeting classifications table
    CREATE TABLE IF NOT EXISTS meeting_classifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        meeting_type TEXT NOT NULL,
        confidence REAL NOT NULL,
        FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_class_session ON meeting_classifications(session_id);
    CREATE INDEX IF NOT EXISTS idx_class_meeting ON meeting_classifications(meeting_id);

    -- Meetings table
    CREATE TABLE IF NOT EXISTS meetings (
        meeting_id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        title TEXT NOT NULL,
        start_datetime TIMESTAMP NOT NULL,
        end_datetime TIMESTAMP NOT NULL,
        duration_minutes INTEGER NOT NULL,
        attendee_emails TEXT NOT NULL,
        organizer_email TEXT,
        is_recurring BOOLEAN DEFAULT 0,
        recurrence_rule TEXT,
        meeting_type TEXT,
        notes_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_meetings_session ON meetings(session_id);
    CREATE INDEX IF NOT EXISTS idx_meetings_start ON meetings(start_datetime);
    CREATE INDEX IF NOT EXISTS idx_meetings_type ON meetings(meeting_type);
    
    -- Waste scores table
    CREATE TABLE IF NOT EXISTS waste_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        cost_factor REAL,
        decision_deficit REAL,
        participation_imbalance REAL,
        recurrence_staleness REAL,
        composite_score REAL NOT NULL,
        category TEXT NOT NULL CHECK(category IN ('High Waste', 'Medium Waste', 'Low Waste', 'High Value')),
        threshold_exceeded BOOLEAN DEFAULT 0,
        FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_waste_session ON waste_scores(session_id);
    CREATE INDEX IF NOT EXISTS idx_waste_meeting ON waste_scores(meeting_id);
    CREATE INDEX IF NOT EXISTS idx_waste_score ON waste_scores(composite_score DESC);
    CREATE INDEX IF NOT EXISTS idx_waste_threshold ON waste_scores(session_id, threshold_exceeded);
    
    -- Recommendations table
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        recommended_action TEXT NOT NULL CHECK(recommended_action IN ('cancel', 'merge', 'shorten', 'restructure', 'keep')),
        reasoning TEXT NOT NULL,
        priority INTEGER NOT NULL,
        FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_rec_session ON recommendations(session_id);
    CREATE INDEX IF NOT EXISTS idx_rec_priority ON recommendations(session_id, priority);
    
    -- Meeting health scores table
    CREATE TABLE IF NOT EXISTS meeting_health_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        has_agenda BOOLEAN,
        duration_appropriate BOOLEAN,
        attendee_fit_score REAL,
        overall_health_score REAL NOT NULL,
        FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_health_session ON meeting_health_scores(session_id);
    CREATE INDEX IF NOT EXISTS idx_health_score ON meeting_health_scores(overall_health_score DESC);
    
    -- Focus scores table
    CREATE TABLE IF NOT EXISTS focus_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        person_email TEXT NOT NULL,
        total_meeting_hours REAL,
        focus_blocks_remaining INTEGER,
        longest_focus_block_minutes INTEGER,
        focus_percentage REAL,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_focus_session ON focus_scores(session_id);
    CREATE INDEX IF NOT EXISTS idx_focus_person ON focus_scores(session_id, person_email);
    CREATE INDEX IF NOT EXISTS idx_focus_percentage ON focus_scores(focus_percentage);
    
    -- Anomalies table
    CREATE TABLE IF NOT EXISTS anomalies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        entity_type TEXT NOT NULL CHECK(entity_type IN ('meeting', 'person', 'team')),
        anomaly_type TEXT NOT NULL,
        severity TEXT NOT NULL CHECK(severity IN ('low', 'medium', 'high')),
        description TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_anomaly_session ON anomalies(session_id);
    CREATE INDEX IF NOT EXISTS idx_anomaly_severity ON anomalies(session_id, severity);
    
    -- Cascade chains table
    CREATE TABLE IF NOT EXISTS cascade_chains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        origin_meeting_id TEXT NOT NULL,
        total_cascade_cost REAL NOT NULL,
        cascade_depth INTEGER NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id),
        FOREIGN KEY (origin_meeting_id) REFERENCES meetings(meeting_id)
    );
    CREATE INDEX IF NOT EXISTS idx_cascade_session ON cascade_chains(session_id);
    CREATE INDEX IF NOT EXISTS idx_cascade_cost ON cascade_chains(total_cascade_cost DESC);
    
    -- Cascade chain meetings junction table
    CREATE TABLE IF NOT EXISTS cascade_chain_meetings (
        chain_id INTEGER NOT NULL,
        meeting_id TEXT NOT NULL,
        FOREIGN KEY (chain_id) REFERENCES cascade_chains(id),
        FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
        PRIMARY KEY (chain_id, meeting_id)
    );
    CREATE INDEX IF NOT EXISTS idx_ccm_chain ON cascade_chain_meetings(chain_id);
    CREATE INDEX IF NOT EXISTS idx_ccm_meeting ON cascade_chain_meetings(meeting_id);
    
    -- Interventions table
    CREATE TABLE IF NOT EXISTS interventions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        pre_meeting_email_template TEXT NOT NULL,
        suggested_agenda TEXT NOT NULL,
        recommended_attendee_reduction TEXT NOT NULL,
        alternative_format TEXT NOT NULL,
        FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_intervention_session ON interventions(session_id);
    CREATE INDEX IF NOT EXISTS idx_intervention_meeting ON interventions(meeting_id);
    
    -- Action items table
    CREATE TABLE IF NOT EXISTS action_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        description TEXT NOT NULL,
        assignee_email TEXT,
        followed_through BOOLEAN,
        FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_action_session ON action_items(session_id);
    CREATE INDEX IF NOT EXISTS idx_action_meeting ON action_items(meeting_id);
    
    -- Network nodes table
    CREATE TABLE IF NOT EXISTS network_nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        email TEXT NOT NULL,
        display_name TEXT NOT NULL,
        total_meeting_hours REAL,
        centrality_score REAL,
        focus_percentage REAL,
        at_risk BOOLEAN DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_node_session ON network_nodes(session_id);
    CREATE INDEX IF NOT EXISTS idx_node_centrality ON network_nodes(centrality_score DESC);
    
    -- Network edges table
    CREATE TABLE IF NOT EXISTS network_edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        person_a TEXT NOT NULL,
        person_b TEXT NOT NULL,
        co_occurrence_count INTEGER NOT NULL,
        combined_cost REAL NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_edge_session ON network_edges(session_id);
    CREATE INDEX IF NOT EXISTS idx_edge_cost ON network_edges(combined_cost DESC);
    
    -- Upcoming risks table
    CREATE TABLE IF NOT EXISTS upcoming_risks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        meeting_id TEXT NOT NULL,
        title TEXT NOT NULL,
        scheduled_datetime TIMESTAMP NOT NULL,
        attendee_emails TEXT NOT NULL,
        waste_probability REAL NOT NULL,
        risk_factors TEXT NOT NULL,
        recommended_intervention TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_risk_session ON upcoming_risks(session_id);
    CREATE INDEX IF NOT EXISTS idx_risk_probability ON upcoming_risks(waste_probability DESC);
    
    -- Reports table
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL UNIQUE,
        period TEXT NOT NULL,
        total_cost REAL,
        total_meetings INTEGER,
        meetrix_score REAL NOT NULL,
        summary TEXT,
        key_findings TEXT NOT NULL,
        top_recommendations TEXT NOT NULL,
        trend_direction TEXT CHECK(trend_direction IN ('improving', 'worsening', 'stable')),
        data_residency TEXT NOT NULL DEFAULT 'All data processed and stored locally. No external API calls.',
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_report_session ON reports(session_id);
    CREATE INDEX IF NOT EXISTS idx_report_score ON reports(meetrix_score DESC);
    
    -- ROI projections table
    CREATE TABLE IF NOT EXISTS roi_projections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL UNIQUE,
        projected_annual_saving REAL NOT NULL,
        weeks_to_break_even INTEGER NOT NULL,
        top_changes TEXT NOT NULL,
        assumptions TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_roi_session ON roi_projections(session_id);
    
    -- Agent events table
    CREATE TABLE IF NOT EXISTS agent_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        tier INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('queued', 'running', 'complete', 'failed', 'skipped')),
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        error_message TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_event_session ON agent_events(session_id);
    CREATE INDEX IF NOT EXISTS idx_event_agent ON agent_events(session_id, agent_name);

    -- Transcripts table
    CREATE TABLE IF NOT EXISTS transcripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        content TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE INDEX IF NOT EXISTS idx_transcript_session ON transcripts(session_id);
    CREATE INDEX IF NOT EXISTS idx_transcript_meeting ON transcripts(meeting_id);
    """
    
    try:
        # Ensure data directory exists
        db_path = Path(settings.DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiosqlite.connect(settings.DATABASE_PATH) as db:
            # Enable foreign keys
            await db.execute("PRAGMA foreign_keys = ON")
            
            # Execute schema
            await db.executescript(schema_sql)
            await db.commit()
            
        logger.info("Database schema created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database schema: {e}")
        raise


async def check_database_empty() -> bool:
    """Check if database has any sessions."""
    try:
        async with aiosqlite.connect(settings.DATABASE_PATH) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM sessions")
            count = await cursor.fetchone()
            return count[0] == 0
    except Exception:
        return True


async def seed_demo_data() -> None:
    """
    Seed NovaCorp demo dataset if database is empty.
    This is called during FastAPI lifespan startup.
    """
    try:
        if not await check_database_empty():
            logger.info("Database already contains data, skipping demo seed")
            return
        
        logger.info("Seeding NovaCorp demo dataset...")
        
        # Import and run the seed script
        from fixtures.seed_novacorp import seed_novacorp_data
        await seed_novacorp_data()
        
        logger.info("NovaCorp demo dataset seeded successfully")
        
    except Exception as e:
        logger.warning(f"Failed to seed demo data: {e}")
        # Don't raise - demo data is optional


async def initialize_database() -> None:
    """Initialize database: create schema and optionally seed demo data."""
    await create_schema()
    await seed_demo_data()

# Made with Bob
