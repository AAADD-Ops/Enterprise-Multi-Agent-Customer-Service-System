import type { ChatResponse, SessionMeta, SessionHistoryResponse } from '../types';

const API_BASE = '/api/v1';

export async function sendMessage(
  message: string,
  sessionId: string | null,
  userId: string = 'anonymous'
): Promise<ChatResponse> {
  const res = await fetch(API_BASE + '/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId, user_id: userId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(err.detail || 'HTTP ' + res.status);
  }
  return res.json();
}

export async function listSessions(userId: string = 'anonymous'): Promise<SessionMeta[]> {
  const res = await fetch(API_BASE + '/sessions?user_id=' + encodeURIComponent(userId));
  if (!res.ok) throw new Error('Failed to list sessions');
  const data = await res.json();
  return data.sessions || [];
}

export async function getSessionHistory(sessionId: string): Promise<SessionHistoryResponse> {
  const res = await fetch(API_BASE + '/sessions/' + encodeURIComponent(sessionId));
  if (!res.ok) throw new Error('Failed to get session history');
  return res.json();
}

export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch(API_BASE + '/health');
  return res.json();
}
