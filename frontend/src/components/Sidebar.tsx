import React from 'react';
import type { SessionMeta } from '../types';

interface Props {
  sessions: SessionMeta[];
  currentSessionId: string | null;
  onSelect: (sessionId: string) => void;
  onNewSession: () => void;
}

const sidebarStyle: React.CSSProperties = {
  width: 240,
  height: '100%',
  background: '#f7f8fa',
  borderRight: '1px solid #eee',
  display: 'flex',
  flexDirection: 'column',
  flexShrink: 0,
};

const headerStyle: React.CSSProperties = {
  padding: '16px',
  borderBottom: '1px solid #eee',
  fontWeight: 600,
  fontSize: 14,
  color: '#333',
};

const newBtnStyle: React.CSSProperties = {
  margin: '12px 16px',
  padding: '10px 0',
  borderRadius: 8,
  border: '1px solid #1677ff',
  background: '#1677ff',
  color: '#fff',
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 500,
  textAlign: 'center' as const,
};

const listStyle: React.CSSProperties = {
  flex: 1,
  overflowY: 'auto',
  padding: '0 8px',
};

const itemStyle = (active: boolean): React.CSSProperties => ({
  padding: '10px 12px',
  borderRadius: 8,
  cursor: 'pointer',
  marginBottom: 4,
  fontSize: 13,
  color: active ? '#1677ff' : '#333',
  background: active ? '#e6f4ff' : 'transparent',
  whiteSpace: 'nowrap' as const,
  overflow: 'hidden',
  textOverflow: 'ellipsis',
});

const emptyStyle: React.CSSProperties = {
  padding: '24px 16px',
  textAlign: 'center',
  color: '#bbb',
  fontSize: 13,
};

export default function Sidebar({ sessions, currentSessionId, onSelect, onNewSession }: Props) {
  return (
    <div style={sidebarStyle}>
      <div style={headerStyle}>历史会话</div>
      <button style={newBtnStyle} onClick={onNewSession}>
        + 新建会话
      </button>
      <div style={listStyle}>
        {sessions.length === 0 ? (
          <div style={emptyStyle}>暂无历史会话</div>
        ) : (
          sessions.map((s) => (
            <div
              key={s.session_id}
              style={itemStyle(s.session_id === currentSessionId)}
              onClick={() => onSelect(s.session_id)}
            >
              {s.title || s.session_id.slice(0, 8)}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
