import streamlit as st
from PIL import Image
import os
import json

from projects import load_projects, load_project, delete_project # Use project utilities

def project_manager_app():
    st.markdown('<div class="info-box">Manage and revisit your saved AI image generation projects.</div>', unsafe_allow_html=True)

    if 'projects' not in st.session_state or not isinstance(st.session_state.get('projects'), list):
         st.session_state.projects = load_projects()
    if 'current_project_data' not in st.session_state: # Use a different name to avoid conflicts
         st.session_state.current_project_data = None

    if not st.session_state.projects:
        st.info("No projects found. Create images in other modes and use the 'Save Project' feature.")
        return

    project_tabs = st.tabs(["All Projects", "Inpainting", "Text-to-Image", "Restoration", "Batch"])

    with project_tabs[0]:
        display_project_list(st.session_state.projects)
    with project_tabs[1]:
        display_project_list(st.session_state.projects, "inpainting")
    with project_tabs[2]:
        display_project_list(st.session_state.projects, "text2img")
    with project_tabs[3]:
        display_project_list(st.session_state.projects, "restoration")
    with project_tabs[4]:
        display_project_list(st.session_state.projects, "batch")


    # Display details if a project is selected
    if st.session_state.current_project_data:
        st.markdown("---")
        st.subheader(f"Project Details: {st.session_state.current_project_data.get('name', 'Unnamed Project')}")
        display_project_details(st.session_state.current_project_data)


def display_project_list(project_names, filter_type=None):
    filtered_projects = []
    if filter_type:
        for name in project_names:
            # Load minimal data just to check type efficiently if possible
            # For now, load full data
            data = load_project(name)
            if data and data.get("type") == filter_type:
                filtered_projects.append(name)
    else:
        filtered_projects = project_names

    if not filtered_projects:
        st.caption(f"No {'projects' if not filter_type else filter_type + ' projects'} found.")
        return

    num_projects = len(filtered_projects)
    cols_per_row = 3
    rows = (num_projects + cols_per_row - 1) // cols_per_row

    for i in range(rows):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            project_index = i * cols_per_row + j
            if project_index < num_projects:
                project_name = filtered_projects[project_index]
                with cols[j]:
                    try:
                         # Use a container or card style
                         with st.container():
                              st.markdown(f'<div class="feature-card">', unsafe_allow_html=True)
                              st.markdown(f"**{project_name}**")
                              # Try loading just enough data for preview if optimization is needed
                              project_data = load_project(project_name)
                              if project_data:
                                   st.caption(f"Type: {project_data.get('type', 'N/A').capitalize()}")
                                   st.caption(f"Date: {project_data.get('date', 'N/A')[:10]}") # Show only date part

                                   # Display thumbnail/first image
                                   preview_path = None
                                   paths = project_data.get('paths', {})
                                   if isinstance(paths, dict): # Inpaint/Restore format
                                        preview_path = paths.get('result') or paths.get('original')
                                   elif isinstance(paths, list) and paths: # Text2Img/Batch format
                                        preview_path = paths[0]

                                   if preview_path and os.path.exists(preview_path):
                                        try:
                                             st.image(Image.open(preview_path), use_column_width=True, caption="Preview")
                                        except Exception as img_e:
                                             st.warning(f"Could not load preview: {img_e}")
                                   else:
                                        st.caption("No preview available.")

                                   if st.button("View Details", key=f"view_{project_name}"):
                                        st.session_state.current_project_data = project_data
                                        st.experimental_rerun() # Rerun to show details below

                              else:
                                   st.error(f"Could not load data for {project_name}")
                              st.markdown(f'</div>', unsafe_allow_html=True)

                    except Exception as e:
                         st.error(f"Error displaying project card for {project_name}: {e}")


def display_project_details(project_data):
     name = project_data.get('name', 'Unnamed')
     st.markdown(f"**Type:** {project_data.get('type', 'N/A').capitalize()}")
     st.markdown(f"**Date Created:** {project_data.get('date', 'N/A')}")
     st.markdown(f"**ID:** {project_data.get('id', 'N/A')}")

     with st.expander("Generation Parameters"):
          params = project_data.get('params', {})
          if params:
               # Use columns for better layout if many params
               param_cols = st.columns(2)
               i = 0
               for key, value in params.items():
                    col = param_cols[i % 2]
                    col.markdown(f"**{key.replace('_', ' ').capitalize()}:**")
                    # Handle potentially long values like prompts
                    if isinstance(value, str) and len(value) > 100:
                         col.text_area("", value, height=80, key=f"param_{name}_{key}", disabled=True)
                    else:
                         col.code(str(value), language='json')
                    i += 1
          else:
               st.caption("No parameters saved for this project.")

     st.markdown("#### Project Files")
     paths = project_data.get('paths', {})

     if isinstance(paths, dict): # Inpainting, Restoration
          st.markdown("##### Images:")
          cols = st.columns(len(paths))
          i = 0
          for key, path_str in paths.items():
               if path_str and os.path.exists(path_str):
                    try:
                         with cols[i]:
                              st.image(Image.open(path_str), caption=key.capitalize(), use_column_width=True)
                    except Exception as e:
                         st.warning(f"Could not load image '{key}': {e}")
               elif path_str:
                    st.warning(f"File not found for '{key}': {path_str}")
               i += 1

     elif isinstance(paths, list): # Text2Img, Batch
          st.markdown(f"##### Generated Images ({len(paths)}):")
          cols = st.columns(min(3, len(paths)))
          for i, path_str in enumerate(paths):
               if path_str and os.path.exists(path_str):
                    try:
                         with cols[i % len(cols)]:
                              st.image(Image.open(path_str), caption=f"Image {i+1}", use_column_width=True)
                    except Exception as e:
                         st.warning(f"Could not load image {i+1}: {e}")
               elif path_str:
                     st.warning(f"File not found for Image {i+1}: {path_str}")

     else:
          st.caption("No file paths found in project data.")

     st.markdown("---")
     col_b1, col_b2 = st.columns([1,5]) # Give more space to delete button message
     with col_b1:
         if st.button("Close Details", key=f"close_{name}"):
              st.session_state.current_project_data = None
              st.experimental_rerun()
     with col_b2:
         if st.button(f"🗑️ Delete Project '{name}'", key=f"delete_{name}"):
             confirm_placeholder = st.empty()
             with confirm_placeholder.container():
                  st.warning(f"**Are you sure you want to delete project '{name}'?** This cannot be undone.")
                  c1, c2 = st.columns(2)
                  if c1.button("Yes, Delete Permanently", key=f"confirm_delete_{name}"):
                       if delete_project(name):
                            st.session_state.projects = load_projects() # Refresh list
                            st.session_state.current_project_data = None # Close details
                       confirm_placeholder.empty() # Clear confirmation
                       st.experimental_rerun()
                  if c2.button("Cancel", key=f"cancel_delete_{name}"):
                       confirm_placeholder.empty() # Clear confirmation