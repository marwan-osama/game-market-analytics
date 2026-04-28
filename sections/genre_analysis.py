import plotly.express as px
import streamlit as st

from ui import STRETCH_WIDTH


def render_genre_analysis(df):
    st.title("🎯 Game Genres Analysis")
    st.markdown("---")

    if "genres" not in df.columns:
        st.warning("Genres column not found in the data.")
        return

    st.subheader("📊 Genre Distribution")

    genre_exploded = df.explode("genres")
    genre_counts = genre_exploded["genres"].value_counts().reset_index()
    genre_counts.columns = ["genres", "count"]

    col1, col2 = st.columns(2)
    with col1:
        fig_genre = px.bar(
            genre_counts,
            x="genres",
            y="count",
            title="All Game Genres",
            color="count",
            color_continuous_scale="purples",
        )
        fig_genre.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_genre, **STRETCH_WIDTH)

    with col2:
        if "positive_pct" in df.columns:
            genres_and_reviews = df.explode("genres")
            genre_positive = (
                genres_and_reviews.groupby("genres")["positive_pct"].mean().reset_index()
            )
            genre_positive = genre_positive.sort_values(
                "positive_pct", ascending=False
            )

            fig_avg = px.bar(
                genre_positive,
                x="positive_pct",
                y="genres",
                orientation="h",
                title="Average Positive Review % by Genre",
                color="positive_pct",
                color_continuous_scale="Greens",
            )
            fig_avg.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_avg, **STRETCH_WIDTH)
        else:
            st.info("Positive percentage data not available.")

    st.markdown("---")

    if "primary_tag" in df.columns:
        st.subheader("💰 Genre Profitability")
        genre_profit = (
            genre_exploded.groupby("genres")
            .agg(
                {
                    "price": "mean",
                    "total_positive": "sum",
                    "total_negative": "sum",
                    "total_reviews": "sum",
                }
            )
            .reset_index()
        )

        col1, col2 = st.columns(2)
        with col1:
            fig_profit_genre = px.scatter(
                genre_profit,
                x="total_reviews",
                y="price",
                size="total_positive",
                color="total_negative",
                hover_name="genres",
                title="Genre: Price vs Reviews",
                color_continuous_scale="RdYlGn",
            )
            st.plotly_chart(fig_profit_genre, **STRETCH_WIDTH)

        with col2:
            genre_profit["positive_ratio"] = (
                genre_profit["total_positive"] / genre_profit["total_reviews"]
            )
            fig_ratio = px.bar(
                genre_profit.sort_values("positive_ratio", ascending=False),
                x="genres",
                y="positive_ratio",
                title="Positive Review Ratio by Genre",
                color="positive_ratio",
                color_continuous_scale="Greens",
            )
            fig_ratio.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_ratio, **STRETCH_WIDTH)
