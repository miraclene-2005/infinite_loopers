# Industrial Accident Crisis Command AI — Multi-Agent Coordination System

A complete Python-based Multi-Agent Industrial Crisis Management and Emergency Coordination backend built for **GATEWAYS 2026** by Team **Infinite Loopers**.

---

## 🌟 Overview & Architecture

The system acts as a digital emergency control room. When an industrial accident is reported, 10 specialized software agents coordinate in an event-driven workflow to assess risks, model atmospheric plume dispersion, allocate limited emergency resources, dispatch ambulances, map safe routes, manage shelter capacity, and broadcast role-specific alerts.

```
                           [ INPUTS ]
                 (Sensors, Scenarios, Calls, API)
                               │
                               ▼
                   [ 1. Incident Detection ]
                               │
                               ▼
                  [ 2. Incident Assessment ]
                  ┌────────────┴────────────┐
                  ▼                         ▼
         [ 3. Hazard & Risk ]      [ 5. Resource Allocation ]
                  │                         │
                  ▼                         ▼
        [ 4. Spread Prediction ]   [ 6. Medical Response ]
                  │                         │
                  ▼                         │
        [ 7. Route & Logistics ]            │
                  │                         │
                  ▼                         │
       [ 8. Evacuation & Shelter ]          │
                  │                         │
                  └────────────┬────────────┘
                               ▼
                     [ 9. Communication ]
                               │
                               ▼
                 [ 10. Command & Replanning ] ◄─── (Dynamic Replanning Trigger)
                               │
                               ▼
                   [ Human Approval Gate ]
                               │
                               ▼
                 [ Control Room & API Clients ]
```

---

## 🤖 The 10 Specialized Agents

| # | Agent Name | Module | Responsibility & Tech |
|---|---|---|---|
| **1** | **Incident Detection** | `agents/incident_detection.py` | Ingests and normalizes accident signals from `incidents.csv`, `emergency_incident_scenarios_5000.csv`, or API calls. |
| **2** | **Incident Assessment** | `agents/incident_assessment.py` | Determines severity (CRITICAL, HIGH, etc.) and response priorities using rule-based reasoning with ML hooks. |
| **3** | **Hazard & Risk** | `agents/hazard_risk.py` | Identifies primary hazards (toxic, fire, blast, collapse) and secondary domino risks (BLEVE, vapor cloud spread). |
| **4** | **Hazard Spread Prediction** | `agents/hazard_spread.py` | ALOHA-informed Scikit-learn Random Forest model predicting red, orange, yellow zones and downwind directions. |
| **5** | **Emergency Resource Allocation** | `agents/resource_allocation.py` | Optimally allocates Fire, Hazmat, Rescue, Ambulance, and Command vehicles based on readiness, distance, and quotas. |
| **6** | **Medical Response** | `agents/medical_response.py` | Triages casualties across regional hospitals without exceeding emergency and ICU bed capacities. |
| **7** | **Route & Logistics** | `agents/route_logistics.py` | NetworkX road graph routing; calculates safest ingress and egress paths while bypassing blocked roads and plume zones. |
| **8** | **Evacuation & Shelter** | `agents/evacuation_shelter.py` | Categorizes RED/ORANGE/GREEN evacuation zones and assigns evacuees to shelters with positive remaining capacity. |
| **9** | **Communication** | `agents/communication.py` | Generates 8 role-specific broadcasts (Workers, Fire, Hazmat, Rescue, EMS, Hospitals, Public, Control Room). |
| **10**| **Command & Replanning** | `agents/command_replanning.py` | Central orchestrator coordinating all agents; performs dynamic replanning when secondary events or resource failures occur. |

---

## 📊 Datasets Utilized (`data/`)

1. `incidents.csv`: Historical and active industrial incident logs.
2. `emergency_incident_scenarios_5000.csv`: 5,000 synthetic crisis scenarios.
3. `chemical_spread_aloha_informed_synthetic.csv`: ALOHA chemical dispersion training records.
4. `resources.csv`: 600 emergency response assets with readiness and status.
5. `hospitals_500_final.csv`: 500 regional hospitals with emergency & ICU capacities.
6. `shelters (3).csv`: 600 emergency shelters with capacity, occupancy, and supplies.
7. `emergency_map_nodes_2000.csv`: 2,000 georeferenced road network intersections.
8. `emergency_map_roads_3800plus.csv`: 4,810 road segments with speed limits and lane counts.
9. `emergency_road_status_3000.csv`: Real-time road status observations (Open, Congested, Blocked).
10. `emergency_routing_training_data.csv`: Historical route delays, risk metrics, and costs.

---

## ⚡ Setup & Execution

### 1. Activate Environment & Install Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. (Optional) Retrain Spread Prediction Model
```powershell
python train_models/train_spread_model.py
```
*(Model is automatically pre-trained and saved in `models/spread_model.pkl`)*

### 3. Launch Backend Server
```powershell
python app.py
```

- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **OpenAPI JSON**: `http://127.0.0.1:8000/openapi.json`

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health status and safety disclaimer |
| `GET` | `/api/incidents` | List known and registered incidents |
| `POST` | `/api/incidents` | Register a new incident |
| `GET` | `/api/incidents/{id}` | Retrieve incident state by ID |
| `POST` | `/api/incidents/{id}/respond` | **Main Response**: Runs all 10 agents and returns unified response plan |
| `POST` | `/api/incidents/{id}/replan` | **Dynamic Replanning**: Re-runs affected agents upon new explosions, failures, or blocks |
| `GET` | `/api/resources` | Query emergency resources with filters |
| `GET` | `/api/hospitals` | Query regional hospitals and bed capacities |
| `GET` | `/api/shelters` | Query shelters and available capacities |
| `GET` | `/api/routes` | Query safest NetworkX path between two nodes |

---

## 🔄 Dynamic Replanning Example

When a secondary event happens (e.g. secondary explosion, Hazmat suit failure, or road obstruction):
```bash
POST /api/incidents/I001/replan
Content-Type: application/json

{
  "new_events": ["Secondary explosion at solvent storage tank"],
  "unavailable_resources": ["R0002"],
  "newly_blocked_roads": ["R00001"],
  "escalate_severity": true
}
```
The Command Agent will:
1. Detect changes.
2. Escalate severity and casualty projections.
3. Substitute failed resource `R0002` with next-best available unit.
4. Reroute logistics around blocked road `R00001`.
5. Update hospital victim allotments and shelter zoning.
6. Re-issue revised communication directives with human approval gate.
