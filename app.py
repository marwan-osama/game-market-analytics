import streamlit as st

from data_processing import load_dashboard_data, preprocess_data
from sections.dlc_impact import render_dlc_impact
from sections.genre_analysis import render_genre_analysis
from sections.language_categories import render_language_categories
from sections.ml_model_trainer import render_ml_model_trainer
from sections.overview import render_overview
from sections.profit_analysis import render_profit_analysis
from sections.release_trends import render_release_trends
from sections.tag_analysis import render_tag_analysis
from ui import apply_custom_css, render_sidebar, show_data_load_message


st.set_page_config(
    page_title="Steam Games Analytics Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_page(page, df, merged_data):
    page_renderers = {
        "📊 Overview & Summary": lambda: render_overview(df),
        "🏷️ Tag Analysis": lambda: render_tag_analysis(df),
        "📈 Profit Analysis": lambda: render_profit_analysis(df, merged_data),
        "🎯 Genre Analysis": lambda: render_genre_analysis(df),
        "📅 Release Trends": lambda: render_release_trends(df),
        "🌍 Language & Categories": lambda: render_language_categories(df, merged_data),
        "🎮 DLC Impact": lambda: render_dlc_impact(df),
        "🤖 ML Model Trainer": lambda: render_ml_model_trainer(merged_data),
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
    render_page(page, df, merged_data)


if __name__ == "__main__":
    main()
