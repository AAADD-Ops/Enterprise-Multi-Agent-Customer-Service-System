import { useState, useCallback, useEffect } from 'react';
import type { Message, ChatResponse, SessionMeta } from '../types';
import * as api from '../services/api';

let idCounter = 0;

function createMessage(role: Message['role'], content: string): Message {
  return { id: 'msg_' + (++idCounter), role, content, timestamp: Date.now() };
}

export function useChat(userId: string = 'anonymous') {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<SessionMeta[]>([]);

  const loadSessions = useCallback(async () => {
    try {
      const list = await api.listSessions(userId);
      setSessions(list);
    } catch {
      // silently fail
    }
  }, [userId]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const send = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    setError(null);
    setLoading(true);

    const userMsg = createMessage('user', trimmed);
    setMessages((prev) => [...prev, userMsg]);

    try {
      const result: ChatResponse = await api.sendMessage(trimmed, sessionId);
      setSessionId(result.session_id);

      const assistantMsg = createMessage(
        'assistant',
        result.reply || '系统处理异常，请稍后重试。'
      );
      setMessages((prev) => [...prev, assistantMsg]);

      if (result.need_human) {
        setMessages((prev) => [
          ...prev,
          createMessage('system', '【系统提示】已为您创建工单，客服人员将尽快与您联系。'),
        ]);
      }

      loadSessions();
    } catch (err: any) {
      setError(err.message || '请求失败');
      setMessages((prev) => [
        ...prev,
        createMessage('assistant', '抱歉，服务暂时不可用，请稍后再试。'),
      ]);
    } finally {
      setLoading(false);
    }
  }, [sessionId, loadSessions]);

  const newSession = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setError(null);
  }, []);

  const loadSession = useCallback(async (sid: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSessionHistory(sid);
      setSessionId(data.session_id);
      const msgs: Message[] = data.messages.map((m) => ({
        id: 'hist_' + (++idCounter),
        role: m.role as Message['role'],
        content: m.content,
        timestamp: Date.now(),
      }));
      setMessages(msgs);
    } catch (err: any) {
      setError(err.message || '加载历史失败');
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    newSession();
    setSessions([]);
  }, [newSession]);

  return { messages, loading, error, sessionId, sessions, send, newSession, loadSession, clear, loadSessions };
}
