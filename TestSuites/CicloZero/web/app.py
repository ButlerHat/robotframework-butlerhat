import streamlit as st
from page.sidebar import sidebar_header
from page.ciclai_stock import ciclai_stock
from page.ciclai_price import ciclai_price

st.set_page_config(
    page_title="CiclAI",
    page_icon=":tophat:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

# Set color of sidebar #3f4a65
page_task = sidebar_header()

# Check if the user selected a task
if page_task == 'Stock':
    ciclai_stock()

if page_task == 'Price':
    ciclai_price()

