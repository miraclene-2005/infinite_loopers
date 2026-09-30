"""
Single place where the frontend talks to the FastAPI backend.
Pages never touch the database; they only call functions in this file.

If the backend is unreachable (and ALLOW_MOCK_FALLBACK is on), the call is
served by services/mock_data.py and the sidebar shows "Mock data".
"""
import time

import requests
import streamlit as st

import config
from services.mock_data import get_mock_backend


# ----------------------------------------------------------------- transport
def _request(method, path, payload=None):
    """Return parsed JSON from the backend, or None if we should fall back to mock."""
    if time.time() < st.session_state.get("_backend_down_until", 0):
        st.session_state["data_source"] = "mock"
        return None
    try:
        resp = requests.request(method, f"{config.BASE_URL}{path}", json=payload,
                                timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        st.session_state["data_source"] = "live"
        return resp.json()
    except requests.HTTPError as exc:
        # Backend is up but this endpoint failed or isn't built yet.
        if not config.ALLOW_MOCK_FALLBACK:
            raise
        st.session_state["data_source"] = "partial"
        st.session_state["last_api_error"] = f"{method} {path}: {exc}"
        return None
    except requests.RequestException as exc:
        # Backend not reachable at all.
        if not config.ALLOW_MOCK_FALLBACK:
            raise ConnectionError(f"Backend unreachable at {config.BASE_URL}") from exc
        st.session_state["data_source"] = "mock"
        st.session_state["last_api_error"] = f"Cannot reach {config.BASE_URL}"
        st.session_state["_backend_down_until"] = time.time() + config.RETRY_BACKEND_AFTER_SEC
        return None


def _call(method, path, mock_fn, payload=None):
    data = _request(method, path, payload)
    return data if data is not None else mock_fn()


def data_source():
    return st.session_state.get("data_source", "unknown")


def retry_backend_now():
    st.session_state.pop("_backend_down_until", None)


def reset_demo():
    get_mock_backend().reset()


# --------------------------------------------------------------- endpoints
def get_incidents():
    return _call("GET", "/incidents", get_mock_backend().get_incidents)


def create_incident(payload):
    return _call("POST", "/incidents", lambda: get_mock_backend().create_incident(payload), payload)


def get_resources():
    return _call("GET", "/resources", get_mock_backend().get_resources)


def get_hospitals():
    return _call("GET", "/hospitals", get_mock_backend().get_hospitals)


def get_routes():
    return _call("GET", "/routes", get_mock_backend().get_routes)


def get_evacuation(incident_id):
    return _call("GET", f"/evacuation/{incident_id}",
                 lambda: get_mock_backend().get_evacuation(incident_id))


def get_alerts(incident_id):
    return _call("GET", f"/alerts/{incident_id}",
                 lambda: get_mock_backend().get_alerts(incident_id))


def get_response_plan(incident_id):
    return _call("GET", f"/response-plan/{incident_id}",
                 lambda: get_mock_backend().get_response_plan(incident_id))


def trigger_replan(incident_id, event):
    payload = {"incident_id": incident_id, "event": event}
    return _call("POST", "/replan", lambda: get_mock_backend().replan(incident_id, event), payload)


def approve_plan(incident_id, operator="Control room operator"):
    return _call("POST", f"/response-plan/{incident_id}/approve",
                 lambda: get_mock_backend().approve_plan(incident_id, operator),
                 {"operator": operator})