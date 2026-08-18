"""
COLEXA BIOSENSOR - HVAC Monitoring Platform
Supabase CRUD Operations Handler.

All database interactions use the Supabase client API. Every public function
wraps execution in try/except so network or database faults never crash the Streamlit UI.
"""

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from database.schema import get_supabase_client, _log_exception


# ---------------------------------------------------------------------------
# Audit trail helper
# ---------------------------------------------------------------------------

def write_audit_entry(
    username: str, 
    action: str, 
    table_name: str, 
    record_id: int = 0, 
    detail: str = ""
) -> None:
    """Inserts a record into the audit_trail table for FDA 21 CFR Part 11 compliance."""
    try:
        client = get_supabase_client()
        client.table("audit_trail").insert({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "username": username,
            "action": action,
            "table_name": table_name,
            "record_id": record_id,
            "detail": detail,
        }).execute()
    except Exception as exc:
        _log_exception("write_audit_entry", exc)


# ---------------------------------------------------------------------------
# Audit trail fetcher
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def fetch_audit_trail(limit: int = 1000) -> pd.DataFrame:
    """Retrieve the immutable audit trail, most recent first."""
    try:
        client = get_supabase_client()
        response = client.table("audit_trail").select("*").order("id", desc=True).limit(limit).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as exc:
        _log_exception("fetch_audit_trail", exc)
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Facility shift log (mirrors the paper HVAC Monitoring Log)
# ---------------------------------------------------------------------------

def insert_facility_log(entry: dict[str, Any]) -> int | None:
    """Insert one shift telemetry row into facility_logs."""
    try:
        client = get_supabase_client()
        
        shift_date = entry.get("shift_date")
        if not shift_date:
            shift_date = datetime.now().strftime("%Y-%m-%d")

        payload = {
            "timestamp": entry.get("timestamp", datetime.now().isoformat(timespec="seconds")),
            "shift_date": shift_date,
            "shift_time": entry.get("shift_time", datetime.now().strftime("%H:%M")),
            "ahu_temperature": entry.get("ahu_temperature"),
            "ahu_rh": entry.get("ahu_rh"),
            "dhu1_rh": entry.get("dhu1_rh"),
            "dhu1_dpg": entry.get("dhu1_dpg"),
            "dhu2_rh": entry.get("dhu2_rh"),
            "dhu2_dpg": entry.get("dhu2_dpg"),
            "ac_temp_1": entry.get("ac_temp_1"),
            "ac_temp_2": entry.get("ac_temp_2"),
            "ac_temp_3": entry.get("ac_temp_3"),
            "compressor_pressure": entry.get("compressor_pressure"),
            "remarks": entry.get("remarks", ""),
            "operator_id": entry.get("operator_id", "unknown"),
            "checked_by": entry.get("checked_by", ""),
            "verified_by": entry.get("verified_by", ""),
            "status": entry.get("status", "Nominal"),
        }

        response = client.table("facility_logs").insert(payload).execute()
        if response.data:
            new_id = response.data[0]["id"]
            write_audit_entry(entry.get("operator_id", "unknown"), "INSERT", "facility_logs", new_id, "Shift telemetry recorded")
            _clear_streamlit_cache()
            return new_id
        return None
    except Exception as exc:
        _log_exception("insert_facility_log", exc)
        return None


@st.cache_data(ttl=60)
def fetch_facility_logs(limit: int = 500) -> pd.DataFrame:
    """Retrieve the most recent facility_logs rows as a DataFrame."""
    try:
        client = get_supabase_client()
        response = client.table("facility_logs").select("*").order("id", desc=True).limit(limit).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as exc:
        _log_exception("fetch_facility_logs", exc)
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Deviation / CAPA log
# ---------------------------------------------------------------------------

