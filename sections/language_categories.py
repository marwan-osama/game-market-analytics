from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

from ui import STRETCH_WIDTH


def render_language_categories(df, merged_data):
    st.title("Languages & Categories Analysis")
    st.markdown("---")

    st.subheader("Most Used Languages")
    if "supported_languages" in df.columns:
        all_languages = []
        for lang_str in df["supported_languages"].dropna():
            languages = [lang.strip() for lang in lang_str.split(",")]
            all_languages.extend(languages)

        language_counts = Counter(all_languages)
        top_languages = pd.DataFrame(
            {
                "language": list(dict(language_counts.most_common(15)).keys()),
                "count": list(dict(language_counts.most_common(15)).values()),
            }
        )

        fig_lang = px.bar(
            top_languages,
            x="count",
            y="language",
            orientation="h",
            title="Top 15 Most Used Languages",
            color="count",
            color_continuous_scale="Viridis",
        )
        fig_lang.update_layout(
            xaxis_title="Number of Games",
            yaxis_title="Language",
            yaxis={"categoryorder": "total ascending"},
        )
        fig_lang.update_traces(texttemplate="%{x}", textposition="outside")
        st.plotly_chart(fig_lang, **STRETCH_WIDTH)
    else:
        st.info("Supported languages data not available.")

    st.markdown("---")

    st.subheader("Most Popular Categories")
    if "categories" in df.columns:
        categories_exploded = df.explode("categories")
        category_counts = categories_exploded["categories"].value_counts().reset_index()
        category_counts.columns = ["category", "count"]

        col1, col2 = st.columns(2)
        with col1:
            fig_cat = px.bar(
                category_counts.head(10),
                x="category",
                y="count",
                title="Top 10 Game Features/Categories",
                color="count",
                color_continuous_scale="Reds",
            )
            fig_cat.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_cat, **STRETCH_WIDTH)

        with col2:
            fig_cat_treemap = px.treemap(
                category_counts.head(20),
                path=["category"],
                values="count",
                title="Game Categories (Treemap)",
                color="count",
                color_continuous_scale="Blues",
            )
            st.plotly_chart(fig_cat_treemap, **STRETCH_WIDTH)
    else:
        st.info("Categories data not available.")
