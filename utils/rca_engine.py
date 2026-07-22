"""
COLEXA BIOSENSOR - HVAC Monitoring Platform
Root Cause Analysis (RCA) failure-mode dictionary and CAPA recommendation logic.

IMPORTANT SOURCING NOTE:
The three underlying SOPs on file at Colexa Biosensor -
    CBL-MNT-02 (AHU Operating Procedure)
    CBL-MNT-03 (Air Compressor Operating Procedure)
    CBL-MNT-05 (Dehumidifier Operating Procedure)
are start-up/shutdown operating procedures. They do not contain a
pre-numbered failure-mode or CAPA-code table. The probable-cause and CAPA
text below is therefore built from standard GMP/cleanroom HVAC engineering
practice, and every recommendation is tagged back to the specific SOP
document number that governs the corrective action (e.g. re-running the
AHU start-up sequence falls under CBL-MNT-02). These should be reviewed and
formally approved by Engineering/QA before being treated as validated CAPA
text in a regulated environment.
"""

from datetime import datetime
from typing import Any


# Failure-mode knowledge base keyed by parameter, then by direction of the
# excursion ("Low Warning" or "High Excursion").
RCA_KNOWLEDGE_BASE: dict[str, dict[str, dict[str, Any]]] = {
    "ahu_temperature": {
        "High Excursion": {
            "causes": [
                "AHU cooling coil / chilled water supply insufficient",
                "Fresh air damper stuck open admitting warm ambient air",
                "Return air recirculation fan fault or belt slippage",
            ],
            "severity": "Major",
            "capa": "Verify chiller plant supply temperature; inspect and re-seat fresh air dampers per start-up checklist; re-run AHU start-up sequence (power, doors, dampers, drain line) as documented in CBL-MNT-02 before restart.",
        },
        "Low Warning": {
            "causes": [
                "Cooling coil overcooling / control valve stuck open",
                "Thermostat/hygrometer sensor drift",
                "Excess fresh air intake beyond design set point",
            ],
            "severity": "Minor",
            "capa": "Recalibrate the monitoring hygrometer on the control panel; verify cooling valve modulation; confirm fresh air damper position matches design intent per CBL-MNT-02.",
        },
    },
    "ahu_rh": {
        "High Excursion": {
            "causes": [
                "Condensate drain line blocked, raising in-duct moisture",
                "Fresh air damper admitting humid ambient air",
                "AHU dehumidification coil undersized for current load",
            ],
            "severity": "Major",
            "capa": "Inspect and clear the condensate drainpipe and floor drain for clear drainage as specified in CBL-MNT-02 Step 5.4; verify all doors are fully closed to prevent infiltration; escalate to Engineering if RH does not recover within one shift.",
        },
        "Low Warning": {
            "causes": [
                "Hygrometer sensor fault or drift",
                "Excess dry fresh air intake",
            ],
            "severity": "Minor",
            "capa": "Recalibrate hygrometer; confirm timer panel and hygrometer power per CBL-MNT-02 Step 5.7.",
        },
    },
    "dhu1_rh": {
        "High Excursion": {
            "causes": [
                "Desiccant wheel regeneration heater fault",
                "Reactant/heat reactant filters clogged, reducing process air moisture removal",
                "Moisture ingress through an unsealed door or duct joint",
            ],
            "severity": "Critical",
            "capa": "Remove, inspect, and clean the reactant and heat reactant filters per CBL-MNT-05 Step 5.1-5.2; verify regeneration temperature set point on the DHU control panel; log as a moisture ingress risk event for the dry room and notify QA if RH remains out of range beyond 2 hours.",
        },
        "Low Warning": {
            "causes": [
                "RH sensor drift",
                "Over-regeneration lowering moisture below target band",
            ],
            "severity": "Minor",
            "capa": "Recalibrate DHU RH sensor; review temperature/humidity set points entered via the DHU control panel per CBL-MNT-05 Step 5.7-5.9.",
        },
    },
    "dhu2_rh": {
        "High Excursion": {
            "causes": [
                "Desiccant wheel regeneration heater fault",
                "Reactant/heat reactant filters clogged",
                "Moisture ingress through an unsealed door or duct joint",
            ],
            "severity": "Critical",
            "capa": "Remove, inspect, and clean the reactant and heat reactant filters per CBL-MNT-05 Step 5.1-5.2; verify DHU K1 operation button engaged correctly per CBL-MNT-05 Step 5.6; escalate to QA if excursion persists beyond 2 hours.",
        },
        "Low Warning": {
            "causes": [
                "RH sensor drift",
                "Over-regeneration lowering moisture below target band",
            ],
            "severity": "Minor",
            "capa": "Recalibrate DHU RH sensor; review set points per CBL-MNT-05 Step 5.7-5.9.",
        },
    },
    "dhu1_dpg": {
        "High Excursion": {
            "causes": [
                "Filter loading / progressive blockage increasing differential pressure",
                "Duct or damper obstruction downstream of the desiccant wheel",
            ],
            "severity": "Major",
            "capa": "Schedule filter cleaning/replacement per CBL-MNT-05 filter maintenance step; inspect ductwork for obstruction; trend DPG weekly to anticipate filter change-out.",
        },
        "Low Warning": {
            "causes": [
                "DPG gauge/sensor fault",
                "Filter bypass or seal failure lowering resistance abnormally",
            ],
            "severity": "Minor",
            "capa": "Inspect filter seating and gasket integrity; verify DPG gauge calibration.",
        },
    },
    "dhu2_dpg": {
        "High Excursion": {
            "causes": [
                "Filter loading / progressive blockage increasing differential pressure",
                "Duct or damper obstruction downstream of the desiccant wheel",
            ],
            "severity": "Major",
            "capa": "Schedule filter cleaning/replacement per CBL-MNT-05 filter maintenance step; inspect ductwork for obstruction; trend DPG weekly to anticipate filter change-out.",
        },
        "Low Warning": {
            "causes": [
                "DPG gauge/sensor fault",
                "Filter bypass or seal failure",
            ],
            "severity": "Minor",
            "capa": "Inspect filter seating and gasket integrity; verify DPG gauge calibration.",
        },
    },
    "ac_temp_1": {
        "High Excursion": {"causes": ["AC compressor/condenser fault", "Blocked condenser airflow", "Refrigerant undercharge"], "severity": "Major", "capa": "Inspect condenser coil for blockage; verify refrigerant charge; escalate to HVAC technician if temperature does not recover."},
        "Low Warning": {"causes": ["Thermostat/sensor drift", "Overcooling due to control fault"], "severity": "Minor", "capa": "Recalibrate zone thermostat/sensor; verify control set point."},
    },
    "ac_temp_2": {
        "High Excursion": {"causes": ["AC compressor/condenser fault", "Blocked condenser airflow", "Refrigerant undercharge"], "severity": "Major", "capa": "Inspect condenser coil for blockage; verify refrigerant charge; escalate to HVAC technician if temperature does not recover."},
        "Low Warning": {"causes": ["Thermostat/sensor drift", "Overcooling due to control fault"], "severity": "Minor", "capa": "Recalibrate zone thermostat/sensor; verify control set point."},
    },
    "ac_temp_3": {
        "High Excursion": {"causes": ["AC compressor/condenser fault", "Blocked condenser airflow", "Refrigerant undercharge"], "severity": "Major", "capa": "Inspect condenser coil for blockage; verify refrigerant charge; escalate to HVAC technician if temperature does not recover."},
        "Low Warning": {"causes": ["Thermostat/sensor drift", "Overcooling due to control fault"], "severity": "Minor", "capa": "Recalibrate zone thermostat/sensor; verify control set point."},
    },
    "compressor_pressure": {
        "High Excursion": {
            "causes": [
                "Pressure relief/unloading valve set point drift",
                "Downstream demand drop causing storage cylinder over-pressurization",
                "Control system failure to unload at set pressure",
            ],
            "severity": "Critical",
            "capa": "Immediately verify the discharge/storage cylinder valve per CBL-MNT-03 Step 5.7-5.8; check pressure relief valve function; do not exceed manufacturer-rated cylinder pressure; escalate to Engineering immediately.",
        },
        "Low Warning": {
            "causes": [
                "Oil level low or oil leakage reducing compression efficiency",
                "Air leak in delivery line or fittings",
                "Intake filter blockage restricting compressor loading",
            ],
            "severity": "Major",
            "capa": "Check oil level and inspect for leakage per CBL-MNT-03 Step 5.1-5.3; inspect delivery line and fittings for leaks; flush condensate from the storage cylinder per CBL-MNT-03 Step 5.7.",
        },
    },
}

