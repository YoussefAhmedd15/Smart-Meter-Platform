import React, { useState } from 'react';
import { Bot, Send, Sparkles, Database, BookOpen, ShieldCheck } from 'lucide-react';
import { apiService } from '../services/api';

export const AIAgent: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'ai'; text: string; sources?: any[] }>>([
    {
      sender: 'ai',
      text: "Hello! I am your Smart Meter AI Quality & Testing Assistant.\n\nI can analyze Iskraemeco meter failures, search past test run history, recommend regression suites, and query our Knowledge Base.\n\nHow can I assist your testing today?",
    }
  ]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!question.trim()) return;
    const q = question;
    setQuestion('');
    setMessages(prev => [...prev, { sender: 'user', text: q }]);
    setLoading(true);

    try {
      const res = await apiService.askAI(q);
      setMessages(prev => [...prev, { sender: 'ai', text: res.answer, sources: res.sources }]);
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'ai', text: `Error retrieving grounded answer: ${err}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px', height: 'calc(100vh - 120px)' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Grounded AI Testing Assistant (RAG)</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Ask questions grounded directly in database evidence, failure history, and knowledge base articles.</p>
      </div>

      <div className="glass-card" style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', background: '#090d16' }}>
        {/* Chat History */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', paddingRight: '8px' }}>
          {messages.map((m, idx) => (
            <div key={idx} style={{ display: 'flex', gap: '12px', justifyContent: m.sender === 'user' ? 'flex-end' : 'flex-start' }}>
              {m.sender === 'ai' && (
                <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'linear-gradient(135deg, #00f2fe, #4facfe)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bot size={20} color="#090d16" />
                </div>
              )}
              <div style={{
                maxWidth: '75%',
                padding: '14px 18px',
                borderRadius: '12px',
                background: m.sender === 'user' ? 'rgba(0, 242, 254, 0.15)' : 'rgba(17, 23, 38, 0.8)',
                border: m.sender === 'user' ? '1px solid var(--border-cyan)' : '1px solid var(--border-color)',
                fontSize: '0.88rem',
                whiteSpace: 'pre-line',
                color: '#fff'
              }}>
                {m.text}
                {m.sources && m.sources.length > 0 && (
                  <div style={{ marginTop: '12px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.1)', fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>
                    <strong>Sources Referenced:</strong> {m.sources.map(s => s.title || s.test_case).join(', ')}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && <div style={{ color: 'var(--accent-cyan)', fontSize: '0.85rem' }}>Evaluating database evidence and similarity matches...</div>}
        </div>

        {/* Input Bar */}
        <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
          <input
            type="text"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask AI e.g. 'Why did meter ISK-2026-984210 fail?' or 'What tests should I run after changing Load Profile?'"
            style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', background: '#111726', color: '#fff', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
          />
          <button className="btn-cyan" onClick={handleSend}>
            <Send size={16} /> ASK AI
          </button>
        </div>
      </div>
    </div>
  );
};
