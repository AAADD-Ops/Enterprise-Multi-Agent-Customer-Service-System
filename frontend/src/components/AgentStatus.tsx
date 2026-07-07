import React from 'react';

interface AgentStatusProps {
  loading: boolean;
  error: string | null;
  sessionId: string | null;
}

const containerStyle: React.CSSProperties = {
  padding: '8px 16px',
  borderBottom: '1px solid #eee',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  fontSize: 13,
  background: '#fafafa',
  flexShrink: 0,
};

const dotStyle = (color: string): React.CSSProperties => ({
  width: 8,
  height: 8,
  borderRadius: '50%',
  background: color,
  display: 'inline-block',
  marginRight: 6,
});

export default function AgentStatus({ loading, error, sessionId }: AgentStatusProps) {
  return (
    <div style={containerStyle}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <span style={dotStyle(error ? '#ff4d4f' : loading ? '#faad14' : '#52c41a')} />
        <span>
          {error ? '连接异常' : loading ? '思考中...' : '在线'}
        </span>
      </div>
      <div style={{ color: '#999', fontSize: 11 }}>
        {sessionId ? '会话: ' + sessionId.slice(0, 8) + '...' : '新会话'}
      </div>
    </div>
  );
}
