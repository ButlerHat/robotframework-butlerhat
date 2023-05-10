from streamlit.delta_generator import DeltaGenerator
import streamlit.components.v1 as components

def vnc(url: str):
    components.iframe(url, height=600)