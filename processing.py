import streamlit as st
import torch
import numpy as np
from PIL import Image
from utils import add_to_history

def process_inpainting(pipe, image, mask_image, prompt, negative_prompt, seed, guidance_scale, num_inference_steps, strength):
    if not pipe:
        st.error("Inpainting model not loaded.")
        return None, seed

    if seed == -1:
        seed = np.random.randint(0, 2**32 - 1)

    generator = torch.Generator(device=pipe.device).manual_seed(seed)

    mask_image_l = mask_image.convert("L")

    mask_array = np.array(mask_image_l)
    if np.mean(mask_array) < 127: # If mostly black, invert (assume user painted area to keep)
         mask_image_l = Image.fromarray(255 - mask_array)

    # Ensure image and mask are same size
    if image.size != mask_image_l.size:
        st.warning(f"Image ({image.size}) and mask ({mask_image_l.size}) sizes differ. Resizing mask to image size.")
        mask_image_l = mask_image_l.resize(image.size)


    with st.spinner("🎨 AI is working on your image (Inpainting)..."):
        try:
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=image,
                mask_image=mask_image_l,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                strength=strength,
                generator=generator
            )

            if result.images and len(result.images) > 0:
                 output_image = result.images[0]
                 add_to_history("inpaint", output_image, prompt)
                 return output_image, seed
            else:
                 st.error("Inpainting failed to produce an image.")
                 return None, seed

        except Exception as e:
            st.error(f"Error during inpainting: {str(e)}")
            st.info("Try reducing image size, adjusting strength/steps, or using a different model.")
            return None, seed

def process_text2img(pipe, prompt, negative_prompt, seed, guidance_scale, num_inference_steps, width, height, num_images=1):
    if not pipe:
        st.error("Text-to-Image model not loaded.")
        return None, seed

    if seed == -1:
        seed = np.random.randint(0, 2**32 - 1)

    generator = torch.Generator(device=pipe.device).manual_seed(seed)

    with st.spinner("✨ AI is generating your images (Text2Img)..."):
        try:
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                num_images_per_prompt=num_images,
                generator=generator
            )

            if result.images:
                if num_images == 1:
                    add_to_history("text2img", result.images[0], prompt)
                return result.images, seed
            else:
                st.error("Text-to-Image generation failed to produce images.")
                return None, seed

        except Exception as e:
            st.error(f"Error during Text-to-Image generation: {str(e)}")
            return None, seed


def process_img2img(pipe, image, prompt, negative_prompt, seed, guidance_scale, num_inference_steps, strength):
    if not pipe:
        st.error("Image-to-Image model not loaded.")
        return None, seed

    if seed == -1:
        seed = np.random.randint(0, 2**32 - 1)

    generator = torch.Generator(device=pipe.device).manual_seed(seed)

    # Ensure image is RGB
    image = image.convert("RGB")

    with st.spinner("🤖 AI is processing your image (Img2Img)..."):
        try:
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=image,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                strength=strength,
                generator=generator
            )

            if result.images and len(result.images) > 0:
                output_image = result.images[0]
                # Decide if img2img should go to general history
                # add_to_history("img2img", output_image, prompt)
                return output_image, seed
            else:
                st.error("Img2Img processing failed to produce an image.")
                return None, seed

        except Exception as e:
            st.error(f"Error during Img2Img processing: {str(e)}")
            st.info("Try adjusting strength, image size, or using a different model.")
            return None, seed