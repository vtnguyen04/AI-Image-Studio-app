import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from streamlit_drawable_canvas import st_canvas
import uuid
import datetime
import os

from utils import resize_image, get_image_download_link, save_image_to_disk, add_to_history
from models import load_inpainting_model
from processing import process_inpainting
from projects import save_project, load_projects

def inpainting_app(model_id, seed, guidance_scale, num_inference_steps, strength):
    tabs = st.tabs(["✏️ Draw Mask", "📤 Upload Mask"])

    if 'uploaded_image' not in st.session_state:
        st.session_state.uploaded_image = None
    if 'mask_image' not in st.session_state:
        st.session_state.mask_image = None
    if 'result_image' not in st.session_state:
        st.session_state.result_image = None
    if 'last_seed_inpaint' not in st.session_state:
        st.session_state.last_seed_inpaint = seed

    current_image = None
    current_mask = None

    with tabs[0]:
        st.markdown('<div class="info-box">Upload an image and draw the area (in white) you want the AI to replace.</div>', unsafe_allow_html=True)
        uploaded_file_draw = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"], key="inpaint_upload_draw")

        if uploaded_file_draw is not None:
            try:
                image = Image.open(uploaded_file_draw).convert("RGB")
                # Resize to a manageable size for the canvas, divisible by 8
                canvas_width = 512 # Or calculate based on aspect ratio
                aspect_ratio = image.height / image.width
                canvas_height = int(canvas_width * aspect_ratio)
                canvas_height = (canvas_height // 8) * 8
                if canvas_height == 0: canvas_height = 8

                st.session_state.uploaded_image = image.resize((canvas_width, canvas_height), Image.LANCZOS)
                st.session_state.mask_image = None # Reset mask on new image
                st.session_state.result_image = None # Reset result

            except Exception as e:
                st.error(f"Error loading image: {e}")
                st.session_state.uploaded_image = None

        if st.session_state.uploaded_image:
            current_image = st.session_state.uploaded_image
            st.markdown("### Draw Mask (White = Area to Replace)")
            col1, col2 = st.columns([3, 1])
            with col1:
                 # Use a smaller fixed size or calculate based on original aspect ratio
                canvas_width = st.session_state.uploaded_image.width
                canvas_height = st.session_state.uploaded_image.height

                brush_size = st.slider("Brush size", 1, 50, 20, key="inpaint_brush")

                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0.0)", # Transparent fill initially
                    stroke_width=brush_size,
                    stroke_color="white",
                    background_image=st.session_state.uploaded_image,
                    update_streamlit=True, # Update automatically on draw
                    height=canvas_height,
                    width=canvas_width,
                    drawing_mode="freedraw",
                    key="inpaint_canvas",
                )

            with col2:
                if st.button("Clear Mask", key="clear_inpaint_mask"):
                    # Need to figure out how to reset canvas state without full rerun if possible
                    # For now, just trigger a rerun which clears it
                    st.experimental_rerun()

            if canvas_result.image_data is not None:
                # The canvas gives RGBA, we need the mask from the drawn parts (alpha or intensity)
                mask_data = canvas_result.image_data[:, :, 3] # Use alpha channel
                drawn_mask = Image.fromarray(mask_data).convert('L')
                current_mask = drawn_mask
                st.session_state.mask_image = current_mask # Store the drawn mask


    with tabs[1]:
        st.markdown('<div class="info-box">Upload both the original image and a separate black and white mask file (white areas = replace).</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file_img = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"], key="inpaint_upload_img_tab2")
            if uploaded_file_img is not None:
                try:
                    image = Image.open(uploaded_file_img).convert("RGB")
                    st.session_state.uploaded_image = resize_image(image) # Resize if needed
                    st.session_state.result_image = None # Reset result
                    st.image(st.session_state.uploaded_image, caption="Image for Inpainting", use_column_width=True)
                    current_image = st.session_state.uploaded_image
                except Exception as e:
                    st.error(f"Error loading image: {e}")
                    st.session_state.uploaded_image = None

        with col2:
            uploaded_file_mask = st.file_uploader("Upload mask (white = replace)", type=["png", "jpg", "jpeg"], key="inpaint_upload_mask_tab2")
            if uploaded_file_mask is not None and st.session_state.uploaded_image:
                try:
                    mask = Image.open(uploaded_file_mask).convert("L")
                     # Ensure mask matches image size
                    if mask.size != st.session_state.uploaded_image.size:
                         st.warning("Resizing mask to match image dimensions.")
                         mask = mask.resize(st.session_state.uploaded_image.size, Image.NEAREST) # Use NEAREST for masks
                    st.session_state.mask_image = mask
                    st.image(st.session_state.mask_image, caption="Uploaded Mask", use_column_width=True)
                    current_mask = st.session_state.mask_image
                except Exception as e:
                    st.error(f"Error loading mask: {e}")
                    st.session_state.mask_image = None


    # Use the determined image/mask from the active tab logic
    final_image_to_process = current_image if current_image else st.session_state.uploaded_image
    final_mask_to_process = current_mask if current_mask else st.session_state.mask_image


    if final_image_to_process is not None and final_mask_to_process is not None:
        st.markdown("---")
        st.markdown("### 💬 Describe what to generate in the masked area")
        col1, col2 = st.columns(2)
        with col1:
            prompt = st.text_area("Prompt", "A majestic dragon flying", height=100, key="inpaint_prompt")
        with col2:
            negative_prompt = st.text_area("Negative Prompt", "blurry, low quality, text, watermark, deformed", height=100, key="inpaint_neg_prompt")

        col_gen, col_var = st.columns(2)
        with col_gen:
            generate_button = st.button("🎨 Generate Inpainting", key="inpaint_generate")
        with col_var:
            variation_button = st.button("🎲 Generate Variation", key="inpaint_variation", disabled=st.session_state.result_image is None)


        if generate_button or variation_button:
             if final_image_to_process and final_mask_to_process:
                try:
                    with st.spinner("Loading inpainting model..."):
                        pipe, device = load_inpainting_model(model_id)

                    current_seed = np.random.randint(0, 2**32 - 1) if variation_button else seed
                    st.session_state.last_seed_inpaint = current_seed

                    # Resize image and mask *before* sending to pipeline if needed
                    # The pipeline might handle it, but explicit control can be better.
                    # Use a size compatible with the model (often 512x512 or 768x768)
                    # For now, assume `resize_image` handled basic sizing.
                    # Let's ensure they are divisible by 8, which is common for VAEs
                    width, height = final_image_to_process.size
                    target_width = (width // 8) * 8
                    target_height = (height // 8) * 8
                    if target_width == 0: target_width = 512 # Default fallback
                    if target_height == 0: target_height = 512

                    if final_image_to_process.size != (target_width, target_height):
                        st.write(f"Resizing input to {target_width}x{target_height} for model compatibility.")
                        img_to_process = final_image_to_process.resize((target_width, target_height), Image.LANCZOS)
                        mask_to_process = final_mask_to_process.resize((target_width, target_height), Image.NEAREST)
                    else:
                        img_to_process = final_image_to_process
                        mask_to_process = final_mask_to_process


                    result_image, used_seed = process_inpainting(
                        pipe,
                        img_to_process,
                        mask_to_process,
                        prompt,
                        negative_prompt,
                        current_seed,
                        guidance_scale,
                        num_inference_steps,
                        strength
                    )

                    st.session_state.last_seed_inpaint = used_seed

                    if result_image is not None:
                        st.session_state.result_image = result_image
                        # Automatically save to history is handled inside process_inpainting
                    else:
                        st.error("Inpainting generation failed.")

                except Exception as e:
                    st.error(f"Inpainting failed: {str(e)}")
             else:
                 st.warning("Please provide both an image and a mask.")


        if st.session_state.result_image is not None:
            st.markdown("---")
            st.markdown('<div class="result-container">', unsafe_allow_html=True)
            st.markdown("### ✨ Result")

            res_col1, res_col2, res_col3 = st.columns(3)
            with res_col1:
                 st.image(final_image_to_process, caption="Original", use_column_width=True)
            with res_col2:
                 # Display the mask used for generation
                 st.image(final_mask_to_process, caption="Mask Used", use_column_width=True)
            with res_col3:
                st.image(st.session_state.result_image, caption=f"Inpainted (Seed: {st.session_state.last_seed_inpaint})", use_column_width=True)

                st.markdown(
                    get_image_download_link(
                        st.session_state.result_image,
                        f'inpainted_seed_{st.session_state.last_seed_inpaint}.png',
                        '📥 Download Result'
                    ),
                    unsafe_allow_html=True
                )

                if st.button("💾 Save to Library", key="inpaint_save_lib"):
                    filepath = save_image_to_disk(st.session_state.result_image, "inpainted")
                    if filepath:
                        st.success(f"Image saved to {filepath}")

                st.markdown("</div>", unsafe_allow_html=True) # Close result-container

            # Save Project outside the result display columns
            st.markdown("---")
            project_name_inp = st.text_input("Save Project As:", key="inpaint_project_name", placeholder="e.g., Dragon Inpainting")
            if project_name_inp and st.button("💾 Save Project", key="inpaint_save_project"):
                 if final_image_to_process and final_mask_to_process and st.session_state.result_image:
                    orig_path = save_image_to_disk(final_image_to_process, f"{project_name_inp}_orig")
                    mask_path = save_image_to_disk(final_mask_to_process, f"{project_name_inp}_mask")
                    result_path = save_image_to_disk(st.session_state.result_image, f"{project_name_inp}_result")

                    if orig_path and mask_path and result_path:
                        project_data = {
                            "id": str(uuid.uuid4()),
                            "name": project_name_inp,
                            "type": "inpainting",
                            "date": datetime.datetime.now().isoformat(),
                            "params": {
                                "prompt": prompt,
                                "negative_prompt": negative_prompt,
                                "seed": st.session_state.last_seed_inpaint,
                                "guidance_scale": guidance_scale,
                                "strength": strength,
                                "steps": num_inference_steps,
                                "model_id": model_id,
                            },
                            "paths": {
                                "original": str(orig_path),
                                "mask": str(mask_path),
                                "result": str(result_path)
                            }
                        }
                        if save_project(project_name_inp, project_data):
                            st.session_state.projects = load_projects() # Refresh project list
                    else:
                        st.error("Failed to save one or more images for the project.")
                 else:
                     st.warning("Cannot save project without original image, mask, and result.")

    elif final_image_to_process is None:
        st.info("Upload an image to get started with inpainting.")