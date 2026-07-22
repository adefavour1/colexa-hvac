"""
COLEXA BIOSENSOR - HVAC Monitoring Platform
Database schema initialization module.

Creates and maintains the SQLite schema used across the application.
All statements are idempotent (CREATE TABLE IF NOT EXISTS) so this module
can be safely imported and executed on every application startup.
"""

import os
import sqlite3
from datetime import datetime

DB_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
DB_PATH: str = os.path.join(DB_DIR, "colexa_matrix.db")

LOG_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def _log_exception(context: str, exc: Exception) -> None:
    """Append a timestamped exception record to logs/db_errors.log.

    Args:
        context: Short description of where the exception occurred.
        exc: The caught exception instance.
    """
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_path: str = os.path.join(LOG_DIR, "db_errors.log")
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{datetime.now().isoformat()}] {context}: {exc}\n")
    except Exception:
        # Logging must never crash the application.
        pass


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with sane defaults for a desktop app.

    Returns:
        An sqlite3.Connection with foreign keys enabled and row factory set.

    Raises:
        sqlite3.Error: If the database file cannot be opened/created.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    connection: sqlite3.Connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA journal_mode = WAL;")
    return connection


SCHEMA_STATEMENTS: list[str] = [
    # 1. Master shift summary log - mirrors the physical "HVAC Monitoring Log" sheet
    """
    CREATE TABLE IF NOT EXISTS facility_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        shift_date TEXT NOT NULL,
        shift_time TEXT NOT NULL,
        ahu_temperature REAL,
        ahu_rh REAL,
        dhu1_rh REAL,
        dhu1_dpg REAL,
        dhu2_rh REAL,
        dhu2_dpg REAL,
        ac_temp_1 REAL,
        ac_temp_2 REAL,
        ac_temp_3 REAL,
        compressor_pressure REAL,
        remarks TEXT,
        operator_id TEXT NOT NULL,
        checked_by TEXT,
        verified_by TEXT,
        status TEXT NOT NULL DEFAULT 'Nominal'
    );
    """,
    # 2. AHU detailed breakdown (extended parameters beyond the paper log)
    """
    CREATE TABLE IF NOT EXISTS ahu_detailed_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facility_log_id INTEGER,
        timestamp TEXT NOT NULL,
        unit_id TEXT NOT NULL,
        supply_temp REAL,
        return_temp REAL,
        relative_humidity REAL,
        differential_pressure REAL,
        fan_speed REAL,
        motor_current REAL,
        filter_delta_p REAL,
        damper_position REAL,
        operator_id TEXT NOT NULL,
        FOREIGN KEY (facility_log_id) REFERENCES facility_logs (id)
    );
    """,
    # 3. DHU detailed breakdown
    """
    CREATE TABLE IF NOT EXISTS dhu_detailed_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facility_log_id INTEGER,
        timestamp TEXT NOT NULL,
        unit_id TEXT NOT NULL,
        relative_humidity REAL,
        dpg_mmwc REAL,
        dew_point REAL,
        air_flow_rate REAL,
        desiccant_wheel_efficiency REAL,
        regeneration_temp REAL,
        operator_id TEXT NOT NULL,
        FOREIGN KEY (facility_log_id) REFERENCES facility_logs (id)
    );
    """,
    # 4. Air Compressor logs
    """
    CREATE TABLE IF NOT EXISTS compressor_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facility_log_id INTEGER,
        timestamp TEXT NOT NULL,
        delivery_pressure REAL,
        discharge_temp REAL,
        runtime_hours REAL,
        oil_differential REAL,
        dew_point REAL,
        operator_id TEXT NOT NULL,
        FOREIGN KEY (facility_log_id) REFERENCES facility_logs (id)
    );
    """,
    # 5. Electrical / panel logs
    """
    CREATE TABLE IF NOT EXISTS panel_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        panel_name TEXT NOT NULL,
        voltage REAL,
        current REAL,
        power_factor REAL,
        operator_id TEXT NOT NULL
    );
    """,
    # 6. Deviation / CAPA event log
    """
    CREATE TABLE IF NOT EXISTS deviation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        equipment TEXT NOT NULL,
        parameter TEXT NOT NULL,
        observed_value REAL,
        lower_limit REAL,
        upper_limit REAL,
        severity TEXT NOT NULL,
        probable_causes TEXT,
        recommended_capa TEXT,
        referenced_sop TEXT,
        capa_status TEXT NOT NULL DEFAULT 'Open',
        operator_id TEXT NOT NULL
    );
    """,
    # 7. Immutable audit trail (21 CFR Part 11 baseline)
    """
    CREATE TABLE IF NOT EXISTS audit_trail (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        username TEXT NOT NULL,
        action TEXT NOT NULL,
        table_name TEXT,
        record_id INTEGER,
        detail TEXT
    );
    """,
]

INDEX_STATEMENTS: list[str] = [
    "CREATE INDEX IF NOT EXISTS idx_facility_logs_timestamp ON facility_logs (timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_deviation_logs_timestamp ON deviation_logs (timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_audit_trail_timestamp ON audit_trail (timestamp);",
]


def initialize_database() -> bool:
    """Create all required tables and indexes if they do not already exist.

    Returns:
        True if initialization succeeded, False otherwise.
    """
    connection: sqlite3.Connection | None = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        for statement in SCHEMA_STATEMENTS:
            cursor.execute(statement)
        for statement in INDEX_STATEMENTS:
            cursor.execute(statement)
        connection.commit()
        return True
    except sqlite3.Error as exc:
        _log_exception("initialize_database", exc)
        return False
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    success: bool = initialize_database()
    print("Database initialized successfully." if success else "Database initialization FAILED. Check logs/db_errors.log.")
