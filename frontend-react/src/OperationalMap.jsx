import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Tile layer definitions for real-world visualization
const TILE_LAYERS = {
  streets: {
    name: 'Real-World Streets (OSM)',
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    options: {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
  },
  satellite: {
    name: 'Real-World Satellite (Esri)',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    options: {
      maxZoom: 19,
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    },
  },
  dark: {
    name: 'Tactical Dark (CartoDB)',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    options: {
      maxZoom: 19,
      subdomains: 'abcd',
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    },
  },
};

export default function OperationalMap({
  liveState,
  trackedUnitId,
  onSelectUnit,
  height = '100%',
}) {
  const containerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const tileLayerRef = useRef(null);
  const layersGroupRef = useRef(null);
  const [activeBaseLayer, setActiveBaseLayer] = useState('streets');

  // Default coordinate center: Chennai Industrial Sector around Plant B
  const incLat = liveState?.coordinates?.lat || 12.9920;
  const incLng = liveState?.coordinates?.lng || 80.2480;

  // 1. Initialize Map on Mount & Clean up on Unmount
  useEffect(() => {
    if (!containerRef.current) return;

    // Clean up any stale map instance
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const map = L.map(containerRef.current, {
      center: [incLat, incLng],
      zoom: 13,
      zoomControl: true,
      fadeAnimation: true,
    });

    // Add selected real-world tile layer
    const layerConfig = TILE_LAYERS[activeBaseLayer] || TILE_LAYERS.streets;
    const tile = L.tileLayer(layerConfig.url, layerConfig.options).addTo(map);
    tileLayerRef.current = tile;

    // Layer group for all dynamic overlays
    const overlays = L.layerGroup().addTo(map);
    layersGroupRef.current = overlays;
    mapInstanceRef.current = map;

    // Force size invalidation to guarantee full-resolution rendering
    const t1 = setTimeout(() => map.invalidateSize(), 150);
    const t2 = setTimeout(() => map.invalidateSize(), 500);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // 2. Handle Base Layer Switching (Streets vs Satellite vs Dark)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current);
    }

    const cfg = TILE_LAYERS[activeBaseLayer] || TILE_LAYERS.streets;
    tileLayerRef.current = L.tileLayer(cfg.url, cfg.options).addTo(map);
  }, [activeBaseLayer]);

  // 3. Draw and Update Real-World Operational Overlays
  useEffect(() => {
    const map = mapInstanceRef.current;
    const layer = layersGroupRef.current;
    if (!map || !layer) return;

    layer.clearLayers();

    const spread = liveState?.spread || {};
    const responders = liveState?.responders || [];
    const hospitals = liveState?.hospitals || [];
    const shelters = liveState?.shelters || [];
    const roadClosures = liveState?.road_closures || [];
    const isRoadBlocked = roadClosures.includes('R03108') || roadClosures.length > 0;
    const leadUnit = responders[0] || {};

    // -------------------------------------------------------------
    // LAYER 1: ALOHA Hazard Plume Dispersion Circles
    // -------------------------------------------------------------
    // Yellow Advisory Zone
    L.circle([incLat, incLng], {
      radius: spread.yellow_zone_m || 1100,
      color: '#eab308',
      weight: 1.5,
      dashArray: '5, 5',
      fillColor: '#fef08a',
      fillOpacity: 0.18,
    }).addTo(layer).bindTooltip(`Yellow Advisory Zone (${spread.yellow_zone_m || 1100}m)`);

    // Orange Buffer Zone
    L.circle([incLat, incLng], {
      radius: spread.orange_zone_m || 620,
      color: '#f97316',
      weight: 2,
      dashArray: '4, 4',
      fillColor: '#fed7aa',
      fillOpacity: 0.28,
    }).addTo(layer).bindTooltip(`Orange Buffer Zone (${spread.orange_zone_m || 620}m)`);

    // Red Exclusion Zone
    L.circle([incLat, incLng], {
      radius: spread.red_zone_m || 380,
      color: '#ef4444',
      weight: 2.5,
      fillColor: '#fca5a5',
      fillOpacity: 0.48,
    }).addTo(layer).bindTooltip(`Red Exclusion Zone (${spread.red_zone_m || 380}m) — Evacuate Immediately`);

    // -------------------------------------------------------------
    // LAYER 2: Incident Epicenter Pulsing Marker
    // -------------------------------------------------------------
    const incidentIcon = L.divIcon({
      className: 'aidroute-pulse-pin',
      html: `<div class="pin-halo"></div><div class="pin-core"></div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });

    const incMarker = L.marker([incLat, incLng], { icon: incidentIcon }).addTo(layer);
    incMarker.bindPopup(`
      <div style="font-family: Inter, sans-serif; font-size: 12px; min-width: 220px;">
        <div style="font-weight: 800; color: #ef4444; font-size: 13px; margin-bottom: 3px;">
          🔴 ${liveState?.incident_id || 'I001'} ${liveState?.type?.replace(/_/g, ' ') || 'Chemical Leak'}
        </div>
        <div><strong>Facility:</strong> ${liveState?.location || 'Plant B'}</div>
        <div><strong>Toxic Substance:</strong> ${liveState?.chemical || 'Sulfur Dioxide'}</div>
        <div><strong>Wind Direction:</strong> ${spread.wind_direction || 'NW'} (${spread.wind_speed_ms || 6.5} m/s)</div>
        <div><strong>Exclusion Radius:</strong> ${spread.red_zone_m || 380} meters</div>
        <div><strong>People At Risk:</strong> ${liveState?.people_at_risk || 250} civilians</div>
      </div>
    `);

    // -------------------------------------------------------------
    // LAYER 3: Ingress Corridors & Reroute Detours
    // -------------------------------------------------------------
    const primaryPath = leadUnit.route_geometry?.coordinates || [
      [12.9650, 80.2150],
      [12.9750, 80.2280],
      [12.9830, 80.2390],
      [incLat, incLng],
    ];

    // Primary Active Route (Blue solid or Amber dashed if rerouted)
    L.polyline(primaryPath, {
      color: isRoadBlocked ? '#d97706' : '#2563eb',
      weight: 5,
      dashArray: isRoadBlocked ? '7, 7' : undefined,
      opacity: 0.9,
    }).addTo(layer).bindTooltip(
      `Route: ${leadUnit.route_id || 'R03108'} (${leadUnit.route_status || 'ACTIVE'}) - ETA: ${leadUnit.eta_display || '08:21'}`
    );

    // Blocked Road Marker
    if (isRoadBlocked) {
      L.polyline([
        [12.9810, 80.2350],
        [12.9880, 80.2420],
      ], {
        color: '#dc2626',
        weight: 7,
        dashArray: '6, 6',
      }).addTo(layer).bindPopup(`
        <div style="font-family: Inter, sans-serif; font-size: 12px; color: #991b1b;">
          <strong>🚧 ROAD R03108 BLOCKED</strong><br/>
          Corridor obstructed by toxic chemical plume and emergency barrier.<br/>
          Detour active via Northern Bypass R03204.
        </div>
      `);
    }

    // Safe Evacuation Corridor to Shelter S001
    L.polyline([
      [incLat, incLng],
      [12.9980, 80.2600],
      [13.0080, 80.2720],
    ], {
      color: '#10b981',
      weight: 4,
      opacity: 0.85,
    }).addTo(layer).bindTooltip('Safe Evacuation Corridor to Anna Nagar Shelter (S001)');

    // -------------------------------------------------------------
    // LAYER 4: Dispatched Responders with Moving GPS Coordinates
    // -------------------------------------------------------------
    responders.forEach((unit) => {
      const uLat = unit.latitude || unit.current_location?.lat || 12.9716;
      const uLng = unit.longitude || unit.current_location?.lng || 80.2200;
      const isLead = unit.resource_id === trackedUnitId;

      const respIcon = L.divIcon({
        className: 'responder-leaflet-marker',
        html: `
          <div class="resp-pin-box ${unit.type.toLowerCase().includes('hazmat') ? 'hazmat' : 'fire'}" style="${
            isLead ? 'border: 2px solid #0f172a; box-shadow: 0 0 8px rgba(37,99,235,0.6); transform: scale(1.08);' : ''
          }">
            <span style="font-size: 14px;">${
              unit.type.toLowerCase().includes('hazmat')
                ? '☢'
                : unit.type.toLowerCase().includes('ambulance')
                ? '🚑'
                : '🚒'
            }</span>
            <span class="resp-label">${unit.resource_id} (${unit.eta_display || unit.eta_minutes + 'm'})</span>
          </div>
        `,
        iconSize: [94, 26],
        iconAnchor: [47, 13],
      });

      const marker = L.marker([uLat, uLng], { icon: respIcon }).addTo(layer);
      marker.bindPopup(`
        <div style="font-family: Inter, sans-serif; font-size: 12px; min-width: 200px;">
          <div style="font-weight: 800; font-size: 13px; color: #0f172a;">${unit.name}</div>
          <div><strong>Status:</strong> ${unit.status}</div>
          <div><strong>Speed:</strong> ${unit.speed_kmh} km/h (Heading: ${unit.heading_deg}°)</div>
          <div><strong>Destination:</strong> ${unit.destination}</div>
          <div style="margin-top: 4px; padding: 4px; background: #f1f5f9; border-radius: 4px;">
            <strong>Dynamic ETA:</strong> <span style="color: #2563eb; font-weight: 800;">${unit.eta_display}</span><br/>
            Normal: ${Math.round(unit.normal_eta_seconds / 60)}m | Traffic: ${Math.round(unit.traffic_eta_seconds / 60)}m
          </div>
          <div style="font-size: 10px; color: #64748b; margin-top: 3px;">
            Route: ${unit.route_id} [${unit.data_source || 'SIMULATION ROUTE'}]
          </div>
        </div>
      `);

      if (onSelectUnit) {
        marker.on('click', () => onSelectUnit(unit.resource_id));
      }
    });

    // -------------------------------------------------------------
    // LAYER 5: Regional Hospitals
    // -------------------------------------------------------------
    hospitals.forEach((h) => {
      const isFull = h.status === 'FULL';
      const hIcon = L.divIcon({
        className: 'facility-leaflet-marker hospital',
        html: `
          <div class="fac-pin" style="background: ${isFull ? '#ef4444' : '#2563eb'}; border: 2px solid #ffffff; box-shadow: 0 2px 5px rgba(0,0,0,0.3); border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 13px;">
            🏥
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      L.marker([h.lat, h.lng], { icon: hIcon }).addTo(layer).bindPopup(`
        <div style="font-family: Inter, sans-serif; font-size: 12px; min-width: 190px;">
          <div style="font-weight: 800; color: #0f172a; margin-bottom: 2px;">🏥 ${h.name}</div>
          <div>Status: <span style="font-weight: 800; color: ${isFull ? '#dc2626' : '#166534'};">${h.status}</span></div>
          <div>Emergency Capacity: <strong>${h.emergency_capacity_free}</strong> Free / ${h.emergency_capacity_total} Total</div>
          <div>ICU Beds: <strong>${h.icu_free}</strong> Free / ${h.icu_total} Total</div>
          <div>Transit ETA: ${h.eta_minutes} min (${h.distance_km} km)</div>
        </div>
      `);
    });

    // -------------------------------------------------------------
    // LAYER 6: Safe Evacuation Shelters
    // -------------------------------------------------------------
    shelters.forEach((s) => {
      const isFull = s.status === 'FULL';
      const sIcon = L.divIcon({
        className: 'facility-leaflet-marker shelter',
        html: `
          <div class="fac-pin" style="background: ${isFull ? '#991b1b' : '#10b981'}; border: 2px solid #ffffff; box-shadow: 0 2px 5px rgba(0,0,0,0.3); border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 13px;">
            🏠
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      L.marker([s.lat, s.lng], { icon: sIcon }).addTo(layer).bindPopup(`
        <div style="font-family: Inter, sans-serif; font-size: 12px; min-width: 190px;">
          <div style="font-weight: 800; color: #0f172a; margin-bottom: 2px;">🏠 ${s.name}</div>
          <div>Status: <span style="font-weight: 800; color: ${isFull ? '#dc2626' : '#166534'};">${s.status}</span></div>
          <div>Occupancy: ${s.current_occupancy} / ${s.total_capacity} (${s.fill_rate_pct}% full)</div>
          <div>Available Beds: <strong>${s.available_capacity}</strong></div>
          <div>Safe Corridor: <span style="color: #10b981; font-weight: 700;">${s.safe_route_status || 'CLEAR'}</span></div>
        </div>
      `);
    });
  }, [liveState, trackedUnitId]);

  // Map Navigation Helper Controls
  const handleFocusIncident = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([incLat, incLng], 14, { duration: 1.2 });
    }
  };

  const handleFocusFleet = () => {
    if (mapInstanceRef.current && liveState?.responders?.length) {
      const bounds = L.latLngBounds(
        liveState.responders.map((r) => [
          r.latitude || r.current_location?.lat || incLat,
          r.longitude || r.current_location?.lng || incLng,
        ])
      );
      bounds.extend([incLat, incLng]);
      mapInstanceRef.current.fitBounds(bounds, { padding: [40, 40] });
    }
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: height, minHeight: '380px' }}>
      {/* 1. Leaflet Map DOM Node */}
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          minHeight: '380px',
          background: '#e2e8f0',
        }}
      ></div>

      {/* 2. Floating Real-World Map Layer Switcher (Streets / Satellite / Dark) */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          zIndex: 1000,
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(6px)',
          borderRadius: '6px',
          padding: '4px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.18)',
          border: '1px solid #cbd5e1',
          display: 'flex',
          gap: '4px',
        }}
      >
        <button
          style={{
            background: activeBaseLayer === 'streets' ? '#0f172a' : 'transparent',
            color: activeBaseLayer === 'streets' ? '#ffffff' : '#334155',
            border: 'none',
            borderRadius: '4px',
            padding: '4px 8px',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
          }}
          onClick={() => setActiveBaseLayer('streets')}
        >
          🗺️ Streets
        </button>
        <button
          style={{
            background: activeBaseLayer === 'satellite' ? '#0f172a' : 'transparent',
            color: activeBaseLayer === 'satellite' ? '#ffffff' : '#334155',
            border: 'none',
            borderRadius: '4px',
            padding: '4px 8px',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
          }}
          onClick={() => setActiveBaseLayer('satellite')}
        >
          🛰️ Satellite
        </button>
        <button
          style={{
            background: activeBaseLayer === 'dark' ? '#0f172a' : 'transparent',
            color: activeBaseLayer === 'dark' ? '#ffffff' : '#334155',
            border: 'none',
            borderRadius: '4px',
            padding: '4px 8px',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
          }}
          onClick={() => setActiveBaseLayer('dark')}
        >
          🌃 Dark
        </button>
      </div>

      {/* 3. Floating Quick-Focus Navigation Helpers */}
      <div
        style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          zIndex: 1000,
          display: 'flex',
          gap: '6px',
        }}
      >
        <button
          style={{
            background: '#ffffff',
            color: '#0f172a',
            border: '1px solid #cbd5e1',
            borderRadius: '4px',
            padding: '5px 10px',
            fontSize: '11px',
            fontWeight: 700,
            boxShadow: '0 2px 6px rgba(0,0,0,0.12)',
            cursor: 'pointer',
          }}
          onClick={handleFocusIncident}
        >
          🎯 Focus Incident
        </button>
        <button
          style={{
            background: '#ffffff',
            color: '#0f172a',
            border: '1px solid #cbd5e1',
            borderRadius: '4px',
            padding: '5px 10px',
            fontSize: '11px',
            fontWeight: 700,
            boxShadow: '0 2px 6px rgba(0,0,0,0.12)',
            cursor: 'pointer',
          }}
          onClick={handleFocusFleet}
        >
          🚒 Focus Fleet
        </button>
      </div>
    </div>
  );
}