def insert_deviation(entry: dict[str, Any]) -> int | None:
    """Insert a deviation/CAPA event."""
    try:
        client = get_supabase_client()
        payload = {
            "timestamp": entry.get("timestamp", datetime.now().isoformat(timespec="seconds")),
            "equipment": entry.get("equipment"),
            "parameter": entry.get("parameter"),
            "observed_value": entry.get("observed_value"),
            "lower_limit": entry.get("lower_limit"),
            "upper_limit": entry.get("upper_limit"),
            "severity": entry.get("severity", "Minor"),
            "probable_causes": entry.get("probable_causes", ""),
            "recommended_capa": entry.get("recommended_capa", ""),
            "referenced_sop": entry.get("referenced_sop", ""),
            "capa_status": entry.get("capa_status", "Open"),
            "operator_id": entry.get("operator_id", "unknown"),
        }

        response = client.table("deviation_logs").insert(payload).execute()
        if response.data:
            new_id = response.data[0]["id"]
            write_audit_entry(entry.get("operator_id", "unknown"), "INSERT", "deviation_logs", new_id, f"Deviation logged: {entry.get('parameter')}")
            _clear_streamlit_cache()
            return new_id
        return None
    except Exception as exc:
        _log_exception("insert_deviation", exc)
        return None


@st.cache_data(ttl=60)
def fetch_deviations(limit: int = 500, status_filter: str | None = None) -> pd.DataFrame:
    """Retrieve deviation_logs rows, optionally filtered by CAPA status."""
    try:
        client = get_supabase_client()
        query = client.table("deviation_logs").select("*")
        if status_filter:
            query = query.eq("capa_status", status_filter)
        response = query.order("id", desc=True).limit(limit).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as exc:
        _log_exception("fetch_deviations", exc)
        return pd.DataFrame()


def update_capa_status(deviation_id: int, new_status: str, username: str) -> bool:
    """Update the CAPA status of a deviation record."""
    try:
        client = get_supabase_client()
        client.table("deviation_logs").update({"capa_status": new_status}).eq("id", deviation_id).execute()
        write_audit_entry(username, "UPDATE", "deviation_logs", deviation_id, f"CAPA status changed to {new_status}")
        _clear_streamlit_cache()
        return True
    except Exception as exc:
        _log_exception("update_capa_status", exc)
        return False


# ---------------------------------------------------------------------------
# Detailed module logs (AHU / DHU / Compressor)
# ---------------------------------------------------------------------------

def insert_ahu_detail(entry: dict[str, Any]) -> int | None:
    """Insert a detailed AHU telemetry record."""
    try:
        client = get_supabase_client()
        payload = {
            "facility_log_id": entry.get("facility_log_id"),
            "timestamp": entry.get("timestamp", datetime.now().isoformat(timespec="seconds")),
            "unit_id": entry.get("unit_id", "AHU-01"),
            "supply_temp": entry.get("supply_temp"),
            "return_temp": entry.get("return_temp"),
            "relative_humidity": entry.get("relative_humidity"),
            "differential_pressure": entry.get("differential_pressure"),
            "fan_speed": entry.get("fan_speed"),
            "motor_current": entry.get("motor_current"),
            "filter_delta_p": entry.get("filter_delta_p"),
            "damper_position": entry.get("damper_position"),
            "operator_id": entry.get("operator_id", "unknown"),
        }
        response = client.table("ahu_detailed_logs").insert(payload).execute()
        _clear_streamlit_cache()
        return response.data[0]["id"] if response.data else None
    except Exception as exc:
        _log_exception("insert_ahu_detail", exc)
        return None


@st.cache_data(ttl=60)
def fetch_ahu_details(limit: int = 500) -> pd.DataFrame:
    """Retrieve recent AHU detailed telemetry."""
    return _fetch_table("ahu_detailed_logs", limit)


