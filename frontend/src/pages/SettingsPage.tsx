import React, { useState } from 'react';
import { Settings as SettingsIcon, Save, CheckCircle2, Info, Monitor, Server } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [comPort,          setComPort]          = useState('COM6');
  const [interfaceType,    setInterfaceType]    = useState('HDLC_WITH_MODE_E');
  const [baudrate,         setBaudrate]         = useState('300');
  const [clientAddress,    setClientAddress]    = useState('1');
  const [physicalAddress,  setPhysicalAddress]  = useState('11');
  const [appMode,          setAppMode]          = useState('demo');
  const [saveStatus,       setSaveStatus]       = useState<'idle' | 'saved'>('idle');

  const handleSave = () => {
    // Settings are UI-only until backend CRUD is implemented
    setSaveStatus('saved');
    setTimeout(() => setSaveStatus('idle'), 3000);
  };

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '22px' }}>

      <div>
        <h2 className="section-title">System &amp; Communication Configuration</h2>
        <p className="section-sub">
          Configure Iskraemeco optical head serial settings, Mode E baudrates, DLMS addressing, and hardware mode.
        </p>
      </div>

      <div className="alert-banner info">
        <Info size={18} style={{ flexShrink: 0 }} />
        <div>
          Configuration changes are applied at runtime. Restart the backend service after changing the COM port or interface type.
        </div>
      </div>

      {/* Hardware Settings */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px', color: 'var(--accent-cyan)' }}>
          <Monitor size={18} />
          <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
            Hardware Communication Parameters
          </h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div>
            <label className="form-label">Application Operational Mode</label>
            <select className="form-select" value={appMode} onChange={e => setAppMode(e.target.value)}>
              <option value="demo">Demo / Mock Mode (Dynamic Hardware Simulation)</option>
              <option value="hardware">Hardware Mode (Real Physical COM Port Access)</option>
            </select>
          </div>

          <div>
            <label className="form-label">DLMS Interface Type</label>
            <select className="form-select" value={interfaceType} onChange={e => setInterfaceType(e.target.value)}>
              <option value="HDLC_WITH_MODE_E">HDLC_WITH_MODE_E (IEC 62056-21 Optical Probe 300 7E1)</option>
              <option value="HDLC">HDLC (Direct Serial Frame)</option>
              <option value="WRAPPER">WRAPPER (TCP/IP Socket Port 4059)</option>
            </select>
          </div>

          <div>
            <label className="form-label">Target Serial COM Port</label>
            <input className="form-input mono" type="text" value={comPort} onChange={e => setComPort(e.target.value)} placeholder="COM6" />
          </div>

          <div>
            <label className="form-label">Initial Mode E Baudrate</label>
            <input className="form-input mono" type="text" value={baudrate} onChange={e => setBaudrate(e.target.value)} placeholder="300" />
          </div>

          <div>
            <label className="form-label">DLMS Client Address</label>
            <input className="form-input mono" type="text" value={clientAddress} onChange={e => setClientAddress(e.target.value)} placeholder="1" />
          </div>

          <div>
            <label className="form-label">Physical / Server Address</label>
            <input className="form-input mono" type="text" value={physicalAddress} onChange={e => setPhysicalAddress(e.target.value)} placeholder="11" />
          </div>
        </div>

        <hr className="divider" />

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button className="btn-cyan" onClick={handleSave}>
            {saveStatus === 'saved'
              ? <><CheckCircle2 size={16} /> Saved!</>
              : <><Save size={16} /> Save Configuration</>
            }
          </button>
          {saveStatus === 'saved' && (
            <span style={{ fontSize: '0.82rem', color: 'var(--accent-green)' }}>
              ✓ Configuration updated successfully.
            </span>
          )}
        </div>
      </div>

      {/* Azure DevOps — Future Integration Panel */}
      <div className="glass-card" style={{ padding: '24px', borderLeft: '4px solid var(--accent-purple)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <Server size={18} color="var(--accent-purple)" />
          <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
            Azure DevOps Test Plans Integration
          </h3>
          <span className="badge badge-purple" style={{ marginLeft: 'auto' }}>COMING SOON</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', opacity: 0.55, pointerEvents: 'none' }}>
          {[
            { label: 'Azure Organization', placeholder: 'e.g. iskraemeco' },
            { label: 'Azure Project Name', placeholder: 'e.g. SmartMeterPlatform' },
            { label: 'Personal Access Token (PAT)', placeholder: '••••••••••••••••••••' },
            { label: 'API Version', placeholder: '7.1' },
          ].map(f => (
            <div key={f.label}>
              <label className="form-label">{f.label}</label>
              <input className="form-input" type="text" placeholder={f.placeholder} disabled />
            </div>
          ))}
        </div>

        <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginTop: '14px' }}>
          Azure DevOps synchronization will allow automatic test case and test run syncing with your Azure Test Plans project.
        </p>
      </div>
    </div>
  );
};
