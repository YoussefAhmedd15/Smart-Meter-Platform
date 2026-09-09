import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { KnowledgeItem } from '../types';

export const KnowledgeBase: React.FC = () => {
  const [items, setItems] = useState<KnowledgeItem[]>([]);

  useEffect(() => {
    apiService.getKnowledge().then(setItems).catch(console.error);
  }, []);

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div>
        <h2 className="section-title">Meter Testing Knowledge Base</h2>
        <p className="section-sub">Curated technical solutions for smart meter DLMS/COSEM failures, Mode E baudrate switching, and HDLC framing errors.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {items.length === 0 ? (
          <div className="glass-card" style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No knowledge base entries found in database.
          </div>
        ) : (
          items.map(item => (
            <div key={item.id} className="glass-card" style={{ padding: '20px', borderLeft: '4px solid var(--accent-cyan)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', margin: 0 }}>{item.title}</h3>
                <span className="badge badge-info">{item.severity} SEVERITY</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '0.85rem', margin: '12px 0' }}>
                <div>
                  <strong style={{ color: 'var(--accent-red)' }}>PROBLEM / SYMPTOMS:</strong>
                  <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>{item.problem}</p>
                  <p className="mono" style={{ color: '#fca5a5', fontSize: '0.78rem', marginTop: '4px' }}>{item.symptoms}</p>
                </div>

                <div>
                  <strong style={{ color: 'var(--accent-green)' }}>ROOT CAUSE & SOLUTION:</strong>
                  <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>{item.root_cause}</p>
                  <p style={{ color: '#a7f3d0', marginTop: '4px', fontWeight: 500 }}>✓ {item.solution}</p>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.05)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <div>
                  Affected Models: <strong style={{ color: '#fff' }}>{item.affected_models || 'All'}</strong> • Fixed in Firmware: <strong style={{ color: 'var(--accent-cyan)' }}>{item.fixed_version || 'N/A'}</strong>
                </div>
                <div style={{ display: 'flex', gap: '6px' }}>
                  {(item.tags || '').split(',').filter(Boolean).map((tag, i) => (
                    <span key={i} style={{ padding: '2px 8px', borderRadius: '4px', background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)' }}>#{tag.trim()}</span>
                  ))}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
