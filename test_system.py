"""
Comprehensive Integration Test Suite for the Multi-Agent Crisis Management System.
Tests all 10 agents, all API endpoints, and dynamic replanning using FastAPI TestClient.
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["agents_active"] == 10
    print("[PASS] GET /api/health")

def test_list_incidents():
    resp = client.get("/api/incidents?limit=5")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "incidents" in data
    assert len(data["incidents"]) == 5
    print("[PASS] GET /api/incidents")

def test_create_incident():
    payload = {
        "incident_id": "TEST-INC-99",
        "incident_type": "Chemical_Fire",
        "location": "Plant_C",
        "chemical": "Chlorine",
        "people_affected": 45,
        "fire": True,
        "explosion": False,
        "severity": 8,
        "x": 48.0,
        "y": 70.0
    }
    resp = client.post("/api/incidents", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "registered"
    assert data["incident"]["incident_id"] == "TEST-INC-99"
    print("[PASS] POST /api/incidents")

def test_respond_endpoint():
    resp = client.post("/api/incidents/I001/respond")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # Verify top-level structure required by frontend
    for key in ["incident", "severity", "hazards", "spread", "resources", "medical", "routes", "evacuation", "communications", "replanning"]:
        assert key in data, f"Missing key: {key}"

    assert data["incident"]["incident_id"] == "I001"
    assert len(data["resources"]) > 0
    assert len(data["routes"]) > 0
    assert "patient_distribution" in data["medical"]
    assert "assigned_shelters" in data["evacuation"]
    assert "alerts" in data["communications"]
    print("[PASS] POST /api/incidents/I001/respond (Full 10-Agent Pipeline)")

def test_replan_endpoint():
    replan_payload = {
        "new_events": ["Explosion in Sector 4", "Wind shifted to East"],
        "unavailable_resources": ["R0002", "R0007"],
        "newly_blocked_roads": ["R00001", "R00002"],
        "escalate_severity": True
    }
    resp = client.post("/api/incidents/I001/replan", json=replan_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["replanning"]["is_replanned"] is True
    assert data["replanning"]["version"] >= 2
    # Verify failed resources not in assignments
    assigned_ids = [r["resource_id"] for r in data["resources"]]
    assert "R0002" not in assigned_ids
    assert "R0007" not in assigned_ids
    print("[PASS] POST /api/incidents/I001/replan (Dynamic Replanning)")

def test_resources_endpoint():
    resp = client.get("/api/resources?status=Available&limit=10")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["resources"]) <= 10
    print("[PASS] GET /api/resources")

def test_hospitals_endpoint():
    resp = client.get("/api/hospitals?limit=5")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["hospitals"]) == 5
    print("[PASS] GET /api/hospitals")

def test_shelters_endpoint():
    resp = client.get("/api/shelters?limit=5")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["shelters"]) == 5
    print("[PASS] GET /api/shelters")

def test_routes_endpoint():
    resp = client.get("/api/routes?from_node=N0001&to_node=N0010")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert len(data["roads"]) > 0
    print("[PASS] GET /api/routes")

def test_live_incident_state():
    resp = client.get("/api/incidents/I001/live-state")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "overview" in data
    assert "hazard_dispersion" in data
    assert "tracking_fleet" in data
    assert len(data["tracking_fleet"]) > 0
    assert "approval_queue" in data
    assert "event_timeline" in data
    print("[PASS] GET /api/incidents/I001/live-state")

def test_telemetry_tick():
    resp = client.post("/api/incidents/I001/tick-telemetry")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["tracking_fleet"]) > 0
    unit0 = data["tracking_fleet"][0]
    assert "progress_pct" in unit0
    assert "eta_minutes" in unit0
    print("[PASS] POST /api/incidents/I001/tick-telemetry")

def test_event_inject_and_closed_loop():
    payload = {
        "event_type": "ROAD_BLOCKED",
        "details": {"road_id": "R03108"}
    }
    resp = client.post("/api/incidents/I001/event-inject", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["replanning"]["is_replanned"] is True
    assert data["replanning"]["version"] >= 2
    assert len(data["approval_queue"]) > 0
    print("[PASS] POST /api/incidents/I001/event-inject (Closed Loop Replanning)")

def test_human_approval():
    st = client.get("/api/incidents/I001/live-state").json()
    action_id = st["approval_queue"][0]["action_id"]
    payload = {
        "decision": "APPROVE",
        "modifications": "Commander verified Level A Hazmat protocol."
    }
    resp = client.post(f"/api/incidents/I001/approvals/{action_id}/decision", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    appr = [a for a in data["approval_queue"] if a["action_id"] == action_id][0]
    assert appr["status"] == "APPROVED"
    print("[PASS] POST /api/incidents/I001/approvals/{action_id}/decision")

def test_responder_terminal():
    resp = client.get("/api/responder/R0433")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "unit" in data
    assert "turn_by_turn" in data
    assert len(data["turn_by_turn"]) > 0

    st_resp = client.post("/api/responder/R0433/status", json={"status": "ARRIVED", "notes": "On scene"})
    assert st_resp.status_code == 200, st_resp.text
    print("[PASS] GET & POST /api/responder/R0433")

def test_public_safety_portal():
    resp = client.get("/api/public/incident/I001")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "emergency_headline" in data
    assert "hazard_zones" in data
    assert "recommended_shelters" in data
    assert "emergency_helpline" in data
    print("[PASS] GET /api/public/incident/I001")

if __name__ == "__main__":
    print("=" * 50)
    print("Running Full System Integration & Closed-Loop Suite...")
    print("=" * 50)
    test_health()
    test_list_incidents()
    test_create_incident()
    test_respond_endpoint()
    test_replan_endpoint()
    test_resources_endpoint()
    test_hospitals_endpoint()
    test_shelters_endpoint()
    test_routes_endpoint()
    test_live_incident_state()
    test_telemetry_tick()
    test_event_inject_and_closed_loop()
    test_human_approval()
    test_responder_terminal()
    test_public_safety_portal()
    print("=" * 50)
    print(">>> ALL 15 TESTS COMPLETED AND VERIFIED SUCCESSFULLY! <<<")
    print("=" * 50)

