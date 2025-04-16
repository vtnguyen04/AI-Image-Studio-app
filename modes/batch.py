import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from streamlit_drawable_canvas import st_canvas
import io
import zipfile
import base64
import uuid
import datetime

from utils import resize_image, save_image_to_disk
from models import load_inpainting_model, load_text2img_model
from processing import process_inpainting, process_text2img
from projects import save_project, load_projects

def batch_processing_app(model_id, seed, guidance_scale, num_inference_steps, strength, width, height):
    st.markdown('<div class="info-box">Process multiple images or generate variations with consistent settings.</div>', unsafe_allow_html=True)

    if 'batch_op_type' not in st.session_state:
        st.session_state.batch_op_type = "Inpainting (Uniform Mask)"
    if 'batch_images_input' not in st.session_state:
        st.session_state.batch_images_input = []
    if 'batch_mask_input' not in st.session_state:
        st.session_state.batch_mask_input = None
    if 'batch_results_output' not in st.session_state:
        st.session_state.batch_results_output = []
    if 'batch_last_run_params' not in st.session_state:
         st.session_state.batch_last_run_params = {}

    operation_options = [
        "Inpainting (Uniform Mask)",
        "Text-to-Image Variations",
        "Bulk Image Enhancement (Img2Img)"
    ]
    st.session_state.batch_op_type = st.selectbox(
        "Select Batch Operation",
        operation_options,
        index=operation_options.index(st.session_state.batch_op_type), # Maintain selection
        key="batch_op_selector"
    )
    operation_type = st.session_state.batch_op_type


    # --- UI based on Operation Type ---
    if operation_type == "Inpainting (Uniform Mask)":
        batch_inpainting_ui(model_id, seed, guidance_scale, num_inference_steps, strength)
    elif operation_type == "Text-to-Image Variations":
        batch_text2img_ui(model_id, seed, guidance_scale, num_inference_steps, width, height)
    elif operation_type == "Bulk Image Enhancement (Img2Img)":
        batch_enhancement_ui(model_id, seed, guidance_scale, num_inference_steps, strength)

    # --- Display Results ---
    if st.session_state.batch_results_output:
        st.markdown("---")
        st.markdown("### Batch Results")

        cols = st.columns(min(4, len(st.session_state.batch_results_output)))
        for i, result in enumerate(st.session_state.batch_results_output):
            col = cols[i % len(cols)]
            with col:
                st.image(result, caption=f"Result {i+1}", use_column_width=True)

        st.markdown("---")
        col_dl, col_save = st.columns(2)
        with col_dl:
            if st.button("📥 Download All as ZIP", key="batch_download_zip"):
                zip_buffer = io.BytesIO()
                try:
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for i, img in enumerate(st.session_state.batch_results_output):
                            img_buffer = io.BytesIO()
                            img.save(img_buffer, format="PNG")
                            zip_file.writestr(f"result_{i+1}.png", img_buffer.getvalue())

                    zip_buffer.seek(0)
                    b64 = base64.b64encode(zip_buffer.read()).decode()
                    href = f'<a href="data:application/zip;base64,{b64}" download="batch_results.zip" style="background-color:#3b82f6;color:white;padding:8px 16px;text-decoration:none;border-radius:4px;font-weight:bold;">Click to Download ZIP</a>'
                    st.markdown(href, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Failed to create ZIP file: {e}")

        with col_save:
            project_name_batch = st.text_input("Save Batch as Project:", key="batch_project_name", placeholder="e.g., Batch Inpaint Run")
            if project_name_batch and st.button("💾 Save Batch Project", key="batch_save_project"):
                image_paths = []
                success = True
                for i, img in enumerate(st.session_state.batch_results_output):
                    filepath = save_image_to_disk(img, f"{project_name_batch}_{i+1}")
                    if filepath:
                        image_paths.append(str(filepath))
                    else:
                        success = False
                        st.error(f"Failed to save image #{i+1} for project.")
                        break

                if success and image_paths:
                    project_data = {
                        "id": str(uuid.uuid4()),
                        "name": project_name_batch,
                        "type": "batch",
                        "operation": st.session_state.batch_last_run_params.get('operation_type', 'unknown'),
                        "date": datetime.datetime.now().isoformat(),
                        "params": st.session_state.batch_last_run_params, # Store params used for this run
                        "paths": image_paths
                    }
                    if save_project(project_name_batch, project_data):
                        st.session_state.projects = load_projects() # Refresh list

# --- Specific UI and Logic Functions ---

def batch_inpainting_ui(model_id, seed, guidance_scale, num_inference_steps, strength):
    st.markdown("### 1. Upload Images")
    uploaded_files = st.file_uploader("Upload images for batch inpainting", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="batch_inpaint_upload")

    if uploaded_files:
        new_images = []
        for uploaded_file in uploaded_files:
            try:
                image = Image.open(uploaded_file).convert("RGB")
                new_images.append(resize_image(image)) # Resize for consistency
            except Exception as e:
                st.warning(f"Could not load {uploaded_file.name}: {e}")
        if new_images:
             st.session_state.batch_images_input = new_images
             st.session_state.batch_results_output = [] # Clear old results

    if st.session_state.batch_images_input:
        st.markdown(f"**{len(st.session_state.batch_images_input)} images loaded.**")
        # Display thumbnails
        cols = st.columns(min(len(st.session_state.batch_images_input), 6))
        for i, img in enumerate(st.session_state.batch_images_input[:6]):
            cols[i].image(img, width=100)
        if len(st.session_state.batch_images_input) > 6:
             st.write(f"... and {len(st.session_state.batch_images_input)-6} more.")

        st.markdown("### 2. Create or Upload Mask")
        st.caption("This mask will be applied to *all* images in the batch.")

        mask_method = st.radio("Mask Source", ["Draw on first image", "Upload mask file"], key="batch_inpaint_mask_source")

        temp_mask = None
        if mask_method == "Draw on first image":
            img_for_canvas = st.session_state.batch_images_input[0]
            st.write("Draw mask (white = area to replace):")
            brush_size = st.slider("Brush size", 1, 50, 20, key="batch_inpaint_brush")
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0.0)",
                stroke_width=brush_size, stroke_color="white",
                background_image=img_for_canvas, update_streamlit=True,
                height=img_for_canvas.height, width=img_for_canvas.width,
                drawing_mode="freedraw", key="batch_inpaint_canvas"
            )
            if canvas_result.image_data is not None:
                mask_data = canvas_result.image_data[:, :, 3]
                temp_mask = Image.fromarray(mask_data).convert('L')
        else:
            mask_file = st.file_uploader("Upload mask file (white = replace)", type=["png", "jpg", "jpeg"], key="batch_inpaint_mask_upload")
            if mask_file:
                try:
                     temp_mask = Image.open(mask_file).convert("L")
                     st.image(temp_mask, caption="Uploaded Mask", width=200)
                except Exception as e:
                     st.error(f"Error loading mask file: {e}")

        st.session_state.batch_mask_input = temp_mask # Store the potential mask

        if st.session_state.batch_mask_input:
            st.markdown("### 3. Set Inpainting Parameters")
            prompt = st.text_area("Prompt (applied to all)", "A beautiful sunset", key="batch_inpaint_prompt")
            negative_prompt = st.text_area("Negative Prompt (applied to all)", "blurry, low quality, text", key="batch_inpaint_neg_prompt")

            if st.button("🎨 Process Batch Inpainting", key="batch_inpaint_process"):
                 if not st.session_state.batch_images_input or st.session_state.batch_mask_input is None:
                      st.warning("Please upload images and provide a mask.")
                      return

                 st.session_state.batch_results_output = []
                 progress_bar = st.progress(0.0)
                 status_text = st.empty()
                 try:
                      with st.spinner("Loading inpainting model..."):
                           pipe, device = load_inpainting_model(model_id)

                      total_images = len(st.session_state.batch_images_input)
                      for i, img in enumerate(st.session_state.batch_images_input):
                           status_text.text(f"Processing image {i+1}/{total_images}...")

                           # Resize mask to match current image
                           resized_mask = st.session_state.batch_mask_input.resize(img.size, Image.NEAREST)

                           # Ensure mask is inverted correctly (white = inpaint)
                           mask_array = np.array(resized_mask)
                           if np.mean(mask_array) < 127: # Mostly black means user likely painted area to *keep*
                                mask_to_use = Image.fromarray(255 - mask_array)
                           else:
                                mask_to_use = resized_mask

                           # Use unique seed per image if master seed is random, else increment
                           img_seed = (seed + i) if seed != -1 else np.random.randint(0, 2**32 - 1)

                           result, _ = process_inpainting(
                                pipe, img, mask_to_use, prompt, negative_prompt,
                                img_seed, guidance_scale, num_inference_steps, strength
                           )
                           if result:
                                st.session_state.batch_results_output.append(result)
                           else:
                                st.warning(f"Failed to process image {i+1}.")
                           progress_bar.progress((i + 1) / total_images)

                      status_text.success(f"Batch inpainting complete! Processed {len(st.session_state.batch_results_output)} images.")
                      # Store params for potential project save
                      st.session_state.batch_last_run_params = {
                           'operation_type': 'Inpainting (Uniform Mask)', 'prompt': prompt, 'negative_prompt': negative_prompt,
                           'seed': seed, 'guidance_scale': guidance_scale, 'steps': num_inference_steps, 'strength': strength, 'model_id': model_id,
                           'num_images': len(st.session_state.batch_results_output)
                           }
                 except Exception as e:
                      status_text.error(f"Batch inpainting failed: {e}")

