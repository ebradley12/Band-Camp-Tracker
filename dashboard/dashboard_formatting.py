"""This is the script for formatting some aspects of the dashboard"""

import streamlit as st


def customize_sidebar(degree: int, start_hex: str, end_hex: str):
    """
    Applies custom styling to change the sidebar 
    background color to a gradient and style the sidebar.
    """

    st.markdown(
        f"""
        <style>
        [data-testid="stSidebarContent"] {{
            background: linear-gradient({degree}deg, #{start_hex}, #{end_hex});
            color: white;
            #66b6d2;
            border: 3px solid
            border-radius: 10px;
            padding: 10px;
        }}
        [data-testid="stSidebarContent"] * {{
            color: white;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def glamourize_dashboard():
    """
    Runs all functions related to 
    formatting the Streamlit dashboard
    """
    customize_sidebar(180, "8c52ff", "5ce1e6")
