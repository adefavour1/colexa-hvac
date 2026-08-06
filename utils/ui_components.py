"""
COLEXA BIOSENSOR - HVAC Monitoring Platform
Corporate theme CSS, reusable custom widgets, and parameter boundary evaluators.

Boundary ranges below are sourced from the controlled paper form
"HVAC Monitoring Log" (Doc No. CBL/ENG/02/R01) currently in use on the
production floor, NOT from a generic HVAC textbook default. If the
facility's validated ranges change, update PARAMETER_BOUNDS below and the
change will propagate through the whole application.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Brand palette
# ---------------------------------------------------------------------------

COLOR_CANVAS: str = "#0B0F19"
COLOR_SIDEBAR: str = "#06080F"
COLOR_CARD_A: str = "#111827"
COLOR_CARD_B: str = "#1E293B"
COLOR_CYAN: str = "#06B6D4"
COLOR_BIOGREEN: str = "#C1F24D"
COLOR_RED: str = "#EF4444"
COLOR_AMBER: str = "#F59E0B"
COLOR_NOMINAL: str = "#C1F24D"

# ---------------------------------------------------------------------------
# Validated parameter boundaries (source: HVAC Monitoring Log, Doc CBL/ENG/02/R01)
# Each entry: (label, unit, lower_limit, upper_limit, referenced_sop)
# ---------------------------------------------------------------------------

PARAMETER_BOUNDS: dict[str, dict[str, object]] = {
    "ahu_temperature": {"label": "AHU Control Panel Temp", "unit": "°C", "low": 0.0, "high": 30.0, "sop": "CBL-MNT-02"},
    "ahu_rh": {"label": "AHU Control Panel RH", "unit": "%", "low": 20, "high": 40, "sop": "CBL-MNT-02"},
    "dhu1_rh": {"label": "DHU-1 RH", "unit": "%", "low": 30.0, "high": 40.0, "sop": "CBL-MNT-05"},
    "dhu1_dpg": {"label": "DHU-1 DPG", "unit": "mmWC", "low": 2.5, "high": 25.0, "sop": "CBL-MNT-05"},
    "dhu2_rh": {"label": "DHU-2 RH", "unit": "%", "low": 30.0, "high": 40.0, "sop": "CBL-MNT-05"},
    "dhu2_dpg": {"label": "DHU-2 DPG", "unit": "mmWC", "low": 2.5, "high": 25.0, "sop": "CBL-MNT-05"},
    "ac_temp_1": {"label": "Air Conditioning Temp-1", "unit": "°C", "low": 20.0, "high": 30.0, "sop": "CBL-MNT-02"},
    "ac_temp_2": {"label": "Air Conditioning Temp-2", "unit": "°C", "low": 20.0, "high": 30.0, "sop": "CBL-MNT-02"},
    "ac_temp_3": {"label": "Air Conditioning Temp-3", "unit": "°C", "low": 20.0, "high": 30.0, "sop": "CBL-MNT-02"},
    "compressor_pressure": {"label": "Air Compressor Pressure", "unit": "Bar", "low": 5.0, "high": 7.0, "sop": "CBL-MNT-03"},
}

# Extended engineering parameters (not on the paper log, but referenced by the
# module deep-dive pages). Ranges here are conservative GMP defaults and
# should be confirmed against equipment datasheets / validation protocols
# before being treated as release-critical limits.
EXTENDED_PARAMETER_BOUNDS: dict[str, dict[str, object]] = {
    "supply_temp": {"label": "AHU Supply Air Temp", "unit": "°C", "low": 20.0, "high": 24.0, "sop": "CBL-MNT-02"},
    "differential_pressure": {"label": "AHU Room Differential Pressure", "unit": "Pa", "low": 15.0, "high": 45.0, "sop": "CBL-MNT-02"},
    "filter_delta_p": {"label": "AHU Filter Delta-P", "unit": "Pa", "low": 0.0, "high": 250.0, "sop": "CBL-MNT-02"},
    "dew_point": {"label": "DHU Dew Point", "unit": "°C", "low": -40.0, "high": -20.0, "sop": "CBL-MNT-05"},
    "discharge_temp": {"label": "Compressor Discharge Temp", "unit": "°C", "low": 20.0, "high": 85.0, "sop": "CBL-MNT-03"},
    "oil_differential": {"label": "Compressor Oil Differential", "unit": "Bar", "low": 0.0, "high": 1.0, "sop": "CBL-MNT-03"},
}


def evaluate_parameter_bounds(parameter_key: str, value: float) -> dict[str, object]:
    """Evaluate a telemetry value against its validated boundary.

    Args:
        parameter_key: Key into PARAMETER_BOUNDS or EXTENDED_PARAMETER_BOUNDS.
        value: The observed numeric reading.

    Returns:
        Dict with keys: in_bounds (bool), status ("Nominal" | "Low Warning" |
        "High Excursion"), low, high, unit, label, referenced_sop.
        Returns a permissive default if parameter_key is unknown.
    """
    bounds: dict[str, object] | None = PARAMETER_BOUNDS.get(parameter_key) or EXTENDED_PARAMETER_BOUNDS.get(parameter_key)
    if bounds is None:
        return {"in_bounds": True, "status": "Unknown Parameter", "low": None, "high": None, "unit": "", "label": parameter_key, "referenced_sop": ""}

    low: float = float(bounds["low"])
    high: float = float(bounds["high"])
    status: str = "Nominal"
    in_bounds: bool = True

    if value < low:
        status = "Low Warning"
        in_bounds = False
    elif value > high:
        status = "High Excursion"
        in_bounds = False

    return {
        "in_bounds": in_bounds,
        "status": status,
        "low": low,
        "high": high,
        "unit": bounds["unit"],
        "label": bounds["label"],
        "referenced_sop": bounds["sop"],
    }


def status_color(status: str) -> str:
    """Map a boundary status string to a brand hex color.

    Args:
        status: One of "Nominal", "Low Warning", "High Excursion".

    Returns:
        A hex color string.
    """
    mapping: dict[str, str] = {
        "Nominal": COLOR_NOMINAL,
        "Low Warning": COLOR_AMBER,
        "High Excursion": COLOR_RED,
    }
    return mapping.get(status, COLOR_CYAN)


def inject_global_css() -> None:
    """Inject the Colexa Biosensor corporate slate theme via unsafe HTML/CSS.

    Call this once near the top of every page.
    """
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {COLOR_CANVAS};
            color: #E5E7EB;
        }}
        section[data-testid="stSidebar"] {{
            background-color: {COLOR_SIDEBAR};
            border-right: 1px solid #1F2937;
        }}
        section[data-testid="stSidebar"] * {{
            color: #E5E7EB !important;
        }}
        [data-testid="collapsedControl"] svg, button[kind="header"] svg {{
            color: {COLOR_CYAN} !important;
            fill: {COLOR_CYAN} !important;
        }}
        .colexa-ribbon {{
            height: 6px;
            width: 100%;
            background: linear-gradient(90deg, {COLOR_BIOGREEN} 0%, {COLOR_CYAN} 100%);
            border-radius: 3px;
            margin-bottom: 1.1rem;
        }}
        .colexa-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem 1.25rem;
            background: linear-gradient(135deg, {COLOR_CARD_A} 0%, {COLOR_CARD_B} 100%);
            border: 1px solid #1F2937;
            border-radius: 14px;
            margin-bottom: 1rem;
        }}
        .colexa-header h1 {{
            font-size: 1.5rem;
            margin: 0;
            color: #F8FAFC;
        }}
        .colexa-header .subtitle {{
            color: {COLOR_CYAN};
            font-size: 0.85rem;
            margin-top: 2px;
        }}
        .colexa-badge {{
            display: inline-block;
            padding: 0.2rem 0.7rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            border: 1px solid {COLOR_CYAN};
            color: {COLOR_CYAN};
            background: rgba(6, 182, 212, 0.08);
        }}
        .colexa-kpi-card {{
            background: linear-gradient(160deg, {COLOR_CARD_A} 0%, {COLOR_CARD_B} 100%);
            border: 1px solid #1F2937;
            border-radius: 16px;
            padding: 1.1rem 1.2rem;
            transition: box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease;
        }}
        .colexa-kpi-card:hover {{
            box-shadow: 0 0 22px rgba(6, 182, 212, 0.35);
            border-color: {COLOR_CYAN};
            transform: translateY(-2px);
        }}
        .colexa-kpi-label {{
            font-size: 0.78rem;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .colexa-kpi-value {{
            font-size: 1.9rem;
            font-weight: 700;
            color: #F8FAFC;
            margin-top: 0.15rem;
        }}
        .colexa-alert-card {{
            border-radius: 14px;
            padding: 0.9rem 1.1rem;
            border-left: 5px solid;
            margin-bottom: 0.6rem;
            background: {COLOR_CARD_A};
        }}
        .stButton > button {{
            background: linear-gradient(90deg, {COLOR_CYAN} 0%, {COLOR_BIOGREEN} 100%);
            color: #06080F;
            font-weight: 700;
            border: none;
            border-radius: 10px;
            padding: 0.5rem 1.1rem;
            transition: filter 0.15s ease, transform 0.15s ease;
        }}
        .stButton > button:hover {{
            filter: brightness(1.08);
            transform: translateY(-1px);
        }}
        div[data-testid="stMetric"] {{
            background: {COLOR_CARD_A};
            border: 1px solid #1F2937;
            border-radius: 14px;
            padding: 0.8rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_ribbon() -> None:
    """Render the signature gradient ribbon at the top of a page."""
    st.markdown('<div class="colexa-ribbon"></div>', unsafe_allow_html=True)


def render_facility_header(title: str, subtitle: str = "ISO 13485:2016 | FDA 21 CFR Part 11 Baseline") -> None:
    """Render the branded facility header banner.

    Args:
        title: Page title text.
        subtitle: Small regulatory context line under the title.
    """
    render_top_ribbon()
    st.markdown(
        f"""
        <div class="colexa-header">
            <div>
                <h1>{title}</h1>
                <div class="subtitle">{subtitle}</div>
            </div>
            <div class="colexa-badge">COLEXA BIOSENSOR &bull; HVAC MATRIX</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, help_text: str = "") -> None:
    """Render a single custom KPI card with glow-on-hover styling.

    Args:
        label: KPI label, shown uppercase.
        value: The KPI value, already formatted as a string.
        help_text: Optional small caption below the value.
    """
    st.markdown(
        f"""
        <div class="colexa-kpi-card">
            <div class="colexa-kpi-label">{label}</div>
            <div class="colexa-kpi-value">{value}</div>
            <div style="color:#64748B;font-size:0.75rem;margin-top:0.25rem;">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_deviation_alert(parameter_label: str, status: str, observed: float, low: float, high: float, unit: str) -> None:
    """Render an inline visual deviation alert card.

    Args:
        parameter_label: Human-readable parameter name.
        status: "Low Warning" or "High Excursion" (Nominal is not alerted).
        observed: The observed value that triggered the alert.
        low: Validated lower limit.
        high: Validated upper limit.
        unit: Engineering unit string.
    """
    color: str = status_color(status)
    st.markdown(
        f"""
        <div class="colexa-alert-card" style="border-left-color:{color};">
            <strong style="color:{color};">&#9888; {status}: {parameter_label}</strong><br>
            <span style="color:#CBD5E1;">Observed: {observed} {unit} &nbsp;|&nbsp; Validated range: {low}&ndash;{high} {unit}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
