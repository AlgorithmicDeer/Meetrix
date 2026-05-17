/**
 * Session ID management for Meetrix.
 * Each browser tab gets its own session ID stored in sessionStorage.
 */

export function getSessionId(): string {
  const existing = sessionStorage.getItem('meetrix_session_id');
  if (existing) return existing;
  
  const id = `session-${crypto.randomUUID()}`;
  sessionStorage.setItem('meetrix_session_id', id);
  return id;
}

export function clearSessionId(): void {
  sessionStorage.removeItem('meetrix_session_id');
}

export function setSessionId(id: string): void {
  sessionStorage.setItem('meetrix_session_id', id);
}

// Made with Bob
