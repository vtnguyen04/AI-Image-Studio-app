import streamlit as st
import torch
from diffusers import StableDiffusionInpaintPipeline, StableDiffusionPipeline, StableDiffusionImg2ImgPipeline

@st.cache_resource
def load_pipeline(pipeline_class, model_id):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if device == "cuda" else torch.float32
    st.write(f"Loading {pipeline_class.__name__} for {model_id} on {device}...")

    try:
        pipe = pipeline_class.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            use_safetensors=True,
            variant="fp16" if torch_dtype == torch.float16 else None # Common variant for fp16 models
        )
    except (OSError, ValueError, EnvironmentError) as e1:
        st.warning(f"Could not load with safetensors/fp16 variant ({e1}). Trying without.")
        try:
            pipe = pipeline_class.from_pretrained(
                model_id,
                torch_dtype=torch_dtype,
                use_safetensors=False
            )
        except Exception as e2:
            st.error(f"Failed to load model {model_id}. Error: {e2}")
            st.stop() # Stop execution if model fails to load


    pipe = pipe.to(device)

    # Optional: Enable memory optimizations if on CUDA
    if device == "cuda":
        try:
            pipe.enable_model_cpu_offload() # Reduces VRAM usage significantly
            # pipe.enable_xformers_memory_efficient_attention() # Can speed up but needs xformers installed
            st.write("Enabled CPU offloading for model.")
        except AttributeError:
            st.write("CPU offloading not available for this pipeline.")
        except ImportError:
            st.write("xformers not installed, memory efficient attention disabled.")


    if hasattr(pipe, 'safety_checker') and pipe.safety_checker is not None:
        # It's generally recommended to keep the safety checker unless you have specific reasons.
        # pipe.safety_checker = None
        # st.warning("Safety checker disabled for this model.")
        pass # Keep safety checker by default

    return pipe, device

def load_inpainting_model(model_id):
    return load_pipeline(StableDiffusionInpaintPipeline, model_id)

def load_text2img_model(model_id):
    return load_pipeline(StableDiffusionPipeline, model_id)

def load_img2img_model(model_id):
    return load_pipeline(StableDiffusionImg2ImgPipeline, model_id)