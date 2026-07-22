"""
COLEXA_HVAC.exe entry point.

PyInstaller executables cannot simply shell out to `streamlit run app.py`,
so this script boots the Streamlit server programmatically and opens the
default web browser to it. Used only when building via COLEXA_HVAC.spec;
during normal development, run `streamlit run app.py` directly instead.
"""

import os
import sys
import threading
import webbrowser

from streamlit.web import cli as streamlit_cli


def _open_browser_when_ready(url: str, delay_seconds: float = 2.5) -> None:
    """Open the default browser to the local Streamlit server after a short delay.

    Args:
        url: The local URL the Streamlit server is bound to.
        delay_seconds: How long to wait before opening, to give the server
            time to bind its port.
    """
    timer = threading.Timer(delay_seconds, lambda: webbrowser.open(url))
    timer.daemon = True
    timer.start()


def main() -> None:
    """Launch the bundled Streamlit app on localhost with browser auto-open."""
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    app_path = os.path.join(base_dir, "app.py")
    if not os.path.exists(app_path):
        # Fallback for source-tree execution (not frozen)
        app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")

    local_url = "http://localhost:8501"
    _open_browser_when_ready(local_url)

    sys.argv = [
        "streamlit", "run", app_path,
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
    ]
    sys.exit(streamlit_cli.main())


if __name__ == "__main__":
    main()
