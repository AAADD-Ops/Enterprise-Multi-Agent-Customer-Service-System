export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  routes: string[];
  need_human: boolean;
}

export interface SessionMeta {
  session_id: string;
  title: string;
  created_at: string;
}

export interface SessionHistoryResponse {
  session_id: string;
  messages: { role: string; content: string }[];
}

export type RouteType = 'knowledge' | 'tool' | 'human';
