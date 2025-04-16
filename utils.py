import streamlit as st
import io
import base64
import datetime
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
from config import SAVE_DIR

def resize_image(image, max_size=512):
    try:
        width, height = image.size
        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            # Ensure dimensions are divisible by 8 for some models
            new_width = (new_width // 8) * 8
            new_height = (new_height // 8) * 8
            if new_width == 0: new_width = 8
            if new_height == 0: new_height = 8
            return image.resize((new_width, new_height), Image.LANCZOS)
        return image
    except Exception as e:
        st.error(f"Error resizing image: {e}")
        return image # Return original if resizing fails


def get_image_download_link(img, filename, text):
    buffered = io.BytesIO()
    try:
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        href = f'<a href="data:image/png;base64,{img_str}" download="{filename}" style="background-color:#3b82f6;color:white;padding:8px 16px;text-decoration:none;border-radius:4px;font-weight:bold;">{text}</a>'
        return href
    except Exception as e:
        st.error(f"Error creating download link: {e}")
        return ""


def save_image_to_disk(img, prefix="ai_image"):
    try:
        filename = f"{prefix}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        filepath = SAVE_DIR / filename
        img.save(filepath)
        return filepath
    except Exception as e:
        st.error(f"Error saving image to disk: {e}")
        return None


def add_to_history(mode, image, prompt):
    if 'history' not in st.session_state:
        st.session_state.history = []
    try:
        thumbnail = image.copy()
        thumbnail.thumbnail((100, 100))

        entry = {
            "mode": mode,
            "image": image,
            "thumbnail": thumbnail,
            "prompt": prompt,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.history.append(entry)
    except Exception as e:
        st.warning(f"Could not add item to history: {e}")

def apply_basic_adjustments(image, brightness, contrast, sharpness, saturation):
    edited_img = image.copy()
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(edited_img)
        edited_img = enhancer.enhance(brightness)
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(edited_img)
        edited_img = enhancer.enhance(contrast)
    if sharpness != 1.0:
        enhancer = ImageEnhance.Sharpness(edited_img)
        edited_img = enhancer.enhance(sharpness)
    if saturation != 1.0:
        enhancer = ImageEnhance.Color(edited_img)
        edited_img = enhancer.enhance(saturation)
    return edited_img

def apply_filter(image, filter_name, intensity=1.0):
    edited_img = image.copy()
    try:
        if filter_name == "Blur":
            edited_img = edited_img.filter(ImageFilter.GaussianBlur(radius=intensity))
        elif filter_name == "Sharpen":
            edited_img = edited_img.filter(ImageFilter.UnsharpMask(radius=intensity, percent=150))
        elif filter_name == "Grayscale":
            edited_img = edited_img.convert("L").convert("RGB")
        elif filter_name == "Sepia":
            grayscale = edited_img.convert("L")
            sepia_img = Image.new("RGB", edited_img.size)
            r_tint, g_tint, b_tint = (255 * 0.393 + 255 * 0.769 + 255 * 0.189,
                                      255 * 0.349 + 255 * 0.686 + 255 * 0.168,
                                      255 * 0.272 + 255 * 0.534 + 255 * 0.131)
            scale = intensity / 1.0 # Simple intensity scaling

            sepia_pixels = np.array(grayscale).astype(float)
            sepia_pixels = np.dot(sepia_pixels[...,None], [[r_tint/255, g_tint/255, b_tint/255]]) * scale
            sepia_pixels = np.clip(sepia_pixels, 0, 255).astype(np.uint8)
            edited_img = Image.fromarray(sepia_pixels)

        elif filter_name == "Edge Enhance":
            edited_img = edited_img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        elif filter_name == "Emboss":
            edited_img = edited_img.filter(ImageFilter.EMBOSS)
    except Exception as e:
        st.error(f"Error applying filter '{filter_name}': {e}")
        return image # Return original on error
    return edited_img