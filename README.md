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
```
AI-Image-Studio-app/
├── app.py                # Main Streamlit application file, routing, sidebar
├── config.py             # Configuration (paths, CSS, themes), setup
├── utils.py              # Utility functions (image handling, saving, history)
├── models.py             # Model loading functions (cached)
├── processing.py         # Core AI processing logic (inpainting, t2i, img2img)
├── projects.py           # Project loading/saving/deleting functions
├── modes/
│   ├── __init__.py
│   ├── inpainting.py     # UI and logic for Inpainting mode
│   ├── text2img.py       # UI and logic for Text-to-Image mode
│   ├── editor.py         # UI and logic for Image Editor mode
│   ├── restore.py        # UI and logic for Restoration mode
│   ├── batch.py          # UI and logic for Batch Processing mode
│   └── projects_display.py # UI for displaying projects in Project Manager
├── saved_images/         # Default directory for saved individual images
├── projects/             # Default directory for saved project JSON files & associated images
├── requirements.txt      # Python package dependencies
└── README.md             # This file
```
## 🚀 Setup and Installation

**Prerequisites:**

*   Python 3.8 or higher
*   `pip` and `venv` (usually included with Python)
*   Git
*   **(Strongly Recommended)** An NVIDIA GPU with CUDA installed for reasonable performance. CPU execution is possible but *very* slow for diffusion models. Ensure your PyTorch installation matches your CUDA version.

**Steps:**

1.  **Clone the repository:**
    ```bash
    git@github.com:vtnguyen04/AI-Image-Studio-app.git
    cd AI-Image-Studio-app
    ```

2.  **Create and activate a virtual environment:**
    *   **Linux/macOS:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    *   **Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```
    *   *Note:* This step might take a while, especially downloading PyTorch and Diffusers dependencies.
    *   *GPU Users:* If you have a specific CUDA version, you might need to install a specific PyTorch version first (check [PyTorch website](https://pytorch.org/get-started/locally/)). For example:
        ```bash
        # Example for CUDA 11.8
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
        pip install -r requirements.txt
        ```

## ▶️ Running the Application

1.  Make sure your virtual environment is activated (`(venv)` should be visible in your terminal prompt).
2.  Navigate to the project's root directory (where `app.py` is located).
3.  Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```
4.  Open your web browser and go to `http://localhost:8501` (or the URL provided in the terminal).


## 🖱️ Usage

1.  **Select Mode:** Use the sidebar radio buttons to choose the desired function (Inpainting, Text-to-Image, etc.).
2.  **Select Model:** Choose an appropriate AI model from the dropdown in the sidebar for the selected mode.
3.  **Adjust Parameters:** Configure generation settings like Steps, Guidance (CFG), Seed, and Strength in the sidebar.
4.  **Interact with Main Area:**
    *   Upload images, draw masks, or enter text prompts based on the selected mode.
    *   Use the mode-specific controls (e.g., filters in the editor, variations in batch).
    *   Click the "Generate" or relevant action button.
5.  **View Results:** Generated images or edited versions will appear in the main area.
6.  **Download/Save:** Use the download buttons or "Save to Library" options for individual images. Use ZIP download for batch results.
7.  **Save Project:** In modes that support it, enter a project name and click "Save Project" to store the parameters and associated images for later retrieval via the Project Manager.
8.  **Manage Projects:** Use the "Project Manager" mode to view, load details of, or delete saved projects.
9.  **View History:** The sidebar shows thumbnails and basic info for your last few generations in the current session.

## ⚙️ Configuration

*   **Image/Project Paths:** The default save locations (`saved_images/`, `projects/`) are defined in `config.py`. You can modify these paths if needed.
*   **Models:** Available models for each mode are defined within the sidebar logic in `app.py`. This could be moved to `config.py` for easier modification.
*   **CSS Styling:** Custom styles are applied via `config.apply_custom_css()`. Modify the CSS strings within that function to change the appearance.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.

Please ensure your code adheres to basic Python best practices and includes documentation where necessary.

## 📜 License

This project is licensed under the MIT License - see the `LICENSE` file for details (if you create one - otherwise, state the license here).

```txt
MIT License

Copyright (c) [2025] [Vo Thanh Nguyen]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.