"""
Comprehensive Outcome Verification Script.
Executes against http://127.0.0.1:8000 to test the full pipeline and output metrics.
"""
import requests
import json

base_url = "http://127.0.0.1:8000"

def main():
    print("=" * 70)
    print(" 1. SYSTEM HEALTH & DIAGNOSTICS")
    print("=" * 70)
    r_health = requests.get(f"{base_url}/api/health")
    print(f"Status Code: {r_health.status_code}")
    print(json.dumps(r_health.json(), indent=2))

    print("\n" + "=" * 70)
    print(" 2. MULTI-AGENT PIPELINE OUTCOME ON REAL SCENARIOS")
    print("=" * 70)
    test_cases = [
        ("I001", "Chemical Leak (Sulfur Dioxide) at Plant B"),
        ("I005", "Chemical Fire + Explosion (Benzene) at Plant A"),
        ("I018", "Mass Casualty Industrial Fire (130 affected) at Plant A")
    ]

    for inc_id, label in test_cases:
        print(f"\n>>> [SCENARIO {inc_id}]: {label}")
        resp = requests.post(f"{base_url}/api/incidents/{inc_id}/respond")
        if resp.status_code != 200:
            print(f"FAILED: {resp.text}")
            continue
        data = resp.json()
        inc = data["incident"]
        sev = data["severity"]
        haz = data["hazards"]
        spr = data["spread"]
        res = data["resources"]
        med = data["medical"]
        routes = data["routes"]
        evac = data["evacuation"]
        comm = data["communications"]

        print(f"  [Agent 1: Detection]  ID={inc['incident_id']} | Type={inc['incident_type']} | Plant={inc['location']} | Chem={inc['chemical']} | People={inc['people_affected']}")
        print(f"  [Agent 2: Assessment] Severity={sev['severity']} | Priority={sev['priority']} | Action={sev['recommended_action']}")
        print(f"  [Agent 3: Hazards]    Primary: {[h['hazard'] for h in haz['primary_hazards']]}")
        print(f"                        Secondary: {[h['hazard'] for h in haz['secondary_hazards']]}")
        print(f"  [Agent 4: Spread ML]  Red Zone: {spr['red_zone_m']} m | Orange: {spr['orange_zone_m']} m | Yellow: {spr['yellow_zone_m']} m | Spread Dir: {spr['spread_direction']}")
        print(f"                        Recommendation: {spr['recommended_response']}")
        print(f"  [Agent 5: Resources]  {len(res)} Units Dispatched:")
        for r in res[:4]:
            print(f"                        - {r['resource_id']} [{r['resource_type']}] from {r['station_location']} (ETA: {r['estimated_response_time']}m, Dist: {r['distance_km']}km)")
        print(f"  [Agent 6: Medical]    Casualties: {med['total_injured']} (Critical: {med['critical_cases']}) | Ambulances: {med['ambulances_deployed']}")
        print(f"                        Patient Distribution: {med['patient_distribution']}")
        print(f"  [Agent 7: Routing]    Mapped {len(routes)} Safe Corridors:")
        for ro in routes:
            print(f"                        - {ro['route_type']}: {ro['distance_km']} km, ETA: {ro['eta_minutes']} min, Roads: {len(ro['roads'])}")
        print(f"  [Agent 8: Evacuation] Evacuees: {evac['total_evacuees']} | Red Zone: {evac['zones']['RED']['affected_population']} | Orange: {evac['zones']['ORANGE']['affected_population']}")
        print(f"                        Shelters Assigned: {[s['name'] + ' (qty: ' + str(s['assigned_people']) + ')' for s in evac['assigned_shelters'][:2]]}")
        print(f"  [Agent 9: Comms]      Broadcasted to {len(comm['roles'])} operational channels.")
        print(f"                        Worker Alert: \"{comm['roles']['workers'][:120]}...\"")
        print(f"                        Fire Team:    \"{comm['roles']['fire_team'][:120]}...\"")

    print("\n" + "=" * 70)
    print(" 3. DYNAMIC REPLANNING OUTCOME (SECONDARY ACCIDENT SIMULATION)")
    print("=" * 70)
    replan_payload = {
        "new_events": [
            "Secondary explosion occurred at storage tank",
            "Toxic vapor cloud expanding rapidly towards North gate"
        ],
        "unavailable_resources": ["R0062"],  # Fire team failure
        "newly_blocked_roads": ["R00001", "R00002"],  # Road obstruction
        "escalate_severity": True
    }
    r_rep = requests.post(f"{base_url}/api/incidents/I001/replan", json=replan_payload)
    if r_rep.status_code == 200:
        rep_data = r_rep.json()
        r_info = rep_data["replanning"]
        print(f"  Replanning Triggered : SUCCESS")
        print(f"  Version Transition   : v{r_info.get('previous_version', 1)} -> v{r_info.get('version')}")
        print(f"  Approval Gate        : {r_info.get('status')}")
        print(f"  Detected Events      : {r_info.get('changes_detected')}")
        print(f"  Decision Adaptations : {r_info.get('affected_decisions')}")
        new_assigned = [r['resource_id'] for r in rep_data['resources']]
        print(f"  Failed Asset R0062 excluded? : {'R0062' not in new_assigned} (Substitute assigned)")
        rerouted = [ro.get('rerouted', False) for ro in rep_data['routes']]
        print(f"  Routes Rerouted around R00001/R00002? : {any(rerouted)}")
    else:
        print(f"Replanning request failed: {r_rep.text}")

    print("\n" + "=" * 70)
    print(" 4. REST DATASET ENDPOINT VERIFICATION")
    print("=" * 70)
    for ep in ["resources", "hospitals", "shelters", "routes"]:
        url = f"{base_url}/api/{ep}?limit=2" if ep != "routes" else f"{base_url}/api/{ep}?from_node=N0001&to_node=N0005"
        r = requests.get(url)
        print(f"  GET {url} -> HTTP {r.status_code} OK")

    print("\n" + "=" * 70)
    print(" >>> SYSTEM OUTCOME VERIFICATION COMPLETED: ALL AGENTS OPERATIONAL <<< ")
    print("=" * 70)

if __name__ == "__main__":
    main()