def insert_dhu_detail(entry: dict[str, Any]) -> int | None:
    """Insert a detailed DHU telemetry record."""
    try:
        client = get_supabase_client()
        payload = {
            "facility_log_id": entry.get("facility_log_id"),
            "timestamp": entry.get("timestamp", datetime.now().isoformat(timespec="seconds")),
            "unit_id": entry.get("unit_id", "DHU-01"),
            "relative_humidity": entry.get("relative_humidity"),
            "dpg_mmwc": entry.get("dpg_mmwc"),
            "dew_point": entry.get("dew_point"),
            "air_flow_rate": entry.get("air_flow_rate"),
            "desiccant_wheel_efficiency": entry.get("desiccant_wheel_efficiency"),
            "regeneration_temp": entry.get("regeneration_temp"),
            "operator_id": entry.get("operator_id", "unknown"),
        }
        response = client.table("dhu_detailed_logs").insert(payload).execute()
        _clear_streamlit_cache()
        return response.data[0]["id"] if response.data else None
    except Exception as exc:
        _log_exception("insert_dhu_detail", exc)
        return None


@st.cache_data(ttl=60)
def fetch_dhu_details(limit: int = 500) -> pd.DataFrame:
    """Retrieve recent DHU detailed telemetry."""
    return _fetch_table("dhu_detailed_logs", limit)


def insert_compressor_log(entry: dict[str, Any]) -> int | None:
    """Insert an air compressor telemetry record."""
    try:
        client = get_supabase_client()
        payload = {
            "facility_log_id": entry.get("facility_log_id"),
            "timestamp": entry.get("timestamp", datetime.now().isoformat(timespec="seconds")),
            "delivery_pressure": entry.get("delivery_pressure"),
            "discharge_temp": entry.get("discharge_temp"),
            "runtime_hours": entry.get("runtime_hours"),
            "oil_differential": entry.get("oil_differential"),
            "dew_point": entry.get("dew_point"),
            "operator_id": entry.get("operator_id", "unknown"),
        }
        response = client.table("compressor_logs").insert(payload).execute()
        _clear_streamlit_cache()
        return response.data[0]["id"] if response.data else None
    except Exception as exc:
        _log_exception("insert_compressor_log", exc)
        return None


@st.cache_data(ttl=60)
def fetch_compressor_logs(limit: int = 500) -> pd.DataFrame:
    """Retrieve recent air compressor telemetry."""
    return _fetch_table("compressor_logs", limit)


@st.cache_data(ttl=60)
def _fetch_table(table_name: str, limit: int) -> pd.DataFrame:
    """Shared helper to safely SELECT * from a known, hardcoded table name."""
    allowed_tables: set[str] = {
        "ahu_detailed_logs", "dhu_detailed_logs", "compressor_logs",
        "panel_logs", "audit_trail",
    }
    if table_name not in allowed_tables:
        return pd.DataFrame()

    try:
        client = get_supabase_client()
        response = client.table(table_name).select("*").order("id", desc=True).limit(limit).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as exc:
        _log_exception(f"_fetch_table:{table_name}", exc)
        return pd.DataFrame()


@st.cache_data(ttl=60)
def compute_kpis() -> dict[str, Any]:
    """Compute headline KPIs for the executive dashboard."""
    try:
        client = get_supabase_client()
        
        total_logs_res = client.table("facility_logs").select("id", count="exact").execute()
        total_logs = total_logs_res.count if total_logs_res.count is not None else len(total_logs_res.data)

        open_dev_res = client.table("deviation_logs").select("id", count="exact").neq("capa_status", "Closed").execute()
        open_deviations = open_dev_res.count if open_dev_res.count is not None else len(open_dev_res.data)

        total_dev_res = client.table("deviation_logs").select("id", count="exact").execute()
        total_deviations = total_dev_res.count if total_dev_res.count is not None else len(total_dev_res.data)

        today_str = datetime.now().strftime("%Y-%m-%d")
        today_log_res = client.table("facility_logs").select("id", count="exact").eq("shift_date", today_str).execute()
        today_log_count = today_log_res.count if today_log_res.count is not None else len(today_log_res.data)

        compliance_pct = 100.0
        if total_logs > 0:
            compliance_pct = round(100.0 * (1 - (total_deviations / max(total_logs, 1))), 1)
            compliance_pct = max(0.0, min(100.0, compliance_pct))

        equipment_health_score = round(max(0.0, 100.0 - (open_deviations * 7.5)), 1)

        return {
            "total_logs": total_logs,
            "open_deviations": open_deviations,
            "compliance_pct": compliance_pct,
            "today_log_count": today_log_count,
            "equipment_health_score": equipment_health_score,
        }
    except Exception as exc:
        _log_exception("compute_kpis", exc)
        return {
            "total_logs": 0,
            "open_deviations": 0,
            "compliance_pct": 100.0,
            "today_log_count": 0,
            "equipment_health_score": 100.0,
        }


