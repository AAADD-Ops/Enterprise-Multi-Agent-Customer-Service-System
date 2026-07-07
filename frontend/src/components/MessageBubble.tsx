import React from 'react';
import ReactMarkdown from 'react-markdown';
import type { Message } from '../types';

interface Props {
  message: Message;
}

const roleLabel: Record<Message['role'], string> = {
  user: '你',
  assistant: 'AI 客服',
  system: '系统',
};

const bubbleStyle: React.CSSProperties = {
  maxWidth: '75%',
  padding: '10px 14px',
  borderRadius: 12,
  lineHeight: 1.6,
  fontSize: 14,
  wordBreak: 'break-word',
};

const userBubble: React.CSSProperties = {
  ...bubbleStyle,
  background: '#1677ff',
  color: '#fff',
  alignSelf: 'flex-end',
};

const assistantBubble: React.CSSProperties = {
  ...bubbleStyle,
  background: '#f0f0f0',
  color: '#333',
  alignSelf: 'flex-start',
};

const systemBubble: React.CSSProperties = {
  ...bubbleStyle,
  background: '#fff7e6',
  color: '#ad6800',
  alignSelf: 'center',
  fontSize: 12,
  textAlign: 'center',
};

const wrapperStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  marginBottom: 12,
};

const labelStyle: React.CSSProperties = {
  fontSize: 11,
  color: '#999',
  marginBottom: 4,
};

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  const bubble = isUser ? userBubble : isSystem ? systemBubble : assistantBubble;

  return (
    <div style={{ ...wrapperStyle, alignItems: isUser ? 'flex-end' : isSystem ? 'center' : 'flex-start' }}>
      <span style={{ ...labelStyle, alignSelf: isUser ? 'flex-end' : isSystem ? 'center' : 'flex-start' }}>
        {roleLabel[message.role]}
      </span>
      <div style={bubble}>
        {message.role === 'assistant' ? (
          <ReactMarkdown>{message.content}</ReactMarkdown>
        ) : (
          <span>{message.content}</span>
        )}
      </div>
    </div>
  );
}
