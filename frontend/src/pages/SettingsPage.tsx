import React, { useState, useEffect, useCallback } from 'react';
import {
  Save, CheckCircle2, XCircle, Info,
  Monitor, Server, RefreshCw,
} from 'lucide-react';
import { apiService, AzureConnectionStatus } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [comPort,         setComPort]         = useState(() => localStorage.getItem('smp_pref_com_port') ?? 'COM6');
  const [interfaceType,   setInterfaceType]   = useState(() => localStorage.getItem('smp_pref_interface') ?? 'HDLC_WITH_MODE_E');
  const [baudrate,        setBaudrate]        = useState(() => localStorage.getItem('smp_pref_baudrate') ?? '300');
  const [clientAddress,   setClientAddress]   = useState(() => localStorage.getItem('smp_pref_client_addr') ?? '1');
  const [physicalAddress, setPhysicalAddress] = useState(() => localStorage.getItem('smp_pref_phys_addr') ?? '11');
  const [appMode,         setAppMode]         = useState(() => localStorage.getItem('smp_pref_app_mode') ?? 'demo');
  const [hwSaveStatus,    setHwSaveStatus]    = useState<'idle' | 'saved'>('idle');

  // Azure DevOps: real, read-only, server-side status — no credential of
  // any kind is ever entered into or stored by this page.
  const [azureStatus,  setAzureStatus]  = useState<AzureConnectionStatus | null>(null);
  const [azureLoading, setAzureLoading] = useState(true);
  const [azureError,   setAzureError]   = useState<string | null>(null);

  const loadAzureStatus = useCallback(async () => {
    setAzureLoading(true);
    setAzureError(null);
    try {
      const status = await apiService.getAzureConnectionStatus();
      setAzureStatus(status);
    } catch (err: any) {
      setAzureError(err?.message ?? 'Failed to load Azure DevOps connection status.');
    } finally {
      setAzureLoading(false);
    }
  }, []);

  useEffect(() => { loadAzureStatus(); }, [loadAzureStatus]);

  const handleHwSave = () => {
    localStorage.setItem('smp_pref_com_port', comPort);
    localStorage.setItem('smp_pref_interface', interfaceType);
    localStorage.setItem('smp_pref_baudrate', baudrate);
    localStorage.setItem('smp_pref_client_addr', clientAddress);
    localStorage.setItem('smp_pref_phys_addr', physicalAddress);
    localStorage.setItem('smp_pref_app_mode', appMode);
    setHwSaveStatus('saved');
    setTimeout(() => setHwSaveStatus('idle'), 4000);
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
          Physical communication parameters (COM port, interface mode, serial baudrate) are loaded by the FastAPI backend from the server <span className="mono" style={{ color: 'var(--accent-cyan)' }}>.env</span> file at startup.
        </div>
      </div>

      {/* Hardware Settings */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px', color: 'var(--accent-cyan)' }}>
          <Monitor size={18} />
          <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
            Hardware Communication Parameters (Local Preferences)
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
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <button className="btn-cyan" onClick={handleHwSave}>
            {hwSaveStatus === 'saved'
              ? <><CheckCircle2 size={16} /> Saved to Local Storage</>
              : <><Save size={16} /> Save Local Preferences</>}
          </button>
          {hwSaveStatus === 'saved' && (
            <span style={{ fontSize: '0.8rem', color: 'var(--accent-green)' }}>
              ✓ Preferences saved locally in browser. Note: Real server hardware ports require updating the .env file and restarting FastAPI.
            </span>
          )}
        </div>
      </div>

      {/* Azure DevOps Integration — read-only server-side status. No
          credential of any kind is entered, stored, or transmitted by
          this page; the PAT lives only in the backend's own .env. */}
      <div className="glass-card" style={{ padding: '24px', borderLeft: '4px solid var(--accent-purple)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <Server size={18} color="var(--accent-purple)" />
          <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
            Azure DevOps Test Plans Integration
          </h3>
          <span
            style={{ marginLeft: 'auto', fontSize: '0.72rem', fontWeight: 700, padding: '2px 10px', borderRadius: '99px',
              background: azureStatus?.configured ? 'rgba(0,230,118,0.14)' : 'rgba(255,171,0,0.12)',
              color: azureStatus?.configured ? 'var(--accent-green)' : 'var(--accent-amber)',
              border: `1px solid ${azureStatus?.configured ? 'var(--border-green)' : 'var(--border-amber)'}`,
            }}
          >
            {azureStatus?.configured ? '● CONFIGURED' : '○ NOT CONFIGURED'}
          </span>
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '20px' }}>
          Azure DevOps integration is configured server-side via the backend's <span className="mono" style={{ color: 'var(--accent-cyan)', fontSize: '0.75rem' }}>.env</span> file. This page shows its real, live connection status — there is nothing to enter here, and no credential ever reaches your browser.
        </p>

        {azureLoading ? (
          <div style={{ padding: '16px 0', color: 'var(--text-dim)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <RefreshCw size={14} className="spin" /> Checking connection status…
          </div>
        ) : azureError ? (
          <div className="alert-banner danger">
            <XCircle size={18} style={{ flexShrink: 0 }} />
            <div>{azureError}</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            <div>
              <label className="form-label">Azure Organization</label>
              <div className="mono" style={{ fontSize: '0.92rem', color: 'var(--text-main)', marginTop: '4px' }}>
                {azureStatus?.org ?? '—'}
              </div>
            </div>
            <div>
              <label className="form-label">Azure Project</label>
              <div className="mono" style={{ fontSize: '0.92rem', color: 'var(--text-main)', marginTop: '4px' }}>
                {azureStatus?.project ?? '—'}
              </div>
            </div>
            <div>
              <label className="form-label">Connection</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                {azureStatus?.connected ? (
                  <CheckCircle2 size={16} color="var(--accent-green)" />
                ) : (
                  <XCircle size={16} color={azureStatus?.configured ? 'var(--accent-red)' : 'var(--text-dim)'} />
                )}
                <span style={{ fontSize: '0.88rem' }}>
                  {azureStatus?.connected
                    ? 'Connected'
                    : azureStatus?.configured
                      ? 'Configured, but unreachable'
                      : 'Not configured'}
                </span>
              </div>
            </div>
          </div>
        )}

        <hr className="divider" />
        <button className="btn-ghost" onClick={loadAzureStatus} disabled={azureLoading}>
          <RefreshCw size={15} className={azureLoading ? 'spin' : ''} />
          {azureLoading ? 'Checking…' : 'Refresh Status'}
        </button>
        <p style={{ fontSize: '0.73rem', color: 'var(--text-dim)', marginTop: '10px' }}>
          To change these values, update <span className="mono">AZURE_DEVOPS_ORG</span> / <span className="mono">AZURE_DEVOPS_PROJECT</span> / <span className="mono">AZURE_DEVOPS_PAT</span> / <span className="mono">AZURE_DEVOPS_TEST_PLAN_ID</span> in the backend's <span className="mono">.env</span> file and restart the FastAPI server.
        </p>
      </div>
    </div>
  );
};
