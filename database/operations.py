"""
COLEXA BIOSENSOR - HVAC Monitoring Platform
Isolated database query execution handlers (CRUD).

All queries use parameterized (?) placeholders. Every public function
wraps its connection lifecycle in try/except/finally so a database fault
never crashes the Streamlit UI.
"""

import sqlite3
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from database.schema import get_connection, _log_exception


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def fetch_audit_trail(limit: int = 1000) -> pd.DataFrame:
    """Retrieve the immutable audit trail, most recent first."""
    return _fetch_table("audit_trail", limit)


# ---------------------------------------------------------------------------
# Facility shift log (mirrors the paper HVAC Monitoring Log)
# ---------------------------------------------------------------------------

def insert_facility_log(entry: dict[str, Any]) -> int | None:
    """Insert one shift telemetry row into facility_logs."""
    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        
        # Ensure shift_date defaults to today's date if omitted
        shift_date = entry.get("shift_date")
        if not shift_date:
            shift_date = datetime.now().strftime("%Y-%m-%d")

        cursor = connection.execute(
            """
            INSERT INTO facility_logs (
                timestamp, shift_date, shift_time, ahu_temperature, ahu_rh,
                dhu1_rh, dhu1_dpg, dhu2_rh, dhu2_dpg,
                ac_temp_1, ac_temp_2, ac_temp_3, compressor_pressure,
                remarks, operator_id, checked_by, verified_by, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.get("timestamp", datetime.now().isoformat(timespec="seconds")),
                shift_date,
                entry.get("shift_time", datetime.now().strftime("%H:%M")),
                entry.get("ahu_temperature"),
                entry.get("ahu_rh"),
                entry.get("dhu1_rh"),
                entry.get("dhu1_dpg"),
                entry.get("dhu2_rh"),
                entry.get("dhu2_dpg"),
                entry.get("ac_temp_1"),
                entry.get("ac_temp_2"),
                entry.get("ac_temp_3"),
                entry.get("compressor_pressure"),
                entry.get("remarks", ""),
                entry.get("operator_id", "unknown"),
                entry.get("checked_by", ""),
                entry.get("verified_by", ""),
                entry.get("status", "Nominal"),
            ),
        )
        connection.commit()
        new_id: int = cursor.lastrowid
        write_audit_entry(entry.get("operator_id", "unknown"), "INSERT", "facility_logs", new_id, "Shift telemetry recorded")
        _clear_streamlit_cache()
        return new_id
    except sqlite3.Error as exc:
        _log_exception("insert_facility_log", exc)
        return None
    finally:
        if connection is not None:
            connection.close()


@st.cache_data(ttl=60)
def fetch_facility_logs(limit: int = 500) -> pd.DataFrame:
    """Retrieve the most recent facility_logs rows as a DataFrame."""
    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        df: pd.DataFrame = pd.read_sql_query(
            "SELECT * FROM facility_logs ORDER BY id DESC LIMIT ?",
            connection,
            params=(limit,),
        )
        return df
    except sqlite3.Error as exc:
        _log_exception("fetch_facility_logs", exc)
        return pd.DataFrame()
    finally:
        if connection is not None:
            connection.close()


# ---------------------------------------------------------------------------
# Deviation / CAPA log
# ---------------------------------------------------------------------------

def insert_deviation(entry: dict[str, Any]) -> int | None:
    """Insert a deviation/CAPA event."""
    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        cursor = connection.execute(
            """
            INSERT INTO deviation_logs (
                timestamp, equipment, parameter, observed_value, lower_limit,
                upper_limit, severity, probable_causes, recommended_capa,
                referenced_sop, capa_status, operator_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.get("timestamp", datetime.now().isoformat(timespec="seconds")),
                entry.get("equipment"),
                entry.get("parameter"),
                entry.get("observed_value"),
                entry.get("lower_limit"),
                entry.get("upper_limit"),
                entry.get("severity", "Minor"),
                entry.get("probable_causes", ""),
                entry.get("recommended_capa", ""),
                entry.get("referenced_sop", ""),
                entry.get("capa_status", "Open"),
                entry.get("operator_id", "unknown"),
            ),
        )
        connection.commit()
        new_id: int = cursor.lastrowid
        write_audit_entry(entry.get("operator_id", "unknown"), "INSERT", "deviation_logs", new_id, f"Deviation logged: {entry.get('parameter')}")
        _clear_streamlit_cache()
        return new_id
    except sqlite3.Error as exc:
        _log_exception("insert_deviation", exc)
        return None
    finally:
        if connection is not None:
            connection.close()


