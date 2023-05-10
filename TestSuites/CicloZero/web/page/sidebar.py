import streamlit as st
from streamlit_option_menu import option_menu


def sidebar_header():
    """
    Show the sidebar header
    """
    with st.sidebar:
        # Logo
        st.image(st.secrets.paths.ciclozero_logo)
        _, col1, col2 = st.columns([1, 2, 1])
        col1.image(st.secrets.paths.logo)

        # Create a dropdown menu
        with st.expander('CiclAI', expanded=True):
            
            options = {"Stock": "box-seam", "Price": "cash-coin"}
            default_index = 0
            
            page_task = option_menu(
                menu_title=None,
                options=list(options.keys()),
                icons=list(options.values()),
                default_index=default_index
            )

        return page_task
