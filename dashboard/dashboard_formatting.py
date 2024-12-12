"""This is the script for formatting some aspects of the dashboard"""

import streamlit as st


def customize_sidebar(degree: int, start_hex: str, end_hex: str):
    """
    Applies custom styling to change the sidebar background color to a gradient and style the sidebar.
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


def change_radio_button_colours():
    st.markdown(
        """
    <style>
    /* Sidebar background color */
    div[data-testid="stSidebar"] > div:first-child {
        background-color: #f0f2f6;
    }

    /* Radio button text color */
    div[data-testid="stSidebar"] .stRadio > label {
        color: #8c52ff;
        font-size: 16px;
    }

    /* Radio button dot color */
    div[data-testid="stSidebar"] .stRadio > div > div {
        color: #8c52ff; /* Default color */
        background-color: #8c52ff; /* Dot fill */
    }

    /* Hover effect for radio button */
    div[data-testid="stSidebar"] .stRadio > div > div:hover {
        color: #5ce1e6;
        background-color: #5ce1e6;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def glamourize_dashboard():
    customize_sidebar(180, "8c52ff", "5ce1e6")
    change_radio_button_colours()