@st.cache_data(ttl=60)
def fetch_deviations(limit: int = 500, status_filter: str | None = None) -> pd.DataFrame:
    """Retrieve deviation_logs rows, optionally filtered by CAPA status."""
    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        if status_filter:
            df: pd.DataFrame = pd.read_sql_query(
                "SELECT * FROM deviation_logs WHERE capa_status = ? ORDER BY id DESC LIMIT ?",
                connection,
                params=(status_filter, limit),
            )
        else:
            df = pd.read_sql_query(
                "SELECT * FROM deviation_logs ORDER BY id DESC LIMIT ?",
                connection,
                params=(limit,),
            )
        return df
    except sqlite3.Error as exc:
        _log_exception("fetch_deviations", exc)
        return pd.DataFrame()
    finally:
        if connection is not None:
            connection.close()


def update_capa_status(deviation_id: int, new_status: str, username: str) -> bool:
    """Update the CAPA status of a deviation record."""
    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        connection.execute(
            "UPDATE deviation_logs SET capa_status = ? WHERE id = ?",
            (new_status, deviation_id),
        )
        connection.commit()
        write_audit_entry(username, "UPDATE", "deviation_logs", deviation_id, f"CAPA status changed to {new_status}")
        _clear_streamlit_cache()
        return True
    except sqlite3.Error as exc:
        _log_exception("update_capa_status", exc)
        return False
    finally:
        if connection is not None:
            connection.close()


# ---------------------------------------------------------------------------
# Detailed module logs (AHU / DHU / Compressor)
# ---------------------------------------------------------------------------

def insert_ahu_detail(entry: dict[str, Any]) -> int | None:
    """Insert a detailed AHU telemetry record."""
    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        cursor = connection.execute(
            """
            INSERT INTO ahu_detailed_logs (
                facility_log_id, timestamp, unit_id, supply_temp, return_temp,
                relative_humidity, differential_pressure, fan_speed,
                motor_current, filter_delta_p, damper_position, operator_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.get("facility_log_id"),
                entry.get("timestamp", datetime.now().isoformat(timespec="seconds")),
                entry.get("unit_id", "AHU-01"),
                entry.get("supply_temp"),
                entry.get("return_temp"),
                entry.get("relative_humidity"),
                entry.get("differential_pressure"),
                entry.get("fan_speed"),
                entry.get("motor_current"),
                entry.get("filter_delta_p"),
                entry.get("damper_position"),
                entry.get("operator_id", "unknown"),
            ),
        )
        connection.commit()
        _clear_streamlit_cache()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        _log_exception("insert_ahu_detail", exc)
        return None
    finally:
        if connection is not None:
            connection.close()


@st.cache_data(ttl=60)
def fetch_ahu_details(limit: int = 500) -> pd.DataFrame:
    """Retrieve recent AHU detailed telemetry."""
    return _fetch_table("ahu_detailed_logs", limit)


def insert_dhu_detail(entry: dict[str, Any]) -> int | None:
    """Insert a detailed DHU telemetry record."""
    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        cursor = connection.execute(
            """
            INSERT INTO dhu_detailed_logs (
                facility_log_id, timestamp, unit_id, relative_humidity, dpg_mmwc,
                dew_point, air_flow_rate, desiccant_wheel_efficiency,
                regeneration_temp, operator_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.get("facility_log_id"),
                entry.get("timestamp", datetime.now().isoformat(timespec="seconds")),
                entry.get("unit_id", "DHU-01"),
                entry.get("relative_humidity"),
                entry.get("dpg_mmwc"),
                entry.get("dew_point"),
                entry.get("air_flow_rate"),
                entry.get("desiccant_wheel_efficiency"),
                entry.get("regeneration_temp"),
                entry.get("operator_id", "unknown"),
            ),
        )
        connection.commit()
        _clear_streamlit_cache()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        _log_exception("insert_dhu_detail", exc)
        return None
    finally:
        if connection is not None:
            connection.close()


@st.cache_data(ttl=60)
def fetch_dhu_details(limit: int = 500) -> pd.DataFrame:
    """Retrieve recent DHU detailed telemetry."""
    return _fetch_table("dhu_detailed_logs", limit)