# ---------------------------------------------------------------------------
# Selective & Full Data Deletion Utilities
# ---------------------------------------------------------------------------

def delete_telemetry_by_date_range(
    start_date: str, 
    end_date: str, 
    tables: list[str] | None = None, 
    username: str = "Admin"
) -> tuple[bool, int]:
    """Deletes records across specified telemetry tables within a date range [start_date, end_date]."""
    allowed_tables = {
        "facility_logs", "deviation_logs", "ahu_detailed_logs", 
        "dhu_detailed_logs", "compressor_logs", "panel_logs"
    }
    
    target_tables = [t for t in (tables or list(allowed_tables)) if t in allowed_tables]
    if not target_tables:
        return False, 0

    total_deleted = 0
    try:
        client = get_supabase_client()
        for table in target_tables:
            if table == "facility_logs":
                response = client.table(table).delete().gte("shift_date", start_date).lte("shift_date", end_date).execute()
            else:
                response = client.table(table).delete().gte("timestamp", f"{start_date}T00:00:00").lte("timestamp", f"{end_date}T23:59:59").execute()
            
            if response.data:
                total_deleted += len(response.data)
            
        write_audit_entry(
            username=username,
            action="DELETE_RANGE",
            table_name=", ".join(target_tables),
            record_id=0,
            detail=f"Deleted records between {start_date} and {end_date}"
        )
        
        _clear_streamlit_cache()
        return True, total_deleted
    except Exception as exc:
        _log_exception("delete_telemetry_by_date_range", exc)
        return False, 0


def delete_record_by_id(table_name: str, record_id: int, username: str = "Admin") -> bool:
    """Deletes a single record by primary key ID from an allowed table."""
    allowed_tables = {
        "facility_logs", "deviation_logs", "ahu_detailed_logs", 
        "dhu_detailed_logs", "compressor_logs", "panel_logs"
    }
    if table_name not in allowed_tables:
        return False

    try:
        client = get_supabase_client()
        response = client.table(table_name).delete().eq("id", record_id).execute()
        
        if response.data:
            write_audit_entry(
                username=username,
                action="DELETE_RECORD",
                table_name=table_name,
                record_id=record_id,
                detail=f"Record #{record_id} manually purged"
            )
            _clear_streamlit_cache()
            return True
        return False
    except Exception as exc:
        _log_exception("delete_record_by_id", exc)
        return False


def reset_all_telemetry_data(username: str = "Admin") -> bool:
    """Wipes all telemetry data from the database (Development/Admin use)."""
    try:
        client = get_supabase_client()
        tables = [
            "facility_logs", "deviation_logs", "ahu_detailed_logs", 
            "dhu_detailed_logs", "compressor_logs", "panel_logs", "audit_trail"
        ]
        
        for table in tables:
            # Supabase delete requires a filter condition, so we match id greater than 0
            client.table(table).delete().gt("id", 0).execute()
            
        write_audit_entry(
            username=username,
            action="FULL_RESET",
            table_name="ALL",
            record_id=0,
            detail="Entire telemetry database reset"
        )

        _clear_streamlit_cache()
        return True
    except Exception as exc:
        _log_exception("reset_all_telemetry_data", exc)
        return False


def _clear_streamlit_cache() -> None:
    """Safely clears Streamlit cache if running within Streamlit context."""
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
    except Exception:
        pass
