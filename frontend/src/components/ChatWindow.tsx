import React, { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import AgentStatus from './AgentStatus';
import Sidebar from './Sidebar';
import { useChat } from '../hooks/useChat';

const containerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  flex: 1,
};

const messagesArea: React.CSSProperties = {
  flex: 1,
  overflowY: 'auto',
  padding: '16px',
  display: 'flex',
  flexDirection: 'column',
};

const inputArea: React.CSSProperties = {
  display: 'flex',
  padding: '12px 16px',
  borderTop: '1px solid #eee',
  gap: 10,
  flexShrink: 0,
  background: '#fff',
};

const inputStyle: React.CSSProperties = {
  flex: 1,
  padding: '10px 14px',
  borderRadius: 20,
  border: '1px solid #d9d9d9',
  outline: 'none',
  fontSize: 14,
};

const buttonStyle: React.CSSProperties = {
  padding: '10px 20px',
  borderRadius: 20,
  border: 'none',
  background: '#1677ff',
  color: '#fff',
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 500,
};

const welcomeStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  flex: 1,
  color: '#bbb',
};

const layoutStyle: React.CSSProperties = {
  display: 'flex',
  height: '100%',
  flex: 1,
  overflow: 'hidden',
};

export default function ChatWindow() {
  const { messages, loading, error, sessionId, sessions, send, newSession, loadSession } = useChat();
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    send(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={layoutStyle}>
      <Sidebar
        sessions={sessions}
        currentSessionId={sessionId}
        onSelect={loadSession}
        onNewSession={newSession}
      />
      <div style={containerStyle}>
        <AgentStatus loading={loading} error={error} sessionId={sessionId} />
        <div style={messagesArea}>
          {messages.length === 0 && !loading && (
            <div style={welcomeStyle}>
              <h2 style={{ fontWeight: 400, margin: 0 }}>企业级智能客服</h2>
              <p style={{ marginTop: 8 }}>有什么可以帮助您的？</p>
            </div>
          )}
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          <div ref={bottomRef} />
        </div>
        <div style={inputArea}>
          <input
            style={inputStyle}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息..."
            disabled={loading}
          />
          <button style={buttonStyle} onClick={handleSend} disabled={loading || !input.trim()}>
            发送
          </button>
        </div>
      </div>
    </div>
  );
}
