import streamlit as st
from pathlib import Path

# --- Directories ---
SAVE_DIR = Path("saved_images")
PROJECTS_DIR = Path("projects")

# --- Create Directories ---
def setup_directories():
    SAVE_DIR.mkdir(exist_ok=True)
    PROJECTS_DIR.mkdir(exist_ok=True)

# --- Page Config ---
def configure_page():
    st.set_page_config(
        page_title="Advanced AI Image Studio",
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# --- Theme ---
def apply_theme():
    theme = st.selectbox("Select Theme", ["Light", "Dark"], key="theme_selector")
    if theme == "Dark":
        st.markdown("""
        <style>
        .main {
            background-color: #1e1e1e;
            color: white;
        }
        /* Add other dark theme specific styles if needed */
        </style>
        """, unsafe_allow_html=True)
    # Optionally add light theme specific overrides if needed
    # else: ...

# --- Custom CSS ---
def apply_custom_css():
    st.markdown("""
    <style>
    .main {
        /* Base styles */
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    h1, h2, h3 {
        color: #1e3a8a; /* Default for light theme */
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2563eb;
    }
    .info-box {
        background-color: #e0f2fe;
        padding: 1rem;
        border-radius: 6px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
        color: #0c5460; /* Adjust color for light theme */
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 6px;
        border-left: 4px solid #fbbf24;
        margin-bottom: 1rem;
        color: #856404; /* Adjust color for light theme */
    }
    .feature-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f1f5f9;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
        font-weight: 600;
        color: #334155; /* Default text color */
    }
    .stTabs [aria-selected="true"] {
        background-color: #dbeafe !important;
        color: #1e40af !important;
    }
    .result-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-top: 1.5rem;
    }
    .gallery-item {
        transition: transform 0.2s;
    }
    .gallery-item:hover {
        transform: scale(1.03);
    }
    .label {
        font-size: 0.85rem;
        color: #6b7280;
        margin-bottom: 4px;
    }
    /* Dark theme overrides */
    .main.dark h1, .main.dark h2, .main.dark h3 {
        color: #90caf9; /* Example dark theme color */
    }
    .main.dark .info-box {
         background-color: #1c313a;
         color: #e0f7fa;
         border-left-color: #4fc3f7;
    }
    .main.dark .warning-box {
        background-color: #332a00;
        color: #fffde7;
        border-left-color: #ffeb3b;
    }
    .main.dark .feature-card {
        background-color: #2c2c2c;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }
     .main.dark .stTabs [data-baseweb="tab"] {
        background-color: #374151;
        color: #d1d5db;
    }
    .main.dark .stTabs [aria-selected="true"] {
        background-color: #4b5563 !important;
        color: #e5e7eb !important;
    }
     .main.dark .result-container {
        background-color: #2c2c2c;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
     .main.dark .label {
        color: #9ca3af;
    }

    </style>
    """, unsafe_allow_html=True)