def batch_text2img_ui(model_id, seed, guidance_scale, num_inference_steps, width, height):
    st.markdown("### 1. Base Prompt")
    base_prompt = st.text_area("Base Prompt (common part)", "photo of a cute cat", key="batch_t2i_base")
    negative_prompt = st.text_area("Negative Prompt (common part)", "ugly, deformed, blurry", key="batch_t2i_neg")

    st.markdown("### 2. Variations")
    variations_text = st.text_area("Add variations (one per line)",
                                   "wearing a party hat\nsleeping in a basket\nchasing a laser pointer\nlooking out a window",
                                   height=150, key="batch_t2i_vars")
    variation_list = [line.strip() for line in variations_text.split('\n') if line.strip()]

    if variation_list:
        st.markdown("### 3. Preview Prompts")
        with st.expander("Show Prompts To Be Generated"):
            for i, var in enumerate(variation_list):
                st.write(f"{i+1}. `{base_prompt}, {var}`")

    if st.button("✨ Generate Batch Variations", key="batch_t2i_process", disabled=not variation_list):
        st.session_state.batch_results_output = []
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        try:
            with st.spinner("Loading text-to-image model..."):
                pipe, device = load_text2img_model(model_id)

            total_variations = len(variation_list)
            for i, var in enumerate(variation_list):
                 status_text.text(f"Generating variation {i+1}/{total_variations}...")
                 full_prompt = f"{base_prompt}, {var}"

                 img_seed = (seed + i) if seed != -1 else np.random.randint(0, 2**32 - 1)

                 results, _ = process_text2img(
                      pipe, full_prompt, negative_prompt, img_seed,
                      guidance_scale, num_inference_steps, width, height, num_images=1
                 )
                 if results:
                      st.session_state.batch_results_output.append(results[0])
                 else:
                      st.warning(f"Failed to generate variation {i+1}.")
                 progress_bar.progress((i + 1) / total_variations)

            status_text.success(f"Generated {len(st.session_state.batch_results_output)} variations!")
            # Store params
            st.session_state.batch_last_run_params = {
                 'operation_type': 'Text-to-Image Variations', 'base_prompt': base_prompt, 'negative_prompt': negative_prompt,
                 'variations': variation_list, 'seed': seed, 'guidance_scale': guidance_scale, 'steps': num_inference_steps,
                 'width': width, 'height': height, 'model_id': model_id, 'num_images': len(st.session_state.batch_results_output)
            }
        except Exception as e:
            status_text.error(f"Batch generation failed: {e}")

