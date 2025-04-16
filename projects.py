import streamlit as st
import json
import uuid
import datetime
from pathlib import Path
from config import PROJECTS_DIR # Import the directory path


def load_projects():
    try:
        projects = sorted(list(PROJECTS_DIR.glob("*.json")), key=lambda p: p.stat().st_mtime, reverse=True)
        return [p.stem for p in projects]
    except Exception as e:
        st.error(f"Error loading project list: {e}")
        return []

def save_project(name, data):
    if not name.strip():
        st.error("Project name cannot be empty.")
        return False
    filepath = PROJECTS_DIR / f"{name}.json"
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4) # Use indent for readability
        st.success(f"Project '{name}' saved successfully!")
        return True
    except Exception as e:
        st.error(f"Error saving project '{name}': {str(e)}")
        return False

def load_project(name):
    filepath = PROJECTS_DIR / f"{name}.json"
    if not filepath.exists():
        st.error(f"Project file not found: {filepath}")
        return None
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        st.error(f"Error decoding project file '{name}': {str(e)}. The file might be corrupted.")
        return None
    except Exception as e:
        st.error(f"Error loading project '{name}': {str(e)}")
        return None

def delete_project(name):
    if not name:
        return False
    filepath = PROJECTS_DIR / f"{name}.json"
    try:
        if filepath.exists():
            filepath.unlink()
            st.success(f"Project '{name}' deleted.")
            return True
        else:
            st.warning(f"Project file '{name}' not found for deletion.")
            return False
    except Exception as e:
        st.error(f"Error deleting project '{name}': {e}")
        return False