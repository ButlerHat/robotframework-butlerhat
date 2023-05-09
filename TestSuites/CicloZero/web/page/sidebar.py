import streamlit as st
from streamlit_option_menu import option_menu


def sidebar_header():
    """
    Show the sidebar header
    """
    with st.sidebar:
        st.image(st.secrets.paths.logo)
        main_color = st.secrets.theme.primaryColor
        st.markdown(f'# Cicl<span style="color:{main_color}">AI</span> Price', unsafe_allow_html=True)

        # Create a dropdown menu
        with st.expander('Navigation', expanded=True):
            
            options = {"Stock": "box-seam", "Price": "cash-coin"}
            default_index = 0
            
            page_task = option_menu(
                menu_title=None,
                options=list(options.keys()),
                icons=list(options.values()),
                default_index=default_index
            )

        return page_task
