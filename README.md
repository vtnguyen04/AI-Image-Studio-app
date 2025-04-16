# 🎨 Advanced AI Image Studio

A versatile web application built with Streamlit and Hugging Face Diffusers, offering a suite of AI-powered tools for image generation, editing, and restoration.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](<#replace-with-your-deployed-app-link-if-available>) <!-- Optional: Add link if deployed -->

<!-- Optional: Add a screenshot or GIF demo -->
<!-- [Insert Screenshot/GIF Here] -->
<!-- (A visual demo significantly helps users understand the application) -->

## Overview

This application provides a user-friendly interface to leverage state-of-the-art diffusion models for various image manipulation tasks. Whether you want to generate images from text, seamlessly remove or replace objects (inpainting), enhance existing photos, restore old pictures, or process images in batches, this studio provides the tools you need.

## ✨ Features

*   **Multi-Mode Functionality:**
    *   **📝 Inpainting:** Remove or replace parts of an image using text prompts. Supports drawing masks directly or uploading mask files.
    *   **✨ Text-to-Image:** Generate images from detailed text descriptions, with optional style guidance.
    *   **🖼️ Image Editor:** Apply basic adjustments (brightness, contrast, etc.), filters (blur, sepia, etc.), and experimental AI enhancements (quality improvement, face fixing). Includes Undo functionality.
    *   **🔧 Restore Old Photo:** Attempt to repair scratches, noise, and fading in old photographs using AI.
    *   **📊 Batch Processing:**
        *   Apply the same inpainting mask and prompt to multiple images.
        *   Generate multiple text-to-image variations from a base prompt.
        *   Apply bulk AI enhancements to multiple images.
    *   **📁 Project Manager:** Save your work (inputs, outputs, parameters) as projects and reload them later.
*   **Model Selection:** Choose from various Stable Diffusion models (v1.5, v2.1, SDXL, Inpainting variants) suitable for each task.
*   **Adjustable Parameters:** Fine-tune generation with controls for Steps, Guidance Scale (CFG), Seed, and Strength (for relevant modes).
*   **Image Handling:** Upload images, download results individually or as ZIP archives (for batches).
*   **User Experience:** Interactive interface, history panel for recent generations, light/dark theme selection.
*   **Modular Codebase:** Organized into separate files for better maintainability.

## 💻 Technology Stack

*   **Framework:** Streamlit
*   **AI Models:** Hugging Face Diffusers library
*   **Core ML Library:** PyTorch
*   **Image Processing:** Pillow (PIL), NumPy
*   **Interactive Canvas:** streamlit-drawable-canvas
*   **Language:** Python 3

## 📂 Project Structure

The project is organized into modules for clarity: