import streamlit as st
import numpy as np
import torch # Keep torch import if checking cuda availability here

# Import from local modules
from config import configure_page, apply_theme, apply_custom_css, setup_directories
from utils import add_to_history # Only add_to_history if used directly in sidebar? Check usage.
from projects import load_projects

# Import App functions from modes
from modes.inpainting import inpainting_app
from modes.text2img import text2img_app
from modes.editor import image_editor_app
from modes.restore import restore_old_photo_app
from modes.batch import batch_processing_app
from modes.projects_display import project_manager_app

# --- Initial Setup ---
configure_page()
setup_directories()
apply_custom_css() # Apply CSS early
apply_theme()      # Apply theme right after CSS

# --- Session State Initialization ---
required_state_vars = {
    'history': [],
    'current_project_data': None, # Changed from current_project
    'projects': [],
    # Mode specific states will be initialized within their respective functions if needed
}

for key, default_value in required_state_vars.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

if not st.session_state.projects: # Load initial projects if list is empty
     st.session_state.projects = load_projects()


# --- Sidebar ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/huggingface/diffusers/main/docs/source/imgs/diffusers_library.jpg", use_column_width=True)
    st.title("AI Image Studio")
    st.markdown("### ✨ Modes")

    mode_options = {
        "📝 Inpainting": "inpaint",
        "✨ Text-to-Image": "text2img",
        "🖼️ Image Editor": "editor",
        "🔧 Restore Old Photo": "restore",
        "📊 Batch Processing": "batch",
        "📁 Project Manager": "projects"
    }
    selected_mode_label = st.radio(
        "Select mode:",
        list(mode_options.keys()),
        key="main_mode_selector",
        horizontal=False # Vertical layout might be better for more options
    )
    mode = mode_options[selected_mode_label]

    st.markdown("---")
    st.markdown("### 🤖 Model Selection")
    st.caption("Choose the base model for the selected mode.")

    # Define model choices based on mode
    model_choices = {}
    if mode == "inpaint":
        model_choices = {
            "SD 1.5 Inpainting": "runwayml/stable-diffusion-inpainting",
            "SD 2 Inpainting": "stabilityai/stable-diffusion-2-inpainting",
            # "SDXL Inpainting (Experimental)": "stabilityai/stable-diffusion-xl-1.0-inpainting-0.1" # Check exact name
        }
    elif mode == "text2img":
        model_choices = {
            "SD 1.5": "runwayml/stable-diffusion-v1-5",
            "SD 2.1": "stabilityai/stable-diffusion-2-1",
            "SDXL 1.0 (Experimental)": "stabilityai/stable-diffusion-xl-base-1.0",
        }
    elif mode == "restore" or mode == "editor" or mode == "batch": # Modes often using Img2Img
        model_choices = {
             "SD 1.5": "runwayml/stable-diffusion-v1-5",
             "SD 2.1": "stabilityai/stable-diffusion-2-1",
             "SDXL 1.0 (Experimental)": "stabilityai/stable-diffusion-xl-base-1.0", # Base can work for img2img too
             "SD 1.5 Inpainting (for basic enhance)": "runwayml/stable-diffusion-inpainting", # Sometimes useful
        }
    elif mode == "projects":
         model_choices = {"N/A": None} # No model needed for project management
    else: # Default fallback
         model_choices = {
            "SD 1.5": "runwayml/stable-diffusion-v1-5",
         }

    # Prevent errors if model_choices is empty
    if model_choices and "N/A" not in model_choices:
        model_select_key = f"model_select_{mode}"
        # Set default index intelligently if possible, else 0
        default_index = 0
        if "SDXL" in str(model_choices.keys()) and len(model_choices) > 2: default_index = 2
        elif "SD 2.1" in str(model_choices.keys()) and len(model_choices) > 1: default_index = 1

        selected_model_label = st.selectbox(
            "Select Model",
            list(model_choices.keys()),
            index=default_index, # Sensible default
            key=model_select_key
        )
        model_id = model_choices[selected_model_label]
    else:
        model_id = None # No model relevant for this mode


    # --- Common Generation Settings ---
    if mode != "projects": # Settings not needed for project manager
        st.markdown("---")
        st.markdown("### 🛠️ Generation Settings")

        num_inference_steps = st.slider("Steps", 10, 150, 30, 5, key="common_steps", help="Number of denoising steps. More steps take longer but can improve quality (diminishing returns).")
        guidance_scale = st.slider("Guidance (CFG)", 1.0, 20.0, 7.5, 0.5, key="common_cfg", help="How strongly the prompt guides generation. Higher values follow the prompt more closely, lower values allow more creativity.")
        seed = st.number_input("Seed", -1, 2**32 - 1, 42, key="common_seed", help="Controls randomness. Set to -1 for a random seed on each run.")

        strength = 0.75 # Default, only used by some modes
        if mode in ["inpaint", "restore", "editor", "batch"]: # Modes using strength
             strength = st.slider("Strength / Influence", 0.0, 1.0, 0.75, 0.05, key="common_strength", help="For Inpaint/Img2Img/Restore: Controls how much the original image is changed (0.0 = no change, 1.0 = max change).")

        # Size settings only for Text2Img and potentially Batch Text2Img
        width, height, num_images = 512, 512, 1 # Defaults
        if mode == "text2img" or (mode == "batch" and st.session_state.get("batch_op_type") == "Text-to-Image Variations"):
            st.markdown("#### Image Dimensions & Count")
            img_size_cols = st.columns(2)
            with img_size_cols[0]:
                 width = st.select_slider("Width", [256, 512, 640, 768, 1024], 512, key="common_width")
            with img_size_cols[1]:
                 height = st.select_slider("Height", [256, 512, 640, 768, 1024], 512, key="common_height")
            if mode == "text2img": # Only show num_images for single text2img
                 num_images = st.slider("Number of Images", 1, 4, 1, key="common_num_images", help="How many images to generate at once.")

    # --- History Panel ---
    st.markdown("---")
    st.markdown("### 📜 History (Last 5)")
    if st.session_state.history:
        for item in reversed(st.session_state.history[-5:]):
            cols = st.columns([1, 3])
            with cols[0]:
                st.image(item["thumbnail"], width=60)
            with cols[1]:
                st.caption(f"{item['mode'].capitalize()} ({item['time']})")
                st.caption(item['prompt'][:50] + "..." if len(item['prompt']) > 50 else item['prompt'])
    else:
        st.caption("No generations yet.")


