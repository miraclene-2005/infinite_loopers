"""
Central data loading layer for the Industrial Crisis Management System.
Safely loads and caches all 10 CSV datasets, handling paths, missing values, and type casting.
"""
import os
from pathlib import Path
from typing import Dict, Optional, Any
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

class DataLoader:
    _instance: Optional["DataLoader"] = None
    _cache: Dict[str, pd.DataFrame] = {}

    def __new__(cls, data_dir: Optional[Path] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.data_dir = Path(data_dir) if data_dir else DATA_DIR
            cls._instance._load_all()
        return cls._instance

    def _resolve_file(self, filename: str) -> Path:
        p = self.data_dir / filename
        if p.exists():
            return p
        # Check if alternative filename exists
        candidates = list(self.data_dir.glob(f"*{filename.split('.')[0]}*.csv"))
        if candidates:
            return candidates[0]
        raise FileNotFoundError(f"Dataset {filename} not found in {self.data_dir}")

    def _load_all(self):
        """Loads and sanitizes all datasets into cache."""
        # 1. Incidents
        p_inc = self._resolve_file("incidents.csv")
        df_inc = pd.read_csv(p_inc)
        df_inc["incident_id"] = df_inc["incident_id"].astype(str).str.strip()
        df_inc["chemical"] = df_inc["chemical"].fillna("Unknown").astype(str).str.strip()
        df_inc["type"] = df_inc["type"].fillna("General_Incident").astype(str).str.strip()
        df_inc["plant"] = df_inc["plant"].fillna("Unknown_Plant").astype(str).str.strip()
        self._cache["incidents"] = df_inc

        # 2. Emergency Incident Scenarios (5000)
        p_scen = self._resolve_file("emergency_incident_scenarios_5000.csv")
        df_scen = pd.read_csv(p_scen)
        df_scen["incident_id"] = df_scen["incident_id"].astype(str).str.strip()
        self._cache["scenarios"] = df_scen

        # 3. Chemical spread
        p_chem = self._resolve_file("chemical_spread_aloha_informed_synthetic.csv")
        df_chem = pd.read_csv(p_chem)
        self._cache["chemical_spread"] = df_chem

        # 4. Resources
        p_res = self._resolve_file("resources.csv")
        df_res = pd.read_csv(p_res)
        df_res["resource_id"] = df_res["resource_id"].astype(str).str.strip()
        df_res["status"] = df_res["status"].fillna("Available").astype(str).str.strip()
        df_res["type"] = df_res["type"].fillna("General").astype(str).str.strip()
        df_res["fuel_level_pct"] = df_res["fuel_level_pct"].fillna(50.0)
        df_res["battery_level_pct"] = df_res["battery_level_pct"].fillna(50.0)
        df_res["assigned_incident"] = df_res["assigned_incident"].fillna("None")
        df_res["utilization"] = df_res["utilization"].fillna(0.0)
        self._cache["resources"] = df_res

        # 5. Hospitals
        p_hosp = self._resolve_file("hospitals_500_final.csv")
        df_hosp = pd.read_csv(p_hosp)
        df_hosp["hospital_id"] = df_hosp["hospital_id"].astype(str).str.strip()
        df_hosp["status"] = df_hosp["status"].fillna("Available").astype(str).str.strip()
        df_hosp["emergency_capacity"] = df_hosp["emergency_capacity"].clip(lower=0)
        self._cache["hospitals"] = df_hosp

        # 6. Shelters (handling "shelters (3).csv")
        try:
            p_shelter = self._resolve_file("shelters (3).csv")
        except FileNotFoundError:
            p_shelter = self._resolve_file("shelters.csv")
        df_shelter = pd.read_csv(p_shelter)
        df_shelter["shelter_id"] = df_shelter["shelter_id"].astype(str).str.strip()
        df_shelter["capacity"] = df_shelter["capacity"].clip(lower=0)
        df_shelter["current_occupancy"] = df_shelter["current_occupancy"].clip(lower=0)
        df_shelter["status"] = df_shelter["status"].fillna("Available").astype(str).str.strip()
        self._cache["shelters"] = df_shelter

        # 7. Map nodes
        p_nodes = self._resolve_file("emergency_map_nodes_2000.csv")
        df_nodes = pd.read_csv(p_nodes)
        df_nodes["node_id"] = df_nodes["node_id"].astype(str).str.strip()
        self._cache["nodes"] = df_nodes

        # 8. Map roads
        p_roads = self._resolve_file("emergency_map_roads_3800plus.csv")
        df_roads = pd.read_csv(p_roads)
        df_roads["road_id"] = df_roads["road_id"].astype(str).str.strip()
        df_roads["from_node"] = df_roads["from_node"].astype(str).str.strip()
        df_roads["to_node"] = df_roads["to_node"].astype(str).str.strip()
        self._cache["roads"] = df_roads

        # 9. Road status
        p_status = self._resolve_file("emergency_road_status_3000.csv")
        df_status = pd.read_csv(p_status)
        df_status["road_id"] = df_status["road_id"].astype(str).str.strip()
        self._cache["road_status"] = df_status

        # 10. Routing training data
        p_routing = self._resolve_file("emergency_routing_training_data.csv")
        df_routing = pd.read_csv(p_routing)
        df_routing["road_id"] = df_routing["road_id"].astype(str).str.strip()
        self._cache["routing_training"] = df_routing

    def get_incidents(self) -> pd.DataFrame:
        return self._cache["incidents"].copy()

    def get_scenarios(self) -> pd.DataFrame:
        return self._cache["scenarios"].copy()

    def get_chemical_spread(self) -> pd.DataFrame:
        return self._cache["chemical_spread"].copy()

    def get_resources(self) -> pd.DataFrame:
        return self._cache["resources"].copy()

    def get_hospitals(self) -> pd.DataFrame:
        return self._cache["hospitals"].copy()

    def get_shelters(self) -> pd.DataFrame:
        return self._cache["shelters"].copy()

    def get_nodes(self) -> pd.DataFrame:
        return self._cache["nodes"].copy()

    def get_roads(self) -> pd.DataFrame:
        return self._cache["roads"].copy()

    def get_road_status(self) -> pd.DataFrame:
        return self._cache["road_status"].copy()

    def get_routing_training(self) -> pd.DataFrame:
        return self._cache["routing_training"].copy()

    def reload(self):
        self._load_all()


data_loader = DataLoader()
