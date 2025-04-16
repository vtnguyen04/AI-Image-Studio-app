import streamlit as st
from PIL import Image
import numpy as np
import uuid
import datetime

from utils import resize_image, get_image_download_link, save_image_to_disk, add_to_history
from models import load_img2img_model # Restoration often uses Img2Img
from processing import process_img2img
from projects import save_project, load_projects

def restore_old_photo_app(model_id, seed, guidance_scale, num_inference_steps, strength):
    st.markdown('<div class="info-box">Upload an old or damaged photo. The AI will attempt to restore it based on your prompt and settings.</div>', unsafe_allow_html=True)

    if 'restore_input_image' not in st.session_state:
        st.session_state.restore_input_image = None
    if 'restore_result_image' not in st.session_state:
        st.session_state.restore_result_image = None
    if 'restore_last_seed' not in st.session_state:
        st.session_state.restore_last_seed = seed

    uploaded_file = st.file_uploader("Upload old/damaged photo", type=["png", "jpg", "jpeg"], key="restore_upload")

    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file).convert("RGB")
            # Resize slightly if too large, but try to keep resolution
            st.session_state.restore_input_image = resize_image(image, max_size=1024)
            st.session_state.restore_result_image = None # Reset result on new upload
        except Exception as e:
            st.error(f"Error loading image: {e}")
            st.session_state.restore_input_image = None

    if st.session_state.restore_input_image is not None:
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Original Photo")
            st.image(st.session_state.restore_input_image, use_column_width=True)

        with col2:
            st.markdown("### Restoration Settings")
            default_prompt = "Restore old photo, sharp focus, clear details, remove scratches and noise, enhance colors, realistic, high quality photograph"
            default_neg_prompt = "blurry, noisy, low quality, artifacts, drawing, painting, cartoon, text, watermark, signature, border, frame, disfigured, deformed"

            prompt = st.text_area("Restoration Prompt", default_prompt, height=120, key="restore_prompt")
            negative_prompt = st.text_area("Negative Prompt", default_neg_prompt, height=100, key="restore_neg_prompt")

            st.markdown(f"**Strength:** `{strength:.2f}` (Sidebar Setting)")
            st.caption("Lower values preserve more original structure, higher values allow more AI change based on prompt.")


            if st.button("🔧 Restore Photo", key="restore_button"):
                try:
                    with st.spinner("Loading restoration model (Img2Img)..."):
                        pipe, device = load_img2img_model(model_id)

                    # Ensure image is suitable size for model
                    width, height = st.session_state.restore_input_image.size
                    target_width = (width // 8) * 8
                    target_height = (height // 8) * 8
                    if target_width == 0: target_width = 512
                    if target_height == 0: target_height = 512

                    img_to_process = st.session_state.restore_input_image
                    if img_to_process.size != (target_width, target_height):
                        st.write(f"Resizing input to {target_width}x{target_height} for model.")
                        img_to_process = img_to_process.resize((target_width, target_height), Image.LANCZOS)


                    result_image, used_seed = process_img2img(
                        pipe,
                        img_to_process,
                        prompt,
                        negative_prompt,
                        seed, # Use seed from sidebar
                        guidance_scale,
                        num_inference_steps,
                        strength # Use strength from sidebar for img2img
                    )

                    st.session_state.restore_last_seed = used_seed

                    if result_image is not None:
                        st.session_state.restore_result_image = result_image
                        add_to_history("restore", result_image, prompt) # Add to general history
                    else:
                        st.error("Restoration failed to produce an image.")

                except Exception as e:
                    st.error(f"Restoration failed: {str(e)}")

        # Display Result (outside the columns if a result exists)
        if st.session_state.restore_result_image is not None:
            st.markdown("---")
            st.markdown('<div class="result-container">', unsafe_allow_html=True)
            st.markdown("### ✨ Restored Photo")
            st.image(st.session_state.restore_result_image, caption=f"Restored (Seed: {st.session_state.restore_last_seed})", use_column_width=True)

            col_dl, col_save_lib = st.columns(2)
            with col_dl:
                st.markdown(
                    get_image_download_link(
                        st.session_state.restore_result_image,
                        f'restored_seed_{st.session_state.restore_last_seed}.png',
                        '📥 Download Result'
                    ),
                    unsafe_allow_html=True
                )
            with col_save_lib:
                 if st.button("💾 Save to Library", key="save_restore_lib"):
                    filepath = save_image_to_disk(st.session_state.restore_result_image, "restored")
                    if filepath:
                        st.success(f"Restored image saved to library.")

            st.markdown("</div>", unsafe_allow_html=True) # Close result container

            # Save Project
            st.markdown("---")
            project_name_restore = st.text_input("Save Restoration as Project:", key="restore_project_name", placeholder="e.g., Grandparents Photo Restore")
            if project_name_restore and st.button("💾 Save Project", key="save_restore_project"):
                orig_path = save_image_to_disk(st.session_state.restore_input_image, f"{project_name_restore}_orig")
                result_path = save_image_to_disk(st.session_state.restore_result_image, f"{project_name_restore}_restored")

                if orig_path and result_path:
                    project_data = {
                        "id": str(uuid.uuid4()),
                        "name": project_name_restore,
                        "type": "restoration",
                        "date": datetime.datetime.now().isoformat(),
                        "params": {
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "seed": st.session_state.restore_last_seed,
                            "guidance_scale": guidance_scale,
                            "strength": strength,
                            "steps": num_inference_steps,
                            "model_id": model_id
                        },
                        "paths": {
                            "original": str(orig_path),
                            "result": str(result_path)
                        }
                    }
                    if save_project(project_name_restore, project_data):
                        st.session_state.projects = load_projects() # Refresh project list
                else:
                    st.error("Failed to save images required for the project.")

    elif uploaded_file is None:
        st.info("Upload an old photo to begin the restoration process.")