"""Frontend entrypoint for Streamlit, matching the Capstone Submission Guidelines (Section 11).
Runs the Streamlit application from streamlit_app.py.
Command: streamlit run frontend.py
"""
import runpy
import sys
from pathlib import Path

# Run streamlit_app.py in this process namespace
app_path = Path(__file__).parent / "streamlit_app.py"
runpy.run_path(str(app_path), run_name="__main__")
