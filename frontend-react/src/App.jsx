import React, { useState, useEffect, useRef, useMemo } from 'react';
import OperationalMap from './OperationalMap';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || (
  window.location.hostname.includes('loca.lt')
    ? 'https://eleven-melons-send.loca.lt'
    : (window.location.hostname === 'localhost' ? 'http://localhost:8000' : `${window.location.protocol}//${window.location.host}`)
);
const WS_BASE = import.meta.env.VITE_WS_BASE || (
  window.location.hostname.includes('loca.lt')
    ? 'wss://eleven-melons-send.loca.lt'
    : (window.location.hostname === 'localhost' ? 'ws://localhost:8000' : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`)
);

export default function App() {
  // Navigation: 'command' | 'incidents' | 'operations' | 'responders' | 'medical' | 'evacuation' | 'alerts' | 'ai_activity' | 'audit' | 'responder' | 'public'
  const [activeNav, setActiveNav] = useState('command');

  // Operational State & Incidents
  const [incidentsList, setIncidentsList] = useState([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState('I001');
  const [liveState, setLiveState] = useState(null);
  const [auditEvents, setAuditEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiOnline, setApiOnline] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [dataMode, setDataMode] = useState('SIMULATION'); // 'LIVE' | 'SIMULATION'

  // Route Change Notification Alert
  const [routeChangeAlert, setRouteChangeAlert] = useState(null);

  // Modals & User Input
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [selectedAction, setSelectedAction] = useState(null);
  const [approvalNotes, setApprovalNotes] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newIncidentForm, setNewIncidentForm] = useState({
    incident_type: 'Chemical_Leak',
    location: 'Plant B',
    chemical: 'Sulfur Dioxide',
    people_affected: 25,
    severity: 8,
    fire: false,
    explosion: false,
  });

  // Tracking Focus
  const [trackedUnitId, setTrackedUnitId] = useState('R0433');
  const [responderNote, setResponderNote] = useState('');
  const [publicData, setPublicData] = useState(null);

  const wsRef = useRef(null);

  // 1. Initial Health & Incidents Fetch
  useEffect(() => {
    checkHealth();
    fetchIncidents();
    fetchAuditEvents();
  }, []);

  // 2. Fetch Live State when Incident Changes
  useEffect(() => {
    if (selectedIncidentId) {
      loadLiveState(selectedIncidentId);
      loadPublicData(selectedIncidentId);
      fetchAuditEvents();
      setupWebSocket(selectedIncidentId);
    }
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [selectedIncidentId]);

  // 3. WebSocket Real-time Connection with Automatic Polling Fallback (Step 24)
  const setupWebSocket = (incId) => {
    try {
      if (wsRef.current) {
        wsRef.current.close();
      }
      const ws = new WebSocket(`${WS_BASE}/ws/incidents/${incId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'FULL_STATE' || msg.type === 'HEARTBEAT') {
            if (msg.data) setLiveState(msg.data);
            if (msg.state) setLiveState(msg.state);
          } else if (msg.type === 'EVENT_BROADCAST') {
            if (msg.state) setLiveState(msg.state);
            fetchAuditEvents();
            if (msg.event?.type === 'ROUTE_CHANGED') {
              setRouteChangeAlert(msg.event.data);
            }
          }
        } catch (err) {
          console.error('WS parse error', err);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
      };

      ws.onerror = () => {
        setWsConnected(false);
      };
    } catch (e) {
      setWsConnected(false);
    }
  };

  // 4. Fallback Telemetry Ticker (every 3.2s)
  useEffect(() => {
    if (!selectedIncidentId || activeNav === 'public') return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/incidents/${selectedIncidentId}/tick-telemetry`, {
          method: 'POST',
        });
        if (res.ok) {
          const updated = await res.json();
          setLiveState(updated);
        }
      } catch {
        // Continue silently
      }
    }, 3200);

    return () => clearInterval(interval);
  }, [selectedIncidentId, activeNav]);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      if (res.ok) {
        const d = await res.json();
        setApiOnline(true);
        if (d.data_mode) setDataMode(d.data_mode);
      }
    } catch {
      setApiOnline(false);
    }
  };

  const fetchIncidents = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/incidents?limit=25`);
      if (res.ok) {
        const data = await res.json();
        const active = data.active_incidents || [];
        const catalog = data.catalog_incidents || [];
        setIncidentsList([...active, ...catalog]);
      }
    } catch (e) {
      console.error('Failed to load incidents', e);
    }
  };

  const loadLiveState = async (id) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/incidents/${id}`);
      if (res.ok) {
        const data = await res.json();
        setLiveState(data);
      }
    } catch (e) {
      console.error('Failed to load live state', e);
    } finally {
      setLoading(false);
    }
  };

  const loadPublicData = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/public/incident/${id}`);
      if (res.ok) {
        const data = await res.json();
        setPublicData(data);
      }
    } catch (e) {
      console.error('Failed to load public data', e);
    }
  };

  const fetchAuditEvents = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/events?limit=40`);
      if (res.ok) {
        const data = await res.json();
        setAuditEvents(data.events || []);
      }
    } catch (e) {
      console.error('Failed to load audit events', e);
    }
  };

  // ----------------- Simulation Triggers (Step 25) -----------------
  const handleSimulateBlockRoad = async () => {
    if (!selectedIncidentId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/simulation/block-road`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ incident_id: selectedIncidentId, road_id: 'R03108' }),
      });
      if (res.ok) {
        const updated = await res.json();
        setLiveState(updated);
        fetchAuditEvents();
        const lead = updated.responders?.[0];
        setRouteChangeAlert({
          unit_name: lead?.name || 'R0433 HAZMAT',
          previous_eta: '08:21',
          new_eta: lead?.eta_display || '12:01',
          reason: 'Road R03108 blocked. Alternative route activated.',
        });
      }
    } catch (e) {
      console.error('Block road failed', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateReopenRoad = async () => {
    if (!selectedIncidentId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/simulation/reopen-road`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ incident_id: selectedIncidentId, road_id: 'R03108' }),
      });
      if (res.ok) {
        const updated = await res.json();
        setLiveState(updated);
        setRouteChangeAlert(null);
        fetchAuditEvents();
      }
    } catch (e) {
      console.error('Reopen road failed', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateChangeWind = async () => {
    if (!selectedIncidentId) return;
    setLoading(true);
    const currDir = liveState?.spread?.wind_direction || 'NW';
    const nextDir = currDir === 'NW' ? 'W' : currDir === 'W' ? 'SSE' : 'NW';
    try {
      const res = await fetch(`${API_BASE}/api/simulation/change-wind`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ incident_id: selectedIncidentId, wind_direction: nextDir, wind_speed_ms: 9.2 }),
      });
      if (res.ok) {
        const updated = await res.json();
        setLiveState(updated);
        fetchAuditEvents();
      }
    } catch (e) {
      console.error('Change wind failed', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateHospitalFull = async (hospId = 'H002') => {
    if (!selectedIncidentId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/simulation/hospital-full`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ incident_id: selectedIncidentId, hospital_id: hospId }),
      });
      if (res.ok) {
        const updated = await res.json();
        setLiveState(updated);
        fetchAuditEvents();
      }
    } catch (e) {
      console.error('Hospital full failed', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateShelterFull = async (shelterId = 'S001') => {
    if (!selectedIncidentId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/simulation/shelter-full`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ incident_id: selectedIncidentId, shelter_id: shelterId }),
      });
      if (res.ok) {
        const updated = await res.json();
        setLiveState(updated);
        fetchAuditEvents();
      }
    } catch (e) {
      console.error('Shelter full failed', e);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleDataMode = async (mode) => {
    try {
      const res = await fetch(`${API_BASE}/api/simulation/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
      });
      if (res.ok) {
        const d = await res.json();
        setDataMode(d.operational_mode);
      }
    } catch (e) {
      setDataMode(mode);
    }
  };

  // ----------------- Human Approval Gateway (Step 14) -----------------
  const handleApprovalDecision = async (actionId, decision) => {
    if (!selectedIncidentId || !actionId) return;
    try {
      const res = await fetch(`${API_BASE}/api/incidents/${selectedIncidentId}/approvals/${actionId}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, modifications: approvalNotes }),
      });
      if (res.ok) {
        const updated = await res.json();
        setLiveState(updated);
        setShowApprovalModal(false);
        setSelectedAction(null);
        setApprovalNotes('');
        fetchAuditEvents();
      }
    } catch (e) {
      console.error('Approval decision failed', e);
    }
  };

  // ----------------- Create Incident (Step 5) -----------------
  const handleCreateIncident = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const incId = `I00${incidentsList.length + 1}`;
      const payload = {
        incident_id: incId,
        incident_type: newIncidentForm.incident_type,
        location: newIncidentForm.location,
        chemical: newIncidentForm.chemical,
        people_affected: Number(newIncidentForm.people_affected),
        severity: Number(newIncidentForm.severity),
        fire: newIncidentForm.fire,
        explosion: newIncidentForm.explosion,
      };

      const res = await fetch(`${API_BASE}/api/incidents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setShowCreateModal(false);
        await fetchIncidents();
        setSelectedIncidentId(incId);
        setActiveNav('operations');
      }
    } catch (err) {
      console.error('Creation failed', err);
    } finally {
      setLoading(false);
    }
  };

  // ----------------- Responder Terminal Status (Step 18) -----------------
  const handleUpdateResponderStatus = async (status) => {
    if (!trackedUnitId) return;
    try {
      const res = await fetch(`${API_BASE}/api/responder/${trackedUnitId}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, notes: responderNote }),
      });
      if (res.ok) {
        setResponderNote('');
        loadLiveState(selectedIncidentId);
        fetchAuditEvents();
      }
    } catch (e) {
      console.error('Responder status failed', e);
    }
  };

  // State extractions
  const responders = liveState?.responders || [];
  const spread = liveState?.spread || {};
  const hazard = liveState?.hazard || {};
  const hospitals = liveState?.hospitals || [];
  const shelters = liveState?.shelters || [];
  const approvals = liveState?.approvals || [];
  const aiActivity = liveState?.ai_activity || [];
  const roadClosures = liveState?.road_closures || [];
  const pendingApprovals = approvals.filter((a) => a.status === 'PENDING_APPROVAL');
  const leadResponder = responders[0] || {};

  return (
    <div className="aidroute-layout">
      {/* ========================================================================= */}
      {/* 1. LEFT SIDEBAR NAVIGATION (Step 12 & 15)                                 */}
      {/* ========================================================================= */}
      <aside className="aidroute-sidebar">
        <div className="sidebar-brand">
          <div className="aidroute-logo-icon">
            <span className="logo-square top-left" style={{ background: '#ef4444' }}></span>
            <span className="logo-square top-right" style={{ background: '#0f172a' }}></span>
            <span className="logo-square bottom-left" style={{ background: '#2563eb' }}></span>
            <span className="logo-square bottom-right" style={{ background: '#10b981' }}></span>
          </div>
          <div className="brand-titles">
            <span className="brand-primary">CRISIS COMMAND AI</span>
            <span className="brand-secondary">Operational Engine</span>
          </div>
        </div>

        {/* Commander Status Badge */}
        <div className="coordinator-card">
          <div className="user-icon-circle" style={{ background: '#0f172a', color: '#fff' }}>⚡</div>
          <div className="coordinator-info">
            <div className="coord-name">Incident Commander</div>
            <div className="coord-role">EOC Tactical Control</div>
          </div>
          <span className="coord-live-dot"></span>
        </div>

        {/* Sidebar Nav Items */}
        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activeNav === 'command' ? 'active' : ''}`}
            onClick={() => setActiveNav('command')}
          >
            <span className="nav-icon">🏠</span>
            <div className="nav-text">
              <span className="nav-title">COMMAND</span>
              <span className="nav-sub">System Overview</span>
            </div>
            {activeNav === 'command' && <span className="nav-active-dot"></span>}
          </button>

          <button
            className={`nav-item ${activeNav === 'incidents' ? 'active' : ''}`}
            onClick={() => setActiveNav('incidents')}
          >
            <span className="nav-icon">🚨</span>
            <div className="nav-text">
              <span className="nav-title">INCIDENTS</span>
              <span className="nav-sub">Active Emergencies</span>
            </div>
            {activeNav === 'incidents' && <span className="nav-active-dot"></span>}
          </button>

          <button
            className={`nav-item ${activeNav === 'operations' ? 'active' : ''}`}
            onClick={() => setActiveNav('operations')}
          >
            <span className="nav-icon">🗺</span>
            <div className="nav-text">
              <span className="nav-title">LIVE OPERATIONS</span>
              <span className="nav-sub">Map + Response</span>
            </div>
            {activeNav === 'operations' && <span className="nav-active-dot"></span>}
          </button>

          <button
            className={`nav-item ${activeNav === 'responders' ? 'active' : ''}`}
            onClick={() => setActiveNav('responders')}
          >
            <span className="nav-icon">🚒</span>
            <div className="nav-text">
              <span className="nav-title">RESPONDERS</span>
              <span className="nav-sub">Teams + Fleet</span>
            </div>
            {activeNav === 'responders' && <span className="nav-active-dot"></span>}
          </button>

          <button
            className={`nav-item ${activeNav === 'medical' ? 'active' : ''}`}
            onClick={() => setActiveNav('medical')}
          >
            <span className="nav-icon">🏥</span>
            <div className="nav-text">
              <span className="nav-title">MEDICAL</span>
              <span className="nav-sub">Hospitals + Triage</span>
            </div>
            {activeNav === 'medical' && <span className="nav-active-dot"></span>}
          </button>

          <button
            className={`nav-item ${activeNav === 'evacuation' ? 'active' : ''}`}
            onClick={() => setActiveNav('evacuation')}
          >
            <span className="nav-icon">🏠</span>
            <div className="nav-text">
              <span className="nav-title">EVACUATION</span>
              <span className="nav-sub">Shelters + Safe Corridors</span>
            </div>
            {activeNav === 'evacuation' && <span className="nav-active-dot"></span>}
          </button>

          <button
            className={`nav-item ${activeNav === 'ai_activity' ? 'active' : ''}`}
            onClick={() => setActiveNav('ai_activity')}
          >
            <span className="nav-icon">🧠</span>
            <div className="nav-text">
              <span className="nav-title">AI ACTIVITY</span>
              <span className="nav-sub">Agent Decisions</span>
            </div>
            {activeNav === 'ai_activity' && <span className="nav-active-dot"></span>}
          </button>

          <button
            className={`nav-item ${activeNav === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveNav('audit')}
          >
            <span className="nav-icon">📜</span>
            <div className="nav-text">
              <span className="nav-title">AUDIT</span>
              <span className="nav-sub">Event Bus History</span>
            </div>
            {activeNav === 'audit' && <span className="nav-active-dot"></span>}
          </button>

          <div className="nav-divider"></div>

          <button
            className={`nav-item secondary ${activeNav === 'responder' ? 'active' : ''}`}
            onClick={() => setActiveNav('responder')}
          >
            <span className="nav-icon">🚒</span>
            <div className="nav-text">
              <span className="nav-title">RESPONDER APP</span>
              <span className="nav-sub">Field Terminal</span>
            </div>
          </button>

          <button
            className={`nav-item secondary ${activeNav === 'public' ? 'active' : ''}`}
            onClick={() => setActiveNav('public')}
          >
            <span className="nav-icon">📱</span>
            <div className="nav-text">
              <span className="nav-title">PUBLIC SAFETY</span>
              <span className="nav-sub">Civilian Portal</span>
            </div>
          </button>
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <div className="footer-status">
            <span className="lightning-icon">●</span>
            <span>SYSTEM ONLINE</span>
          </div>
          <div className="footer-network">
            <span className={wsConnected ? 'dot-green' : 'dot-live'}></span>
            <span>{wsConnected ? 'WebSocket Live' : 'Polling Sync'}</span>
          </div>
        </div>
      </aside>

      {/* ========================================================================= */}
      {/* 2. MAIN CONTENT AREA                                                      */}
      {/* ========================================================================= */}
      <div className="aidroute-main-content">
        {/* Step 13: Permanent Simulation Mode Banner */}
        <div className="simulation-mode-banner">
          <div className="sim-banner-left">
            <span className="sim-pulsing-dot"></span>
            <span>CRISIS COMMAND AI ● SYSTEM ONLINE</span>
            <span style={{ opacity: 0.85 }}>|</span>
            <span>DATA MODE: <strong>{dataMode}</strong></span>
            {dataMode === 'SIMULATION' && (
              <span className="source-tag simulation">SIMULATION MODE ACTIVE</span>
            )}
          </div>
          <div className="sim-mode-toggle">
            <button
              className={`sim-toggle-btn ${dataMode === 'LIVE' ? 'active' : ''}`}
              onClick={() => handleToggleDataMode('LIVE')}
            >
              LIVE
            </button>
            <button
              className={`sim-toggle-btn ${dataMode === 'SIMULATION' ? 'active' : ''}`}
              onClick={() => handleToggleDataMode('SIMULATION')}
            >
              SIMULATION
            </button>
          </div>
        </div>

        {/* Step 25: Real Simulation Control Panel */}
        <div className="simulation-control-bar">
          <div className="sim-bar-label">
            <span className="gear-icon">⚙</span>
            <span>SIMULATE EVENT:</span>
          </div>
          <div className="sim-btn-group">
            {roadClosures.includes('R03108') ? (
              <button className="sim-btn" onClick={handleSimulateReopenRoad}>
                🟢 Reopen Road R03108
              </button>
            ) : (
              <button className="sim-btn danger" onClick={handleSimulateBlockRoad}>
                🚧 Block Road R03108
              </button>
            )}
            <button className="sim-btn warning" onClick={handleSimulateChangeWind}>
              💨 Change Wind ({spread.wind_direction || 'NW'} → {spread.wind_direction === 'NW' ? 'W' : 'SSE'})
            </button>
            <button className="sim-btn" onClick={() => handleSimulateHospitalFull('H002')}>
              🏥 Hospital Full (H002)
            </button>
            <button className="sim-btn" onClick={() => handleSimulateShelterFull('S001')}>
              🏠 Shelter Full (S001)
            </button>
            <button className="sim-btn" onClick={() => setShowCreateModal(true)}>
              ➕ New Casualty / Incident
            </button>
          </div>
        </div>

        {/* Step 10: Dynamic Route Change Banner */}
        {routeChangeAlert && (
          <div className="route-change-banner">
            <div className="route-change-content">
              <span className="route-change-badge">⚠ ROUTE CHANGE</span>
              <span className="route-change-text">
                <strong>{routeChangeAlert.unit_name}</strong> | Previous ETA: {routeChangeAlert.previous_eta} → New ETA: <strong>{routeChangeAlert.new_eta}</strong> | Reason: {routeChangeAlert.reason}
              </span>
            </div>
            <button
              className="route-change-action"
              onClick={() => {
                setActiveNav('operations');
                setTrackedUnitId('R0433');
              }}
            >
              VIEW ROUTE ON MAP
            </button>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 1: COMMAND PAGE (Step 1 & 16)                                        */}
        {/* ========================================================================= */}
        {activeNav === 'command' && (
          <div className="content-body-scroll command-view-container">
            {/* Top Operational Incident Card */}
            <div className="command-incident-hero">
              <div className="command-hero-header">
                <div className="active-incident-pill">
                  <span className="dot-live"></span> 🔴 ACTIVE INCIDENT
                </div>
                <div className="source-tag model">
                  ALOHA SPREAD MODEL
                </div>
              </div>

              <div className="command-incident-title">
                {liveState?.incident_id || 'I001'} {liveState?.type?.replace(/_/g, ' ') || 'CHEMICAL LEAK'}
              </div>
              <div className="command-incident-sub">
                {liveState?.location || 'Plant B'} • {liveState?.chemical || 'Sulfur Dioxide'} Vapor Release
              </div>

              <div className="command-kpi-bar">
                <div className="command-kpi-item">
                  <span className="kpi-val critical">{liveState?.people_at_risk || 250}</span>
                  <span className="kpi-lbl">People At Risk</span>
                </div>
                <div className="command-kpi-item">
                  <span className="kpi-val warning">{liveState?.severity || 'HIGH'} ({liveState?.severity_score || 8}/10)</span>
                  <span className="kpi-lbl">Severity Level</span>
                </div>
                <div className="command-kpi-item">
                  <span className="kpi-val" style={{ color: '#10b981' }}>RESPONSE IN PROGRESS</span>
                  <span className="kpi-lbl">Operational Status</span>
                </div>
                <div className="command-kpi-item">
                  <span className="kpi-val">{responders.length} Dispatched</span>
                  <span className="kpi-lbl">Active Responders</span>
                </div>
              </div>

              <div className="command-actions-row">
                <button
                  className="btn-open-response"
                  onClick={() => setActiveNav('operations')}
                >
                  ⚡ OPEN RESPONSE WORKSPACE
                </button>
                <button
                  className="btn-secondary-action"
                  onClick={() => setShowCreateModal(true)}
                >
                  + CREATE INCIDENT
                </button>
              </div>
            </div>

            {/* LIVE INCIDENT MAP (Step 1) */}
            <div className="command-map-card">
              <div className="command-map-header">
                <span className="command-map-title">LIVE INCIDENT MAP & FLEET TELEMETRY (REAL-WORLD GIS)</span>
                <div className="command-map-etas">
                  {responders.slice(0, 2).map((u) => (
                    <span key={u.resource_id} className="eta-pill">
                      {u.type.toLowerCase().includes('hazmat') ? '☢' : '🚒'} {u.resource_id} ETA: <strong>{u.eta_display}</strong>
                    </span>
                  ))}
                  <span className="source-tag simulation">{leadResponder.data_source || 'SIMULATION ROUTE'}</span>
                </div>
              </div>

              {/* Real World GIS Map Canvas */}
              <div style={{ height: '440px', width: '100%', position: 'relative' }}>
                <OperationalMap
                  liveState={liveState}
                  trackedUnitId={trackedUnitId}
                  onSelectUnit={(id) => setTrackedUnitId(id)}
                  height="440px"
                />
              </div>

              {/* Live Response Footer Summary */}
              <div className="command-live-response-summary">
                <span style={{ fontWeight: 800 }}>LIVE RESPONSE ASSETS:</span>
                <div className="response-counts-row">
                  <span className="response-count-chip">🚒 3 Fire Teams</span>
                  <span className="response-count-chip">☢ 2 Hazmat Teams</span>
                  <span className="response-count-chip">🚑 3 Ambulances</span>
                  <span className="response-count-chip">🏥 {hospitals.length} Hospitals</span>
                  <span className="response-count-chip">🏠 {shelters.length} Shelters</span>
                  <span className="response-count-chip" style={{ color: roadClosures.length ? '#ef4444' : '#10b981' }}>
                    🚧 {roadClosures.length} Road Closures
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 2: INCIDENT OPERATIONS WORKSPACE (Step 2, 4, 6)                      */}
        {/* ========================================================================= */}
        {activeNav === 'operations' && (
          <div className="ops-workspace">
            {/* Left: Interactive GIS Map */}
            <div className="ops-workspace-map-pane">
              <div className="command-map-header" style={{ borderBottom: '1px solid #e2e8f0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <button
                    onClick={() => setActiveNav('command')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', fontWeight: 800, color: '#2563eb' }}
                  >
                    ← ACTIVE INCIDENTS
                  </button>
                  <span style={{ color: '#94a3b8' }}>|</span>
                  <span style={{ fontWeight: 800, color: '#ef4444' }}>
                    🔴 {liveState?.incident_id} — {liveState?.chemical} LEAK ({liveState?.location})
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <span className="source-tag model">PLUME: {spread.wind_direction} ({spread.red_zone_m}m RED)</span>
                  <span className="source-tag simulation">{leadResponder.data_source || 'SIMULATION ROUTE'}</span>
                </div>
              </div>

              <div className="ops-map-canvas-wrap">
                <OperationalMap
                  liveState={liveState}
                  trackedUnitId={trackedUnitId}
                  onSelectUnit={(id) => setTrackedUnitId(id)}
                  height="100%"
                />
              </div>
            </div>

            {/* Right: Operational Control Pane */}
            <div className="ops-workspace-sidebar">
              {/* Card 1: Incident Status */}
              <div className="ops-sidebar-card">
                <div className="ops-sidebar-title">
                  <span>INCIDENT STATUS</span>
                  <span className="source-tag live">LIVE</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.6rem', fontSize: '0.78rem' }}>
                  <div>🔴 <strong>Severity:</strong> {liveState?.severity || 'HIGH'}</div>
                  <div>👥 <strong>At Risk:</strong> {liveState?.people_at_risk || 250}</div>
                  <div>🚒 <strong>Responders:</strong> {responders.length} units</div>
                  <div>🏥 <strong>Hospitals:</strong> {hospitals.length} active</div>
                  <div>🏠 <strong>Shelters:</strong> {shelters.length} assigned</div>
                  <div>🚧 <strong>Closures:</strong> {roadClosures.length} blocked</div>
                </div>
              </div>

              {/* Card 2: Response Plan (Step 4) */}
              <div className="ops-sidebar-card">
                <div className="ops-sidebar-title">
                  <span>RESPONSE PLAN</span>
                  <span style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 700 }}>v{liveState?.replanning?.version || 1}</span>
                </div>
                <div style={{ fontSize: '0.76rem', color: '#475569', marginBottom: '0.65rem' }}>
                  <strong>Objective:</strong> {liveState?.objective || 'CONTAIN + PROTECT + EVACUATE'}
                </div>
                <div className="plan-item-check"><span className="check-icon">✓</span> Hazmat team dispatched (R0433)</div>
                <div className="plan-item-check"><span className="check-icon">✓</span> Fire containment unit en route (R0199)</div>
                <div className="plan-item-check"><span className="check-icon">✓</span> Ambulances assigned to trauma centers</div>
                <div className="plan-item-check"><span className="check-icon">✓</span> Safe ingress route calculated (bypassing red zone)</div>
                <div className="plan-item-check"><span className="check-icon">✓</span> Emergency hospital beds reserved</div>
                <div className="plan-item-check"><span className="check-icon">✓</span> Safe shelter capacity verified</div>

                {/* Step 14: Human Review Required Callout */}
                {pendingApprovals.length > 0 && (
                  <div className="review-callout-box">
                    <div className="review-callout-header">
                      <span>⚠</span>
                      <span>HUMAN REVIEW REQUIRED</span>
                    </div>
                    <div className="review-callout-body">
                      {pendingApprovals[0].title} ({pendingApprovals[0].people_affected} affected)
                    </div>
                    <div className="review-callout-actions">
                      <button
                        className="btn-review-approve"
                        onClick={() => handleApprovalDecision(pendingApprovals[0].action_id, 'APPROVE')}
                      >
                        [ APPROVE ]
                      </button>
                      <button
                        className="btn-review-modify"
                        onClick={() => {
                          setSelectedAction(pendingApprovals[0]);
                          setShowApprovalModal(true);
                        }}
                      >
                        [ MODIFY ]
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Card 3: AI Activity Stream (Step 22) */}
              <div className="ops-sidebar-card" style={{ flex: 1 }}>
                <div className="ops-sidebar-title">
                  <span>AI ACTIVITY</span>
                  <span className="source-tag model">10 AGENTS</span>
                </div>
                <div className="ai-activity-feed">
                  {aiActivity.slice(0, 7).map((item, idx) => (
                    <div key={idx} className="ai-activity-row">
                      <span className="ai-activity-time">{item.time}</span>
                      <span className="ai-activity-agent">{item.agent}</span>
                      <span className="ai-activity-desc">{item.action} — {item.details}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 3: INCIDENTS CATALOG VIEW                                            */}
        {/* ========================================================================= */}
        {activeNav === 'incidents' && (
          <div className="content-body-scroll" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>ACTIVE EMERGENCY INCIDENTS</h2>
                <p style={{ fontSize: '0.82rem', color: '#64748b' }}>Select an active emergency or register a new crisis.</p>
              </div>
              <button className="btn-open-response" onClick={() => setShowCreateModal(true)}>
                + Register New Incident
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
              {incidentsList.map((inc) => (
                <div
                  key={inc.incident_id}
                  style={{
                    background: '#ffffff',
                    border: selectedIncidentId === inc.incident_id ? '2px solid #2563eb' : '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '1.15rem',
                    cursor: 'pointer',
                  }}
                  onClick={() => {
                    setSelectedIncidentId(inc.incident_id);
                    setActiveNav('operations');
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.45rem' }}>
                    <span style={{ fontWeight: 800, color: '#ef4444' }}>🔴 {inc.incident_id}</span>
                    <span className="source-tag live">SEV {inc.severity}/10</span>
                  </div>
                  <div style={{ fontWeight: 800, fontSize: '0.95rem', color: '#0f172a', marginBottom: '0.25rem' }}>
                    {inc.plant} — {inc.type?.replace(/_/g, ' ')}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: '0.85rem' }}>
                    Substance: {inc.chemical || 'Industrial Substance'} | {inc.people_affected || 25} Affected
                  </div>
                  <button
                    className="btn-secondary-action"
                    style={{ width: '100%', fontSize: '0.75rem', padding: '0.4rem' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedIncidentId(inc.incident_id);
                      setActiveNav('operations');
                    }}
                  >
                    Open Incident Workspace →
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 4: RESPONDERS FLEET & TELEMETRY (Step 5)                             */}
        {/* ========================================================================= */}
        {activeNav === 'responders' && (
          <div className="content-body-scroll" style={{ padding: '1.25rem' }}>
            <div style={{ marginBottom: '1.25rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>DISPATCHED RESPONDERS & GPS TELEMETRY</h2>
              <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
                Real-time positioning, dynamic turn-by-turn routing, and live traffic-adjusted ETAs.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
              {responders.map((u) => (
                <div key={u.resource_id} className="hospital-oper-card">
                  <div className="hospital-card-header">
                    <div>
                      <div style={{ fontSize: '0.7rem', fontWeight: 800, color: '#64748b' }}>{u.resource_id}</div>
                      <div className="hospital-name">{u.name}</div>
                    </div>
                    <span className="hosp-badge accepting">{u.status}</span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.45rem', fontSize: '0.76rem', color: '#334155' }}>
                    <div>Speed: <strong>{u.speed_kmh} km/h</strong></div>
                    <div>Heading: <strong>{u.heading_deg}°</strong></div>
                    <div>Distance: <strong>{u.distance_km} km</strong></div>
                    <div>Destination: <strong>{u.destination}</strong></div>
                  </div>

                  <div style={{ background: '#f8fafc', padding: '0.55rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', marginBottom: '0.25rem' }}>
                      <span>Dynamic ETA: <strong style={{ color: '#2563eb' }}>{u.eta_display}</strong></span>
                      <span className="source-tag simulation">{u.data_source || 'SIMULATION ROUTE'}</span>
                    </div>
                    <div style={{ fontSize: '0.68rem', color: '#64748b' }}>
                      Normal: {Math.round(u.normal_eta_seconds / 60)}m | Traffic: {Math.round(u.traffic_eta_seconds / 60)}m (Corridor: {u.route_id})
                    </div>
                  </div>

                  <button
                    className="btn-open-response"
                    style={{ width: '100%', justifyContent: 'center', fontSize: '0.75rem', padding: '0.45rem' }}
                    onClick={() => {
                      setTrackedUnitId(u.resource_id);
                      setActiveNav('operations');
                    }}
                  >
                    [ TRACK VEHICLE ON MAP ]
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 5: MEDICAL OPERATIONS (Step 9 & 19)                                  */}
        {/* ========================================================================= */}
        {activeNav === 'medical' && (
          <div className="content-body-scroll" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>MEDICAL OPERATIONS & TRAUMA CENTERS</h2>
                <p style={{ fontSize: '0.82rem', color: '#64748b' }}>Emergency bed capacity, ICU availability, and casualty triage distribution.</p>
              </div>
              <button className="sim-btn" onClick={() => handleSimulateHospitalFull('H002')}>
                Simulate Hospital Saturated
              </button>
            </div>

            <div className="medical-cards-grid">
              {hospitals.map((h) => (
                <div key={h.hospital_id} className="hospital-oper-card">
                  <div className="hospital-card-header">
                    <div>
                      <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 800 }}>{h.hospital_id}</div>
                      <div className="hospital-name">{h.name}</div>
                    </div>
                    <span className={`hosp-badge ${h.status.toLowerCase()}`}>
                      ● {h.status}
                    </span>
                  </div>

                  <div>
                    <div className="capacity-metric-row">
                      <span>Emergency Beds</span>
                      <span>{h.emergency_capacity_free} Free / {h.emergency_capacity_total} Total</span>
                    </div>
                    <div className="capacity-progress-bar">
                      <div
                        className={`capacity-progress-fill ${h.emergency_capacity_free === 0 ? 'full' : ''}`}
                        style={{ width: `${Math.min(100, Math.round(((h.emergency_capacity_total - h.emergency_capacity_free) / h.emergency_capacity_total) * 100))}%` }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="capacity-metric-row">
                      <span>ICU Beds</span>
                      <span>{h.icu_free} Free / {h.icu_total} Total</span>
                    </div>
                    <div className="capacity-progress-bar">
                      <div
                        className={`capacity-progress-fill ${h.icu_free === 0 ? 'full' : ''}`}
                        style={{ width: `${Math.min(100, Math.round(((h.icu_total - h.icu_free) / h.icu_total) * 100))}%` }}
                      ></div>
                    </div>
                  </div>

                  <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #f1f5f9', paddingTop: '0.5rem' }}>
                    <span>Distance: {h.distance_km} km</span>
                    <span>Ambulance ETA: {h.eta_minutes} min</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 6: EVACUATION & SHELTERS (Step 13 & 20)                              */}
        {/* ========================================================================= */}
        {activeNav === 'evacuation' && (
          <div className="content-body-scroll" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>EVACUATION & SHELTER CAPACITY</h2>
                <p style={{ fontSize: '0.82rem', color: '#64748b' }}>Civilian safe zones, live occupancy fill rates, and protected ingress routes.</p>
              </div>
              <button className="sim-btn" onClick={() => handleSimulateShelterFull('S001')}>
                Simulate Shelter Saturated
              </button>
            </div>

            <div className="evacuation-cards-grid">
              {shelters.map((s) => (
                <div key={s.shelter_id} className="shelter-oper-card">
                  <div className="hospital-card-header">
                    <div>
                      <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 800 }}>{s.shelter_id}</div>
                      <div className="hospital-name">{s.name}</div>
                    </div>
                    <span className={`hosp-badge ${s.status === 'FULL' ? 'full' : 'accepting'}`}>
                      ● {s.status}
                    </span>
                  </div>

                  <div style={{ margin: '0.75rem 0' }}>
                    <div className="capacity-metric-row">
                      <span>Occupancy</span>
                      <span>{s.current_occupancy} / {s.total_capacity} beds ({s.fill_rate_pct}% full)</span>
                    </div>
                    <div className="capacity-progress-bar">
                      <div
                        className={`capacity-progress-fill ${s.status === 'FULL' ? 'full' : ''}`}
                        style={{ width: `${s.fill_rate_pct}%` }}
                      ></div>
                    </div>
                  </div>

                  <div style={{ fontSize: '0.75rem', color: '#334155', display: 'flex', justifyContent: 'space-between' }}>
                    <span>Available Capacity: <strong>{s.available_capacity}</strong></span>
                    <span style={{ color: '#10b981', fontWeight: 700 }}>Safe Route: {s.safe_route_status || 'CLEAR'}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 7: AI ACTIVITY STREAM (Step 22)                                      */}
        {/* ========================================================================= */}
        {activeNav === 'ai_activity' && (
          <div className="content-body-scroll" style={{ padding: '1.25rem' }}>
            <div style={{ marginBottom: '1.25rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>10-AGENT AUTONOMOUS ACTIVITY STREAM</h2>
              <p style={{ fontSize: '0.82rem', color: '#64748b' }}>Real-time chronological log of agent decisions, hazard predictions, and replanning triggers.</p>
            </div>

            <div style={{ background: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '1rem' }}>
              <div className="ai-activity-feed">
                {aiActivity.map((item, idx) => (
                  <div key={idx} className="ai-activity-row" style={{ padding: '0.65rem 0.85rem' }}>
                    <span className="ai-activity-time">{item.time}</span>
                    <span className="ai-activity-agent" style={{ color: '#2563eb' }}>{item.agent}</span>
                    <span className="ai-activity-desc">
                      <strong>{item.action}</strong> — {item.details}
                    </span>
                    <span className="source-tag model">{Math.round((item.confidence || 0.95) * 100)}% CONF</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 8: AUDIT EVENT BUS (Step 27)                                         */}
        {/* ========================================================================= */}
        {activeNav === 'audit' && (
          <div className="content-body-scroll audit-container">
            <div style={{ marginBottom: '1.25rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>INCIDENT AUDIT LOG & EVENT BUS</h2>
              <p style={{ fontSize: '0.82rem', color: '#64748b' }}>Every event is published to the central event bus and permanently auditable.</p>
            </div>

            <div className="audit-table-card">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Event ID</th>
                    <th>Type</th>
                    <th>Source</th>
                    <th>Severity</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {auditEvents.map((e) => (
                    <tr key={e.event_id}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>{e.time_formatted || e.timestamp?.slice(11, 19)}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>{e.event_id}</td>
                      <td><span className="evt-type-tag">{e.type}</span></td>
                      <td>{e.source}</td>
                      <td>
                        <span className={`source-tag ${e.severity === 'CRITICAL' ? 'simulation' : e.severity === 'HIGH' ? 'model' : 'live'}`}>
                          {e.severity}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.75rem' }}>{JSON.stringify(e.data)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 9: FIELD RESPONDER TERMINAL (Step 18)                                */}
        {/* ========================================================================= */}
        {activeNav === 'responder' && (
          <div className="content-body-scroll" style={{ padding: '1.25rem', maxWidth: '640px', margin: '0 auto' }}>
            <div style={{ background: '#0f172a', color: '#ffffff', borderRadius: '8px', padding: '1.25rem', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 800 }}>FIELD RESPONDER TERMINAL</span>
                <span className="source-tag live">● GPS CONNECTED</span>
              </div>
              <h2 style={{ fontSize: '1.35rem', fontWeight: 800, marginBottom: '0.35rem' }}>{leadResponder.name || 'R0433 HAZMAT TEAM'}</h2>
              <div style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>Destination: <strong>{leadResponder.destination || 'Plant B Chemical Complex'}</strong></div>
            </div>

            <div style={{ background: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '1.15rem', marginBottom: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.85rem', marginBottom: '1rem' }}>
                <div>
                  <div style={{ fontSize: '0.72rem', color: '#64748b' }}>DYNAMIC ETA</div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#2563eb' }}>{leadResponder.eta_display}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: '#64748b' }}>GROUND SPEED</div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 800 }}>{leadResponder.speed_kmh} km/h</div>
                </div>
              </div>

              <div style={{ fontSize: '0.78rem', color: '#334155', marginBottom: '0.65rem' }}>
                <strong>Active Route:</strong> {leadResponder.route_id} ({leadResponder.route_status || 'ACTIVE'})
              </div>

              <div style={{ background: '#fffbeb', border: '1px solid #fde68a', padding: '0.65rem', borderRadius: '4px', fontSize: '0.74rem', color: '#78350f', marginBottom: '1rem' }}>
                ⚠️ <strong>HAZARD ADVISORY:</strong> Sulfur Dioxide Toxic Plume downwind. Approach from upwind sector. Level A PPE mandatory.
              </div>

              <div style={{ display: 'flex', gap: '0.65rem' }}>
                <button
                  className="btn-open-response"
                  style={{ flex: 1, justifyContent: 'center' }}
                  onClick={() => handleUpdateResponderStatus('ARRIVED')}
                >
                  ARRIVED ON SCENE
                </button>
                <button
                  className="sim-btn danger"
                  style={{ padding: '0.6rem 1rem' }}
                  onClick={() => handleUpdateResponderStatus('SOS')}
                >
                  🚨 SOS EMERGENCY
                </button>
              </div>
            </div>

            {/* Turn by turn */}
            <div style={{ background: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '1.15rem' }}>
              <h3 style={{ fontSize: '0.82rem', fontWeight: 800, marginBottom: '0.75rem' }}>TURN-BY-TURN INSTRUCTIONS</h3>
              {leadResponder.turn_by_turn?.map((step) => (
                <div key={step.step} style={{ display: 'flex', gap: '0.65rem', fontSize: '0.76rem', padding: '0.45rem 0', borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ fontWeight: 800, color: '#2563eb' }}>{step.step}.</span>
                  <div style={{ flex: 1 }}>{step.instruction} ({step.distance_km} km)</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 10: PUBLIC SAFETY PORTAL (Step 21)                                   */}
        {/* ========================================================================= */}
        {activeNav === 'public' && (
          <div className="content-body-scroll" style={{ padding: '1.25rem', maxWidth: '680px', margin: '0 auto' }}>
            <div style={{ background: '#ef4444', color: '#ffffff', borderRadius: '8px', padding: '1.25rem', marginBottom: '1.25rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.08em', marginBottom: '0.35rem' }}>
                OFFICIAL CIVIL EMERGENCY BULLETIN
              </div>
              <h2 style={{ fontSize: '1.35rem', fontWeight: 800 }}>{publicData?.emergency_headline || 'CHEMICAL ALERT'}</h2>
              <p style={{ fontSize: '0.85rem', marginTop: '0.35rem' }}>{publicData?.precautionary_instruction}</p>
            </div>

            <div style={{ background: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '1.15rem', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '0.85rem', fontWeight: 800, marginBottom: '0.75rem' }}>DANGER ZONE CLASSIFICATION</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.78rem' }}>
                <div style={{ background: '#fee2e2', padding: '0.5rem', borderRadius: '4px', borderLeft: '4px solid #ef4444' }}>
                  <strong>Red Exclusion Zone ({spread.red_zone_m || 380}m):</strong> Mandatory Immediate Evacuation
                </div>
                <div style={{ background: '#ffedd5', padding: '0.5rem', borderRadius: '4px', borderLeft: '4px solid #f97316' }}>
                  <strong>Orange Buffer Zone ({spread.orange_zone_m || 620}m):</strong> Shelter-in-Place, Close Windows
                </div>
                <div style={{ background: '#fef9c3', padding: '0.5rem', borderRadius: '4px', borderLeft: '4px solid #eab308' }}>
                  <strong>Yellow Advisory Zone ({spread.yellow_zone_m || 1100}m):</strong> General Precaution & Preparedness
                </div>
              </div>
            </div>

            <div style={{ background: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '1.15rem', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '0.85rem', fontWeight: 800, marginBottom: '0.75rem' }}>DESIGNATED EVACUATION SHELTERS</h3>
              {shelters.slice(0, 2).map((s) => (
                <div key={s.shelter_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.45rem 0', borderBottom: '1px solid #f1f5f9', fontSize: '0.78rem' }}>
                  <div>
                    <strong>{s.name}</strong>
                    <div style={{ fontSize: '0.72rem', color: '#64748b' }}>Safe Route: {s.safe_route_status || 'CLEAR'}</div>
                  </div>
                  <span className="source-tag live">Available</span>
                </div>
              ))}
            </div>

            <div style={{ background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '1rem', fontSize: '0.78rem' }}>
              <strong>EMERGENCY HELPLINES:</strong> Central Command: <strong>112</strong> | Poison Control: <strong>1800-425-1111</strong> | Medical Dispatch: <strong>108</strong>
            </div>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* 3. HUMAN APPROVAL MODAL (Step 14)                                         */}
      {/* ========================================================================= */}
      {showApprovalModal && selectedAction && (
        <div className="clean-modal-backdrop">
          <div className="clean-modal-box">
            <div className="clean-modal-head">
              <h3>COMMANDER AUTHORIZATION REQUIRED</h3>
              <button className="btn-modal-close" onClick={() => setShowApprovalModal(false)}>✕</button>
            </div>
            <div className="clean-modal-body">
              <div style={{ fontSize: '0.82rem', marginBottom: '0.85rem' }}>
                <strong>Action:</strong> {selectedAction.title}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#475569', marginBottom: '0.85rem' }}>
                <strong>Reason:</strong> {selectedAction.reason}
              </div>
              <div className="form-row">
                <label>Commander Directives / Modifications:</label>
                <textarea
                  className="clean-modal-textarea"
                  rows="3"
                  value={approvalNotes}
                  onChange={(e) => setApprovalNotes(e.target.value)}
                  placeholder="Enter operational constraints, shelter preferences, or ingress route specifics..."
                ></textarea>
              </div>
            </div>
            <div className="modal-foot">
              <button
                className="btn-modal-cancel"
                onClick={() => handleApprovalDecision(selectedAction.action_id, 'REJECT')}
              >
                Reject Action
              </button>
              <button
                className="btn-modal-submit"
                onClick={() => handleApprovalDecision(selectedAction.action_id, 'MODIFY')}
              >
                Authorize with Modifications
              </button>
              <button
                className="btn-modal-submit"
                style={{ background: '#10b981' }}
                onClick={() => handleApprovalDecision(selectedAction.action_id, 'APPROVE')}
              >
                Approve Directive
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 4. CREATE INCIDENT MODAL (Step 5)                                         */}
      {/* ========================================================================= */}
      {showCreateModal && (
        <div className="clean-modal-backdrop">
          <div className="clean-modal-box">
            <div className="clean-modal-head">
              <h3>REGISTER NEW EMERGENCY INCIDENT</h3>
              <button className="btn-modal-close" onClick={() => setShowCreateModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateIncident}>
              <div className="clean-modal-body">
                <div className="form-row">
                  <label>Incident Type</label>
                  <select
                    value={newIncidentForm.incident_type}
                    onChange={(e) => setNewIncidentForm({ ...newIncidentForm, incident_type: e.target.value })}
                  >
                    <option value="Chemical_Leak">Chemical Leak</option>
                    <option value="Chemical_Fire">Chemical Fire</option>
                    <option value="Explosion">Industrial Explosion</option>
                    <option value="Toxic_Release">Toxic Vapor Release</option>
                  </select>
                </div>
                <div className="form-row">
                  <label>Facility Location</label>
                  <input
                    type="text"
                    value={newIncidentForm.location}
                    onChange={(e) => setNewIncidentForm({ ...newIncidentForm, location: e.target.value })}
                  />
                </div>
                <div className="form-row">
                  <label>Chemical Substance</label>
                  <input
                    type="text"
                    value={newIncidentForm.chemical}
                    onChange={(e) => setNewIncidentForm({ ...newIncidentForm, chemical: e.target.value })}
                  />
                </div>
                <div className="form-row">
                  <label>People Affected (Estimate)</label>
                  <input
                    type="number"
                    value={newIncidentForm.people_affected}
                    onChange={(e) => setNewIncidentForm({ ...newIncidentForm, people_affected: e.target.value })}
                  />
                </div>
                <div className="form-row">
                  <label>Initial Severity (1-10)</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={newIncidentForm.severity}
                    onChange={(e) => setNewIncidentForm({ ...newIncidentForm, severity: e.target.value })}
                  />
                </div>
              </div>
              <div className="modal-foot">
                <button type="button" className="btn-modal-cancel" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-modal-submit" disabled={loading}>
                  {loading ? 'Initiating Pipeline...' : 'Deploy Emergency Response'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
