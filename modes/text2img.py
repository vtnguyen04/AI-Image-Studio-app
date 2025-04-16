import streamlit as st
import numpy as np
import uuid
import datetime

from utils import get_image_download_link, save_image_to_disk, add_to_history
from models import load_text2img_model
from processing import process_text2img
from projects import save_project, load_projects

def text2img_app(model_id, seed, guidance_scale, num_inference_steps, width, height, num_images):
    st.markdown('<div class="info-box">Generate images directly from your text descriptions.</div>', unsafe_allow_html=True)

    if 'last_seed_text2img' not in st.session_state:
        st.session_state.last_seed_text2img = seed
    if 'generated_text_images' not in st.session_state: # Changed name for clarity
        st.session_state.generated_text_images = []

    st.markdown("### 💬 Describe the image you want")
    prompt = st.text_area("Prompt", "Epic landscape, fantasy art, mountains, river, detailed, sharp focus, trending on artstation", height=120, key="t2i_prompt")
    negative_prompt = st.text_area("Negative Prompt (optional)", "ugly, blurry, deformed, text, watermark, low quality, noisy", height=100, key="t2i_neg_prompt")

    st.markdown("### 🎭 Style Guidance (Optional)")
    style_options = ["None", "Photorealistic", "Digital Art", "Oil Painting", "Anime", "Sketch", "Watercolor", "3D Render", "Pixel Art", "Cyberpunk"]
    selected_style = st.selectbox("Select Art Style", style_options, key="t2i_style")

    style_prompt_text = ""
    if selected_style != "None":
        style_prompts = {
            "Photorealistic": ", photorealistic, 8k, high detail, sharp focus, professional photography, Canon EOS R5",
            "Digital Art": ", digital art, detailed, vibrant colors, concept art, illustration, trending on artstation",
            "Oil Painting": ", oil painting, rich colors, impasto, detailed brushwork, canvas texture, masterpiece",
            "Anime": ", anime style, vibrant, clean lines, studio ghibli inspired, 2D animation",
            "Sketch": ", pencil sketch, detailed lines, monochrome, hand-drawn, hatching, cross-hatching",
            "Watercolor": ", watercolor painting, soft edges, blended colors, wet-on-wet technique, paper texture",
            "3D Render": ", 3D render, octane render, unreal engine 5, cinematic lighting, ray tracing, hyperrealistic",
            "Pixel Art": ", pixel art, 16-bit, detailed sprite, vibrant palette, retro game style",
            "Cyberpunk": ", cyberpunk style, neon lights, futuristic city, dystopian, high tech low life, blade runner"
        }
        style_prompt_text = style_prompts.get(selected_style, "")

    final_prompt = prompt + style_prompt_text

    col1, col2 = st.columns(2)
    with col1:
        generate_button = st.button("✨ Generate Images", key="t2i_generate")
    with col2:
        variation_button = st.button("🎲 Generate Variations", key="t2i_variation", disabled=not st.session_state.generated_text_images)


    if generate_button or variation_button:
        try:
            with st.spinner("Loading text-to-image model..."):
                pipe, device = load_text2img_model(model_id)

            current_seed = np.random.randint(0, 2**32 - 1) if variation_button else seed
            st.session_state.last_seed_text2img = current_seed

            images, used_seed = process_text2img(
                pipe,
                final_prompt,
                negative_prompt,
                current_seed,
                guidance_scale,
                num_inference_steps,
                width,
                height,
                num_images
            )

            st.session_state.last_seed_text2img = used_seed

            if images:
                st.session_state.generated_text_images = images
                # History is added within process_text2img if num_images == 1
            else:
                st.error("Image generation failed.")
                st.session_state.generated_text_images = []

        except Exception as e:
            st.error(f"Text-to-Image generation failed: {str(e)}")
            st.session_state.generated_text_images = []

    if st.session_state.generated_text_images:
        st.markdown("---")
        st.markdown('<div class="result-container">', unsafe_allow_html=True)
        st.markdown(f"### ✨ Generated Images (Seed: {st.session_state.last_seed_text2img})")

        cols = st.columns(min(num_images, 4)) # Max 4 columns
        for idx, img in enumerate(st.session_state.generated_text_images):
            col = cols[idx % len(cols)]
            with col:
                st.image(img, use_column_width=True, output_format='PNG')
                st.markdown(
                    get_image_download_link(
                        img,
                        f't2i_{idx}_seed_{st.session_state.last_seed_text2img}.png',
                        '📥 Download'
                    ),
                    unsafe_allow_html=True
                )
                if st.button(f"💾 Save #{idx+1}", key=f"t2i_save_lib_{idx}"):
                    filepath = save_image_to_disk(img, f"text2img_{idx}")
                    if filepath:
                        st.success(f"Image #{idx+1} saved to library.")

        st.markdown("</div>", unsafe_allow_html=True) # Close result-container

        # Save Project
        st.markdown("---")
        project_name_t2i = st.text_input("Save Batch as Project:", key="t2i_project_name", placeholder="e.g., Fantasy Landscapes")
        if project_name_t2i and st.button("💾 Save Project", key="t2i_save_project"):
            image_paths = []
            success = True
            for idx, img in enumerate(st.session_state.generated_text_images):
                path = save_image_to_disk(img, f"{project_name_t2i}_{idx}")
                if path:
                    image_paths.append(str(path))
                else:
                    success = False
                    st.error(f"Failed to save image #{idx+1} for project.")
                    break

            if success and image_paths:
                project_data = {
                    "id": str(uuid.uuid4()),
                    "name": project_name_t2i,
                    "type": "text2img",
                    "date": datetime.datetime.now().isoformat(),
                    "params": {
                        "prompt": prompt, # Save original prompt without style
                        "negative_prompt": negative_prompt,
                        "style": selected_style,
                        "seed": st.session_state.last_seed_text2img,
                        "guidance_scale": guidance_scale,
                        "steps": num_inference_steps,
                        "width": width,
                        "height": height,
                        "num_images": len(image_paths), # Actual number saved
                        "model_id": model_id,
                    },
                    "paths": image_paths
                }
                if save_project(project_name_t2i, project_data):
                     st.session_state.projects = load_projects() # Refresh project list