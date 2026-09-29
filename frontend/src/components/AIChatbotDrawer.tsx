import React, { useState, useRef, useEffect } from 'react';
import { X, Send, Bot, Sparkles } from 'lucide-react';
import { contractsApi } from '../api/contractsApi';

interface AIChatbotDrawerProps {
  contractId: string;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  sources?: string[];
  timestamp: string;
}

export const AIChatbotDrawer: React.FC<AIChatbotDrawerProps> = ({ contractId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'bot',
      text: 'Hello! I am your AI Financial Assistant. Ask me anything about this contract, expected payments, blockchain activity, or risk analysis.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputMessage('');
    setLoading(true);

    try {
      const res = await contractsApi.sendChatMessage(contractId, text);
      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'bot',
        text: res.answer,
        sources: res.sources,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const botMsg: ChatMessage = {
        id: `bot-err-${Date.now()}`,
        sender: 'bot',
        text: 'Sorry, I encountered an issue connecting to the backend assistant service.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setLoading(false);
    }
  };

  const sampleQuestions = [
    'Why is this contract showing deviation?',
    'What is the expected payment total?',
    'What is the current risk?',
    'What happens if interest rates increase by 3%?',
    'Can you suggest safer terms?',
  ];

  return (
    <>
      {/* FLOATING TRIGGER BUTTON */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            backgroundColor: '#0284c7',
            color: '#ffffff',
            border: 'none',
            borderRadius: '30px',
            padding: '0.85rem 1.4rem',
            fontSize: '0.95rem',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
            boxShadow: '0 10px 25px -5px rgba(2, 132, 199, 0.4)',
            cursor: 'pointer',
            zIndex: 1000,
            transition: 'transform 0.2s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.05)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
        >
          <Sparkles size={20} />
          <span>🤖 AI Assistant</span>
        </button>
      )}

      {/* CHAT DRAWER PANEL */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            width: '420px',
            height: '560px',
            maxWidth: 'calc(100vw - 48px)',
            maxHeight: 'calc(100vh - 48px)',
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            boxShadow: '0 20px 30px -10px rgba(0, 0, 0, 0.2)',
            border: '1px solid #e2e8f0',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 1000,
            overflow: 'hidden',
          }}
        >
          {/* DRAWER HEADER */}
          <div
            style={{
              padding: '1rem 1.25rem',
              backgroundColor: '#0f172a',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Bot size={22} color="#38bdf8" />
              <div>
                <div style={{ fontSize: '0.95rem', fontWeight: 700 }}>AI Financial Assistant</div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Context-aware contract intelligence</div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '0.2rem' }}
            >
              <X size={20} />
            </button>
          </div>

          {/* MESSAGES CONTAINER */}
          <div
            style={{
              flex: 1,
              padding: '1rem',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.85rem',
              backgroundColor: '#f8fafc',
            }}
          >
            {messages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  gap: '0.6rem',
                  alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '88%',
                }}
              >
                {msg.sender === 'bot' && (
                  <div
                    style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      backgroundColor: '#0284c7',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    <Bot size={16} />
                  </div>
                )}

                <div
                  style={{
                    backgroundColor: msg.sender === 'user' ? '#0284c7' : '#ffffff',
                    color: msg.sender === 'user' ? '#ffffff' : '#0f172a',
                    padding: '0.75rem 1rem',
                    borderRadius: '12px',
                    border: msg.sender === 'user' ? 'none' : '1px solid #e2e8f0',
                    fontSize: '0.88rem',
                    lineHeight: 1.45,
                    boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
                  }}
                >
                  <div style={{ whiteSpace: 'pre-line' }}>{msg.text}</div>

                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                      {msg.sources.map((src, i) => (
                        <span
                          key={i}
                          style={{
                            fontSize: '0.68rem',
                            fontWeight: 600,
                            padding: '0.15rem 0.45rem',
                            borderRadius: '4px',
                            backgroundColor: '#f1f5f9',
                            color: '#475569',
                          }}
                        >
                          #{src}
                        </span>
                      ))}
                    </div>
                  )}

                  <div
                    style={{
                      fontSize: '0.68rem',
                      color: msg.sender === 'user' ? '#e0f2fe' : '#94a3b8',
                      marginTop: '0.35rem',
                      textAlign: 'right',
                    }}
                  >
                    {msg.timestamp}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ display: 'flex', gap: '0.6rem', alignSelf: 'flex-start' }}>
                <div style={{ width: '28px', height: '28px', borderRadius: '50%', backgroundColor: '#0284c7', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bot size={16} />
                </div>
                <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', padding: '0.75rem 1rem', borderRadius: '12px', fontSize: '0.85rem', color: '#64748b' }}>
                  Analyzing contract context...
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* QUICK SUGGESTIONS CHIPS */}
          <div style={{ padding: '0.5rem 0.75rem', backgroundColor: '#ffffff', borderTop: '1px solid #f1f5f9', display: 'flex', gap: '0.4rem', overflowX: 'auto' }}>
            {sampleQuestions.slice(0, 3).map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                style={{
                  fontSize: '0.72rem',
                  padding: '0.3rem 0.6rem',
                  borderRadius: '12px',
                  backgroundColor: '#f0f9ff',
                  color: '#0284c7',
                  border: '1px solid #bae6fd',
                  whiteSpace: 'nowrap',
                  cursor: 'pointer',
                }}
              >
                {q}
              </button>
            ))}
          </div>

          {/* INPUT FORM */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            style={{
              padding: '0.75rem 1rem',
              backgroundColor: '#ffffff',
              borderTop: '1px solid #e2e8f0',
              display: 'flex',
              gap: '0.5rem',
            }}
          >
            <input
              type="text"
              placeholder="Ask about this contract..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              style={{
                flex: 1,
                padding: '0.6rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                fontSize: '0.88rem',
                outline: 'none',
              }}
            />
            <button
              type="submit"
              disabled={loading || !inputMessage.trim()}
              style={{
                backgroundColor: '#0284c7',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                padding: '0.6rem 0.85rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: loading || !inputMessage.trim() ? 'not-allowed' : 'pointer',
                opacity: loading || !inputMessage.trim() ? 0.6 : 1,
              }}
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      )}
    </>
  );
};
