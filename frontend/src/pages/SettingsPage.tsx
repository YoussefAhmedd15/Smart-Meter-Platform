import React, { useState } from 'react';
import { Settings as SettingsIcon, Save, RefreshCw, Cpu, ShieldCheck } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [comPort, setComPort] = useState('COM6');
  const [interfaceType, setInterfaceType] = useState('HDLC_WITH_MODE_E');
  const [baudrate, setBaudrate] = useState('300');
  const [clientAddress, setClientAddress] = useState('1');
  const [physicalAddress, setPhysicalAddress] = useState('11');
  const [appMode, setAppMode] = useState('demo');

  const handleSave = () => {
    alert(`Configuration saved successfully!\nPort: ${comPort}, Mode: ${interfaceType}, App Mode: ${appMode}`);
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>System & Communication Configuration</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Configure Iskraemeco optical head serial settings, Mode E baudrates, DLMS addressing, and hardware mode.</p>
      </div>

      <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>Hardware Communication Parameters</h3>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>APPLICATION OPERATIONAL MODE</label>
            <select value={appMode} onChange={e => setAppMode(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#111726', color: '#fff', border: '1px solid var(--border-color)' }}>
              <option value="demo">Demo / Mock Mode (Dynamic Hardware Simulation)</option>
              <option value="hardware">Hardware Mode (Real Physical COM Port Access)</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>DLMS INTERFACE TYPE</label>
            <select value={interfaceType} onChange={e => setInterfaceType(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#111726', color: '#fff', border: '1px solid var(--border-color)' }}>
              <option value="HDLC_WITH_MODE_E">HDLC_WITH_MODE_E (IEC 62056-21 Optical Probe 300 7E1)</option>
              <option value="HDLC">HDLC (Direct Serial Frame)</option>
              <option value="WRAPPER">WRAPPER (TCP/IP Socket 4059)</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>TARGET SERIAL COM PORT</label>
            <input type="text" value={comPort} onChange={e => setComPort(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#111726', color: '#fff', border: '1px solid var(--border-color)' }} />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>INITIAL MODE E BAUDRATE</label>
            <input type="text" value={baudrate} onChange={e => setBaudrate(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#111726', color: '#fff', border: '1px solid var(--border-color)' }} />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>CLIENT ADDRESS</label>
            <input type="text" value={clientAddress} onChange={e => setClientAddress(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#111726', color: '#fff', border: '1px solid var(--border-color)' }} />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>PHYSICAL / SERVER ADDRESS</label>
            <input type="text" value={physicalAddress} onChange={e => setPhysicalAddress(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#111726', color: '#fff', border: '1px solid var(--border-color)' }} />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
          <button className="btn-cyan" onClick={handleSave}>
            <Save size={16} /> SAVE CONFIGURATION
          </button>
        </div>
      </div>
    </div>
  );
};
