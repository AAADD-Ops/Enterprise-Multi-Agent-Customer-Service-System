import React from 'react';
import ChatWindow from './components/ChatWindow';

const appStyle: React.CSSProperties = {
  width: '100vw',
  height: '100vh',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  background: '#f5f5f5',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
};

const cardStyle: React.CSSProperties = {
  width: '100%',
  maxWidth: 1000,
  height: '90vh',
  maxHeight: 800,
  background: '#fff',
  borderRadius: 12,
  boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
  overflow: 'hidden',
  display: 'flex',
  flexDirection: 'column',
};

export default function App() {
  return (
    <div style={appStyle}>
      <div style={cardStyle}>
        <ChatWindow />
      </div>
    </div>
  );
}
