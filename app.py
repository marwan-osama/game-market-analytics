import streamlit as st

from data_processing import load_dashboard_data, preprocess_data
from sections.analytics import render_analytics
from sections.game_listing import render_game_listing
from ui import apply_custom_css, render_sidebar, show_data_load_message


st.set_page_config(
    page_title="Steam Games Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_page(page, df, merged_data, reviews_data, dlcs_data):
    page_renderers = {
        "Game Listing": lambda: render_game_listing(df, reviews_data, dlcs_data),
        "Analytics": lambda: render_analytics(df, merged_data),
    }
    page_renderers[page]()


def main():
    apply_custom_css()
    page = render_sidebar()

    games_data, dlcs_data, reviews_data = load_dashboard_data()

    if games_data is None:
        show_data_load_message()
        return

    df, merged_data = preprocess_data(games_data, dlcs_data, reviews_data)
    render_page(page, df, merged_data, reviews_data, dlcs_data)


if __name__ == "__main__":
    main()
