import streamlit as st
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np

from utils import resize_image, get_image_download_link, save_image_to_disk, apply_basic_adjustments, apply_filter
from models import load_inpainting_model, load_img2img_model # Potentially need both
from processing import process_inpainting, process_img2img # Potentially need both

def image_editor_app(model_id, seed, guidance_scale, num_inference_steps, strength):
    st.markdown('<div class="info-box">Upload an image to apply adjustments, filters, or AI enhancements.</div>', unsafe_allow_html=True)

    if 'edit_image_original' not in st.session_state:
        st.session_state.edit_image_original = None
    if 'edit_image_current' not in st.session_state:
        st.session_state.edit_image_current = None
    if 'edit_history' not in st.session_state:
        st.session_state.edit_history = [] # To store states for undo

    uploaded_file = st.file_uploader("Upload an image to edit", type=["png", "jpg", "jpeg"], key="editor_upload")

    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file).convert("RGB")
            st.session_state.edit_image_original = image
            # Only reset current image and history if it's a *new* upload
            if st.session_state.edit_image_current is None or uploaded_file.name != st.session_state.get('editor_last_uploaded_name'):
                st.session_state.edit_image_current = image.copy()
                st.session_state.edit_history = [image.copy()]
                st.session_state.editor_last_uploaded_name = uploaded_file.name # Track filename

        except Exception as e:
            st.error(f"Error loading image: {e}")
            st.session_state.edit_image_original = None
            st.session_state.edit_image_current = None
            st.session_state.edit_history = []

    if st.session_state.edit_image_current is not None:
        st.markdown("---")
        col_display1, col_display2 = st.columns(2)
        with col_display1:
            st.markdown("### Original Image")
            st.image(st.session_state.edit_image_original, use_column_width=True)
        with col_display2:
            st.markdown("### Current Edit")
            st.image(st.session_state.edit_image_current, use_column_width=True)

            # Edit controls below the current image
            col_save1, col_save2, col_undo = st.columns(3)
            with col_save1:
                st.markdown(
                    get_image_download_link(
                        st.session_state.edit_image_current,
                        'edited_image.png',
                        '📥 Download Edit'
                    ),
                    unsafe_allow_html=True
                )
            with col_save2:
                if st.button("💾 Save to Library", key="editor_save_lib"):
                    filepath = save_image_to_disk(st.session_state.edit_image_current, "edited")
                    if filepath:
                        st.success(f"Edited image saved to {filepath}")
            with col_undo:
                 if st.button("↩️ Undo Last Edit", key="editor_undo", disabled=len(st.session_state.edit_history) <= 1):
                     st.session_state.edit_history.pop() # Remove current state
                     if st.session_state.edit_history:
                         st.session_state.edit_image_current = st.session_state.edit_history[-1].copy() # Restore previous
                     st.experimental_rerun() # Rerun to reflect the change

        st.markdown("---")
        edit_tabs = st.tabs(["Adjustments", "Filters", "AI Enhance"])

        # --- Tab 1: Basic Adjustments ---
        with edit_tabs[0]:
            st.markdown("#### Basic Adjustments")
            col1, col2 = st.columns(2)
            with col1:
                brightness = st.slider("Brightness", 0.1, 3.0, 1.0, step=0.05, key="edit_bright")
                contrast = st.slider("Contrast", 0.1, 3.0, 1.0, step=0.05, key="edit_contrast")
            with col2:
                sharpness = st.slider("Sharpness", 0.0, 3.0, 1.0, step=0.05, key="edit_sharp")
                saturation = st.slider("Saturation (Color)", 0.0, 3.0, 1.0, step=0.05, key="edit_sat")

            if st.button("Apply Adjustments", key="editor_apply_adjust"):
                with st.spinner("Applying adjustments..."):
                    # Apply adjustments to the *current* edited image
                    adjusted_image = apply_basic_adjustments(
                        st.session_state.edit_image_current,
                        brightness, contrast, sharpness, saturation
                    )
                    st.session_state.edit_image_current = adjusted_image
                    st.session_state.edit_history.append(adjusted_image.copy()) # Add new state to history
                    st.experimental_rerun() # Update display

        # --- Tab 2: Filters ---
        with edit_tabs[1]:
            st.markdown("#### Filters")
            filter_options = ["None", "Blur", "Sharpen", "Grayscale", "Sepia", "Edge Enhance", "Emboss"]
            selected_filter = st.selectbox("Select Filter", filter_options, key="editor_filter_select")

            intensity = 1.0
            if selected_filter in ["Blur", "Sharpen", "Sepia"]: # Filters that use intensity
                intensity = st.slider("Intensity", 0.1, 5.0, 1.0, step=0.1, key="editor_filter_intensity")

            if selected_filter != "None" and st.button("Apply Filter", key="editor_apply_filter"):
                 with st.spinner(f"Applying {selected_filter} filter..."):
                    filtered_image = apply_filter(st.session_state.edit_image_current, selected_filter, intensity)
                    st.session_state.edit_image_current = filtered_image
                    st.session_state.edit_history.append(filtered_image.copy())
                    st.experimental_rerun()

        # --- Tab 3: AI Enhancement ---
        with edit_tabs[2]:
            st.markdown("#### AI Enhancement")
            st.warning("AI Enhancements are experimental and may significantly alter the image.")

            ai_options = ["None", "Improve Quality (General)", "Upscale (Experimental)", "Fix Faces (Experimental)"]
            selected_ai_op = st.selectbox("Select AI Operation", ai_options, key="editor_ai_op")

            ai_strength = strength # Use the global strength slider by default
            if selected_ai_op == "Upscale (Experimental)":
                 # Upscaling often works better with lower strength to preserve details
                 ai_strength = st.slider("AI Influence Strength", 0.1, 1.0, 0.5, step=0.05, key="editor_ai_strength")
            elif selected_ai_op == "Fix Faces (Experimental)":
                 ai_strength = st.slider("AI Influence Strength", 0.1, 1.0, 0.7, step=0.05, key="editor_ai_strength")
            else:
                 ai_strength = st.slider("AI Influence Strength", 0.1, 1.0, strength, step=0.05, key="editor_ai_strength")


            if selected_ai_op != "None" and st.button("Apply AI Enhancement", key="editor_apply_ai"):
                with st.spinner(f"Applying AI Enhancement: {selected_ai_op}..."):
                    try:
                        # Use Img2Img for general enhancements
                        pipe, device = load_img2img_model(model_id)

                        prompt = ""
                        neg_prompt = "low quality, blurry, deformed, text, watermark, noise, grain"
                        if selected_ai_op == "Improve Quality (General)":
                            prompt = "enhance quality, clear, sharp focus, high resolution, professional photo"
                        elif selected_ai_op == "Upscale (Experimental)":
                            prompt = "upscale image, enhance details, 4k resolution, sharp, clear"
                            # Consider resizing image slightly *before* passing to model if needed
                        elif selected_ai_op == "Fix Faces (Experimental)":
                            prompt = "fix face, clear face details, realistic eyes, natural skin texture, correct features"
                            neg_prompt += ", blurry face, distorted face, extra limbs, disfigured"

                        # Process using Img2Img
                        ai_result_image, used_seed = process_img2img(
                            pipe,
                            st.session_state.edit_image_current, # Enhance the current state
                            prompt,
                            neg_prompt,
                            seed, # Use global seed or make it random? Maybe random is better here?
                            guidance_scale,
                            num_inference_steps,
                            ai_strength # Use the dedicated AI strength slider
                        )

                        if ai_result_image:
                            st.session_state.edit_image_current = ai_result_image
                            st.session_state.edit_history.append(ai_result_image.copy())
                            st.experimental_rerun()
                        else:
                            st.error("AI enhancement failed.")

                    except Exception as e:
                        st.error(f"Error during AI enhancement: {e}")

    elif uploaded_file is None:
        st.info("Upload an image to start editing.")