DEFAULT_RESULT: dict[str, Any] = {
    "causes": ["Parameter not yet mapped in the RCA knowledge base."],
    "severity": "Minor",
    "capa": "Escalate to Engineering for manual root cause review; no automated CAPA rule exists for this parameter yet.",
}


def get_rca_capa(parameter_key: str, status: str, referenced_sop: str = "") -> dict[str, Any]:
    """Look up probable causes, severity, and CAPA text for a deviation.

    Args:
        parameter_key: Internal parameter key (e.g. "compressor_pressure").
        status: "Low Warning" or "High Excursion".
        referenced_sop: SOP document number associated with this parameter,
            passed through from utils.ui_components.PARAMETER_BOUNDS.

    Returns:
        Dict with keys: causes (list[str], top 3), severity (str),
        recommended_capa (str), referenced_sop (str), generated_at (str ISO).
    """
    parameter_entry: dict[str, dict[str, Any]] = RCA_KNOWLEDGE_BASE.get(parameter_key, {})
    result: dict[str, Any] = parameter_entry.get(status, DEFAULT_RESULT)

    top_causes: list[str] = list(result.get("causes", DEFAULT_RESULT["causes"]))[:3]

    return {
        "causes": top_causes,
        "severity": result.get("severity", "Minor"),
        "recommended_capa": result.get("capa", DEFAULT_RESULT["capa"]),
        "referenced_sop": referenced_sop or "Engineering Review Required",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def severity_rank(severity: str) -> int:
    """Convert a severity label to a sortable integer rank.

    Args:
        severity: "Minor", "Major", or "Critical".

    Returns:
        1 for Minor, 2 for Major, 3 for Critical, 0 if unrecognized.
    """
    ranking: dict[str, int] = {"Minor": 1, "Major": 2, "Critical": 3}
    return ranking.get(severity, 0)
