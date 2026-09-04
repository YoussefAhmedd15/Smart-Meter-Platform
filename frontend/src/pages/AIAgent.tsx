import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, Sparkles, User, Cpu } from 'lucide-react';
import { apiService } from '../services/api';

const SUGGESTED = [
  'Why did meter ISK-2026-984210 fail the Mode E handshake?',
  'What tests should I run after changing Load Profile buffer?',
  'Compare failure patterns in v3.13.0 vs v3.14.2',
  'Explain HDLC FCS checksum errors on AM550',
];

interface Message {
  sender: 'user' | 'ai';
  text: string;
  sources?: any[];
}

export const AIAgent: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'ai',
      text: "Hello! I'm your Smart Meter AI Quality & Testing Assistant.\n\nI can analyze Iskraemeco meter failures, search past test run history, recommend regression suites, and query the Knowledge Base.\n\nHow can I assist your testing today?",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (q?: string) => {
    const text = (q ?? question).trim();
    if (!text) return;
    setQuestion('');
    setMessages(prev => [...prev, { sender: 'user', text }]);
    setLoading(true);

    try {
      const res = await apiService.askAI(text);
      setMessages(prev => [...prev, { sender: 'ai', text: res.answer, sources: res.sources }]);
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'ai', text: `⚠️ Could not retrieve grounded answer: ${err}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '0', height: 'calc(100vh - 68px)', boxSizing: 'border-box' }}>

      {/* Header */}
      <div style={{ marginBottom: '18px' }}>
        <h2 className="section-title">Grounded AI Testing Assistant (RAG)</h2>
        <p className="section-sub">
          Ask questions grounded in database evidence, failure history, and knowledge base articles.
        </p>
      </div>

      {/* Suggestion chips */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '14px' }}>
        {SUGGESTED.map((s, i) => (
          <button key={i} className="chip" onClick={() => handleSend(s)} style={{ cursor: 'pointer' }}>
            <Sparkles size={11} /> {s.length > 50 ? s.slice(0, 50) + '…' : s}
          </button>
        ))}
      </div>

      {/* Chat Window */}
      <div className="glass-card" style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(4, 7, 14, 0.92)',
        overflow: 'hidden',
        minHeight: 0,
      }}>
        {/* Messages */}
        <div style={{
          flex: 1, overflowY: 'auto', padding: '20px',
          display: 'flex', flexDirection: 'column', gap: '16px',
        }}>
          {messages.map((m, idx) => (
            <div key={idx} style={{
              display: 'flex',
              gap: '12px',
              justifyContent: m.sender === 'user' ? 'flex-end' : 'flex-start',
            }}>
              {m.sender === 'ai' && (
                <div style={{
                  width: '34px', height: '34px', borderRadius: '9px', flexShrink: 0,
                  background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: '0 0 12px rgba(0,242,254,0.3)',
                }}>
                  <Bot size={18} color="#070b14" />
                </div>
              )}

              <div style={{
                maxWidth: '72%',
                padding: '13px 17px',
                borderRadius: m.sender === 'user' ? '14px 4px 14px 14px' : '4px 14px 14px 14px',
                background: m.sender === 'user'
                  ? 'rgba(0,242,254,0.12)'
                  : 'rgba(13, 20, 36, 0.9)',
                border: m.sender === 'user'
                  ? '1px solid var(--border-cyan)'
                  : '1px solid var(--border-color)',
                fontSize: '0.87rem',
                whiteSpace: 'pre-line',
                color: m.sender === 'user' ? '#e2f8ff' : 'var(--text-main)',
                lineHeight: '1.6',
              }}>
                {m.text}

                {m.sources && m.sources.length > 0 && (
                  <div style={{
                    marginTop: '12px', paddingTop: '10px',
                    borderTop: '1px solid rgba(255,255,255,0.07)',
                    fontSize: '0.73rem', color: 'var(--accent-cyan)',
                  }}>
                    <Sparkles size={11} style={{ display: 'inline', marginRight: '4px' }} />
                    <strong>Sources:</strong> {m.sources.map(s => s.title || s.test_case).join(' · ')}
                  </div>
                )}
              </div>

              {m.sender === 'user' && (
                <div style={{
                  width: '34px', height: '34px', borderRadius: '9px', flexShrink: 0,
                  background: 'rgba(0,242,254,0.12)', border: '1px solid var(--border-cyan)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <User size={17} color="var(--accent-cyan)" />
                </div>
              )}
            </div>
          ))}

          {/* Typing indicator */}
          {loading && (
            <div style={{ display: 'flex', gap: '12px' }}>
              <div style={{
                width: '34px', height: '34px', borderRadius: '9px',
                background: 'linear-gradient(135deg, #00f2fe, #4facfe)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Bot size={18} color="#070b14" />
              </div>
              <div style={{
                padding: '13px 18px', borderRadius: '4px 14px 14px 14px',
                background: 'rgba(13,20,36,0.9)', border: '1px solid var(--border-color)',
                display: 'flex', gap: '6px', alignItems: 'center',
              }}>
                {[0, 1, 2].map(i => (
                  <div key={i} style={{
                    width: '7px', height: '7px', borderRadius: '50%',
                    background: 'var(--accent-cyan)',
                    animation: `bounce 1.2s ${i * 0.2}s infinite ease-in-out`,
                  }} />
                ))}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input Bar */}
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid var(--border-color)',
          display: 'flex', gap: '10px',
        }}>
          <input
            type="text"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !loading && handleSend()}
            placeholder="Ask about meter failures, test recommendations, DLMS errors…"
            disabled={loading}
            className="form-input"
            style={{ flex: 1 }}
          />
          <button
            className="btn-cyan"
            onClick={() => handleSend()}
            disabled={loading || !question.trim()}
          >
            <Send size={15} />
            {loading ? 'Thinking…' : 'Ask AI'}
          </button>
        </div>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0.7); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
};
