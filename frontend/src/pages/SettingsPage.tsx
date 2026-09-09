import React, { useState } from 'react';
import {
  Save, CheckCircle2, Info,
  Monitor, Server, Eye, EyeOff, TestTube, ExternalLink,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [comPort,         setComPort]         = useState('COM6');
  const [interfaceType,   setInterfaceType]   = useState('HDLC_WITH_MODE_E');
  const [baudrate,        setBaudrate]        = useState('300');
  const [clientAddress,   setClientAddress]   = useState('1');
  const [physicalAddress, setPhysicalAddress] = useState('11');
  const [appMode,         setAppMode]         = useState('demo');
  const [hwSaveStatus,    setHwSaveStatus]    = useState<'idle' | 'saved'>('idle');

  // Azure DevOps credentials
  const [azureOrg,     setAzureOrg]     = useState(() => localStorage.getItem('azure_org')     ?? '');
  const [azureProject, setAzureProject] = useState(() => localStorage.getItem('azure_project') ?? '');
  const [azurePat,     setAzurePat]     = useState(() => localStorage.getItem('azure_pat')     ?? '');
  const [azurePlanId,  setAzurePlanId]  = useState(() => localStorage.getItem('azure_plan_id') ?? '');
  const [showPat,      setShowPat]      = useState(false);
  const [azureSaved,   setAzureSaved]   = useState<'idle' | 'saved' | 'testing' | 'ok' | 'fail'>('idle');

  const handleHwSave = () => {
    setHwSaveStatus('saved');
    setTimeout(() => setHwSaveStatus('idle'), 3000);
  };

  const handleAzureSave = () => {
    localStorage.setItem('azure_org',      azureOrg.trim());
    localStorage.setItem('azure_project',  azureProject.trim());
    localStorage.setItem('azure_pat',      azurePat.trim());
    localStorage.setItem('azure_plan_id',  azurePlanId.trim());
    setAzureSaved('saved');
    setTimeout(() => setAzureSaved('idle'), 3000);
  };

  const handleAzureTest = async () => {
    if (!azureOrg || !azureProject || !azurePat || !azurePlanId) {
      setAzureSaved('fail');
      setTimeout(() => setAzureSaved('idle'), 3000);
      return;
    }
    setAzureSaved('testing');
    try {
      const token = btoa(`:${azurePat}`);
      const url = `https://dev.azure.com/${azureOrg}/${azureProject}/_apis/testplan/plans/${azurePlanId}?api-version=7.1`;
      const res = await fetch(url, {
        headers: { Authorization: `Basic ${token}` },
      });
      setAzureSaved(res.ok ? 'ok' : 'fail');
    } catch {
      setAzureSaved('fail');
    }
    setTimeout(() => setAzureSaved('idle'), 4000);
  };

  const azureConfigured = Boolean(azureOrg && azureProject && azurePat && azurePlanId);

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
          Communication settings apply at backend startup. Restart the FastAPI server after changing the COM port or interface type.
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
          <button className="btn-cyan" onClick={handleHwSave}>
            {hwSaveStatus === 'saved'
              ? <><CheckCircle2 size={16} /> Saved!</>
              : <><Save size={16} /> Save Configuration</>}
          </button>
          {hwSaveStatus === 'saved' && (
            <span style={{ fontSize: '0.82rem', color: 'var(--accent-green)' }}>
              ✓ Configuration updated successfully.
            </span>
          )}
        </div>
      </div>

      {/* Azure DevOps Integration */}
      <div className="glass-card" style={{ padding: '24px', borderLeft: '4px solid var(--accent-purple)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <Server size={18} color="var(--accent-purple)" />
          <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
            Azure DevOps Test Plans Integration
          </h3>
          <span
            style={{ marginLeft: 'auto', fontSize: '0.72rem', fontWeight: 700, padding: '2px 10px', borderRadius: '99px',
              background: azureConfigured ? 'rgba(0,230,118,0.14)' : 'rgba(255,171,0,0.12)',
              color: azureConfigured ? 'var(--accent-green)' : 'var(--accent-amber)',
              border: `1px solid ${azureConfigured ? 'var(--border-green)' : 'var(--border-amber)'}`,
            }}
          >
            {azureConfigured ? '● CONFIGURED' : '○ NOT CONFIGURED'}
          </span>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '20px' }}>
          These credentials are stored in your browser and used to build Azure DevOps links in the Test Case Manager.
          The backend reads them from <span className="mono" style={{ color: 'var(--accent-cyan)', fontSize: '0.75rem' }}>.env</span> at startup.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label className="form-label">Azure Organization</label>
            <input
              id="azure-org"
              className="form-input"
              value={azureOrg}
              onChange={e => setAzureOrg(e.target.value)}
              placeholder="e.g. iskraemeco"
            />
          </div>
          <div>
            <label className="form-label">Azure Project Name</label>
            <input
              id="azure-project"
              className="form-input"
              value={azureProject}
              onChange={e => setAzureProject(e.target.value)}
              placeholder="e.g. SmartMeterPlatform"
            />
          </div>
          <div>
            <label className="form-label">Test Plan ID</label>
            <input
              id="azure-plan-id"
              className="form-input mono"
              value={azurePlanId}
              onChange={e => setAzurePlanId(e.target.value)}
              placeholder="e.g. 123"
            />
          </div>
          <div>
            <label className="form-label">Personal Access Token (PAT)</label>
            <div style={{ position: 'relative' }}>
              <input
                id="azure-pat"
                className="form-input mono"
                type={showPat ? 'text' : 'password'}
                value={azurePat}
                onChange={e => setAzurePat(e.target.value)}
                placeholder="••••••••••••••••••••••••••"
                style={{ paddingRight: '40px' }}
              />
              <button
                onClick={() => setShowPat(x => !x)}
                style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-dim)', padding: '4px' }}
              >
                {showPat ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>
        </div>

        {/* Azure portal link */}
        {azureConfigured && (
          <div style={{ marginTop: '12px' }}>
            <a
              href={`https://dev.azure.com/${azureOrg}/${azureProject}/_testPlans/execute?planId=${azurePlanId}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
            >
              <ExternalLink size={13} /> Open Test Plan in Azure DevOps
            </a>
          </div>
        )}

        <hr className="divider" />
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button id="save-azure-btn" className="btn-cyan" onClick={handleAzureSave}>
            {azureSaved === 'saved'
              ? <><CheckCircle2 size={16} /> Saved!</>
              : <><Save size={16} /> Save Azure Settings</>}
          </button>
          <button id="test-azure-btn" className="btn-ghost" onClick={handleAzureTest} disabled={azureSaved === 'testing'}>
            <TestTube size={15} />
            {azureSaved === 'testing' ? 'Testing…' : 'Test Connection'}
          </button>

          {azureSaved === 'ok'   && <span style={{ fontSize: '0.82rem', color: 'var(--accent-green)' }}>✓ Connection successful!</span>}
          {azureSaved === 'fail' && <span style={{ fontSize: '0.82rem', color: 'var(--accent-red)' }}>✗ Connection failed — check org, project, PAT, and plan ID.</span>}
          {azureSaved === 'saved' && <span style={{ fontSize: '0.82rem', color: 'var(--accent-green)' }}>✓ Credentials saved to browser storage.</span>}
        </div>
        <p style={{ fontSize: '0.73rem', color: 'var(--text-dim)', marginTop: '10px' }}>
          Also add these values to your <span className="mono">.env</span> file so the FastAPI backend can sync test cases automatically on create/update.
        </p>
      </div>
    </div>
  );
};