# --- Main Area Router ---
def main():
    # Display title based on mode
    titles = {
        "inpaint": "📝 AI Image Inpainting",
        "text2img": "✨ AI Text-to-Image Generator",
        "editor": "🖼️ AI Image Editor",
        "restore": "🔧 AI Photo Restoration",
        "batch": "📊 Batch Processing",
        "projects": "📁 Project Manager"
    }
    st.title(titles.get(mode, "AI Image Studio"))

    # Call the appropriate function based on the selected mode
    # Pass necessary parameters from the sidebar
    if mode == "inpaint":
        inpainting_app(model_id, seed, guidance_scale, num_inference_steps, strength)
    elif mode == "text2img":
        text2img_app(model_id, seed, guidance_scale, num_inference_steps, width, height, num_images)
    elif mode == "editor":
        image_editor_app(model_id, seed, guidance_scale, num_inference_steps, strength)
    elif mode == "restore":
        restore_old_photo_app(model_id, seed, guidance_scale, num_inference_steps, strength)
    elif mode == "batch":
        # Batch needs specific width/height if doing T2I, otherwise maybe not
        batch_processing_app(model_id, seed, guidance_scale, num_inference_steps, strength, width, height)
    elif mode == "projects":
        project_manager_app()

if __name__ == '__main__':
    # Check CUDA availability once at the start (optional, models.py handles device)
    if torch.cuda.is_available():
        st.sidebar.success(f"CUDA Available ({torch.cuda.get_device_name(0)})")
    else:
        st.sidebar.warning("CUDA not available, running on CPU (will be slow).")
    main()