def batch_enhancement_ui(model_id, seed, guidance_scale, num_inference_steps, strength):
    st.markdown("### 1. Upload Images for Enhancement")
    uploaded_files = st.file_uploader("Upload images for enhancement", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="batch_enhance_upload")

    if uploaded_files:
        new_images = []
        for uploaded_file in uploaded_files:
             try:
                  image = Image.open(uploaded_file).convert("RGB")
                  # Resize slightly if needed, maybe larger max size for enhancement
                  new_images.append(resize_image(image, max_size=1024))
             except Exception as e:
                  st.warning(f"Could not load {uploaded_file.name}: {e}")
        if new_images:
             st.session_state.batch_images_input = new_images
             st.session_state.batch_results_output = []

    if st.session_state.batch_images_input:
        st.markdown(f"**{len(st.session_state.batch_images_input)} images loaded.**")
        cols = st.columns(min(len(st.session_state.batch_images_input), 6))
        for i, img in enumerate(st.session_state.batch_images_input[:6]):
             cols[i].image(img, width=100)
        if len(st.session_state.batch_images_input) > 6:
             st.write(f"... and {len(st.session_state.batch_images_input)-6} more.")

        st.markdown("### 2. Enhancement Settings")
        enhancement_prompt = st.text_area("Enhancement Prompt (applied to all)",
                                         "enhance quality, sharp focus, clear details, high resolution, professional photograph",
                                         key="batch_enhance_prompt")
        negative_prompt = st.text_area("Negative Prompt (applied to all)", "blurry, noisy, low quality, text, watermark, deformed", key="batch_enhance_neg_prompt")

        # Use the main strength slider passed as an argument
        st.markdown(f"**Enhancement Strength:** `{strength:.2f}` (Sidebar Setting)")
        st.caption("Controls how much the AI alters the original image based on the prompt.")

        if st.button("✨ Enhance Batch Images", key="batch_enhance_process"):
            st.session_state.batch_results_output = []
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            try:
                with st.spinner("Loading enhancement model (Img2Img)..."):
                    # Use Img2Img model for enhancement
                    pipe, device = load_img2img_model(model_id)

                total_images = len(st.session_state.batch_images_input)
                for i, img in enumerate(st.session_state.batch_images_input):
                    status_text.text(f"Enhancing image {i+1}/{total_images}...")

                    # Resize for model compatibility if needed
                    width, height = img.size
                    target_width = (width // 8) * 8
                    target_height = (height // 8) * 8
                    if target_width == 0: target_width = 512
                    if target_height == 0: target_height = 512

                    img_to_process = img
                    if img.size != (target_width, target_height):
                        img_to_process = img.resize((target_width, target_height), Image.LANCZOS)

                    img_seed = (seed + i) if seed != -1 else np.random.randint(0, 2**32 - 1)

                    # Call process_img2img
                    result, _ = process_img2img(
                        pipe, img_to_process, enhancement_prompt, negative_prompt,
                        img_seed, guidance_scale, num_inference_steps, strength
                    )
                    if result:
                        # Optionally resize back to original aspect ratio if needed?
                        # For now, keep the processed size.
                        st.session_state.batch_results_output.append(result)
                    else:
                        st.warning(f"Failed to enhance image {i+1}.")
                    progress_bar.progress((i + 1) / total_images)

                status_text.success(f"Batch enhancement complete! Processed {len(st.session_state.batch_results_output)} images.")
                 # Store params
                st.session_state.batch_last_run_params = {
                     'operation_type': 'Bulk Image Enhancement (Img2Img)', 'prompt': enhancement_prompt, 'negative_prompt': negative_prompt,
                     'seed': seed, 'guidance_scale': guidance_scale, 'steps': num_inference_steps, 'strength': strength, 'model_id': model_id,
                     'num_images': len(st.session_state.batch_results_output)
                     }
            except Exception as e:
                 status_text.error(f"Batch enhancement failed: {e}")