def insert_compressor_log(entry: dict[str, Any]) -> int | None:
    """Insert an air compressor telemetry record."""
    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        cursor = connection.execute(
            """
            INSERT INTO compressor_logs (
                facility_log_id, timestamp, delivery_pressure, discharge_temp,
                runtime_hours, oil_differential, dew_point, operator_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.get("facility_log_id"),
                entry.get("timestamp", datetime.now().isoformat(timespec="seconds")),
                entry.get("delivery_pressure"),
                entry.get("discharge_temp"),
                entry.get("runtime_hours"),
                entry.get("oil_differential"),
                entry.get("dew_point"),
                entry.get("operator_id", "unknown"),
            ),
        )
        connection.commit()
        _clear_streamlit_cache()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        _log_exception("insert_compressor_log", exc)
        return None
    finally:
        if connection is not None:
            connection.close()


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

    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        query: str = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT ?"
        df: pd.DataFrame = pd.read_sql_query(query, connection, params=(limit,))
        return df
    except sqlite3.Error as exc:
        _log_exception(f"_fetch_table:{table_name}", exc)
        return pd.DataFrame()
    finally:
        if connection is not None:
            connection.close()


@st.cache_data(ttl=60)
def compute_kpis() -> dict[str, Any]:
    """Compute headline KPIs for the executive dashboard."""
    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        total_logs: int = connection.execute("SELECT COUNT(*) FROM facility_logs").fetchone()[0]
        open_deviations: int = connection.execute(
            "SELECT COUNT(*) FROM deviation_logs WHERE capa_status != 'Closed'"
        ).fetchone()[0]
        total_deviations: int = connection.execute("SELECT COUNT(*) FROM deviation_logs").fetchone()[0]
        today_str: str = datetime.now().strftime("%Y-%m-%d")
        today_log_count: int = connection.execute(
            "SELECT COUNT(*) FROM facility_logs WHERE shift_date = ?", (today_str,)
        ).fetchone()[0]

        compliance_pct: float = 100.0
        if total_logs > 0:
            compliance_pct = round(100.0 * (1 - (total_deviations / max(total_logs, 1))), 1)
            compliance_pct = max(0.0, min(100.0, compliance_pct))

        equipment_health_score: float = round(max(0.0, 100.0 - (open_deviations * 7.5)), 1)

        return {
            "total_logs": total_logs,
            "open_deviations": open_deviations,
            "compliance_pct": compliance_pct,
            "today_log_count": today_log_count,
            "equipment_health_score": equipment_health_score,
        }
    except sqlite3.Error as exc:
        _log_exception("compute_kpis", exc)
        return {
            "total_logs": 0,
            "open_deviations": 0,
            "compliance_pct": 100.0,
            "today_log_count": 0,
            "equipment_health_score": 100.0,
        }
    finally:
        if connection is not None:
            connection.close()


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
    connection: sqlite3.Connection | None = None
    allowed_tables = {
        "facility_logs", "deviation_logs", "ahu_detailed_logs", 
        "dhu_detailed_logs", "compressor_logs", "panel_logs"
    }
    
    target_tables = [t for t in (tables or list(allowed_tables)) if t in allowed_tables]
    if not target_tables:
        return False, 0

    total_deleted = 0
    try:
        connection = get_connection()
        for table in target_tables:
            table_check = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if not table_check:
                continue

            if table == "facility_logs":
                cursor = connection.execute(
                    f"DELETE FROM {table} WHERE shift_date >= ? AND shift_date <= ?",
                    (start_date, end_date)
                )
            else:
                cursor = connection.execute(
                    f"DELETE FROM {table} WHERE date(timestamp) >= date(?) AND date(timestamp) <= date(?)",
                    (start_date, end_date)
                )
            total_deleted += cursor.rowcount
            
        connection.commit()
        
        write_audit_entry(
            username=username,
            action="DELETE_RANGE",
            table_name=", ".join(target_tables),
            detail=f"Deleted {total_deleted} records between {start_date} and {end_date}"
        )
        
        _clear_streamlit_cache()
        return True, total_deleted
    except sqlite3.Error as exc:
        _log_exception("delete_telemetry_by_date_range", exc)
        return False, 0
    finally:
        if connection is not None:
            connection.close()


def delete_record_by_id(table_name: str, record_id: int, username: str = "Admin") -> bool:
    """Deletes a single record by primary key ID from an allowed table."""
    allowed_tables = {
        "facility_logs", "deviation_logs", "ahu_detailed_logs", 
        "dhu_detailed_logs", "compressor_logs", "panel_logs"
    }
    if table_name not in allowed_tables:
        return False

    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        cursor = connection.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
        connection.commit()
        
        if cursor.rowcount > 0:
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
    except sqlite3.Error as exc:
        _log_exception("delete_record_by_id", exc)
        return False
    finally:
        if connection is not None:
            connection.close()


def reset_all_telemetry_data(username: str = "Admin") -> bool:
    """Wipes all telemetry data from the database (Development/Admin use)."""
    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        tables = [
            "facility_logs", "deviation_logs", "ahu_detailed_logs", 
            "dhu_detailed_logs", "compressor_logs", "panel_logs", "audit_trail"
        ]
        
        for table in tables:
            connection.execute(f"DELETE FROM {table}")
            
        connection.commit()
        
        try:
            connection.isolation_level = None
            connection.execute("VACUUM")
        except sqlite3.Error:
            pass
        finally:
            connection.isolation_level = ""
        
        write_audit_entry(
            username=username,
            action="FULL_RESET",
            table_name="ALL",
            detail="Entire telemetry database reset"
        )

        _clear_streamlit_cache()
        return True
    except sqlite3.Error as exc:
        _log_exception("reset_all_telemetry_data", exc)
        return False
    finally:
        if connection is not None:
            connection.close()


def _clear_streamlit_cache() -> None:
    """Safely clears Streamlit cache if running within Streamlit context."""
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
    except Exception:
        pass