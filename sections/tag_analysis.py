import plotly.express as px
import streamlit as st

from sections.analytics_utils import (
    add_quadrant_guides,
    build_tag_competition_metrics,
    build_tag_profit_table,
    filter_profit_scope,
)
from ui import STRETCH_WIDTH


def render_tag_analysis(df, merged_data=None):
    st.title("Game Tags Analysis")
    st.markdown("---")

    if df is None or df.empty or "tag" not in df.columns:
        st.warning("Tag data is not available.")
        return

    review_tab, profit_tab, playtime_tab = st.tabs(
        ["Reviews by Tag", "Profit & Competition", "Playtime by Tag"]
    )

    with review_tab:
        _render_tag_review_analysis(df)

    with profit_tab:
        _render_tag_profit_analysis(df)

    with playtime_tab:
        _render_tag_playtime_analysis(merged_data)


def _render_tag_review_analysis(df):
    tag_review_stats = (
        df.groupby("tag", dropna=False)
        .agg(
            total_positive=("total_positive", "sum"),
            total_negative=("total_negative", "sum"),
            avg_price=("price", "mean"),
        )
        .reset_index()
        .sort_values("total_positive", ascending=False)
    )

    top_n = st.slider(
        "Tags to compare",
        min_value=1,
        max_value=max(1, min(40, len(tag_review_stats))),
        value=min(15, len(tag_review_stats)),
        key="tag_reviews_top_n",
    )
    tag_slice = tag_review_stats.head(top_n)

    col1, col2 = st.columns(2)
    with col1:
        fig_positive = px.bar(
            tag_slice,
            x="tag",
            y="total_positive",
            title="Positive Reviews by Tag",
            color="tag",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_positive.update_layout(showlegend=False, xaxis_tickangle=45)
        st.plotly_chart(fig_positive, **STRETCH_WIDTH)

    with col2:
        fig_negative = px.bar(
            tag_slice.sort_values("total_negative", ascending=False),
            x="tag",
            y="total_negative",
            title="Negative Reviews by Tag",
            color="tag",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_negative.update_layout(showlegend=False, xaxis_tickangle=45)
        st.plotly_chart(fig_negative, **STRETCH_WIDTH)

    st.subheader("Tag Statistics Heatmap")
    heatmap_source = (
        tag_review_stats.head(top_n)
        .set_index("tag")[["avg_price", "total_positive", "total_negative"]]
        .rename(columns={"avg_price": "price"})
    )
    fig_heatmap = px.imshow(
        heatmap_source,
        color_continuous_scale="viridis",
        text_auto=True,
        aspect="auto",
        title="Genre Statistics Heatmap",
    )
    fig_heatmap.update_layout(coloraxis_colorbar=dict(title="Value"))
    st.plotly_chart(fig_heatmap, **STRETCH_WIDTH)


def _render_tag_profit_analysis(df):
    tag_profit_df = build_tag_profit_table(df)
    if tag_profit_df.empty:
        st.info("Profit metrics are not available for the current data.")
        return

    scope = st.radio(
        "Profit scope",
        ["All", "AAA", "Indie"],
        horizontal=True,
        key="tag_profit_scope",
    )
    scoped_df = filter_profit_scope(tag_profit_df, scope)
    if scoped_df.empty:
        st.info(f"No {scope.lower()} tag rows are available.")
        return

    st.dataframe(
        scoped_df.style.format(
            {
                "positive%": "{:.2f}",
                "negative%": "{:.2f}",
                "avg_price": "${:.2f}",
                "Average Profit (M)": "${:.2f}M",
                "Average Profit per game (M)": "${:.2f}M",
            }
        ),
        **STRETCH_WIDTH,
    )

    chart_top_n = st.slider(
        "Tags to chart",
        min_value=1,
        max_value=max(1, min(30, len(scoped_df))),
        value=min(15, len(scoped_df)),
        key="tag_profit_chart_top_n",
    )
    sorted_df = scoped_df.sort_values("Average Profit (M)", ascending=False).head(
        chart_top_n
    )

    col1, col2 = st.columns(2)
    with col1:
        fig_profit = px.bar(
            sorted_df,
            x="tag",
            y="Average Profit (M)",
            color="positive%",
            color_continuous_scale="RdYlGn",
            title="Average Profit by Tag",
            text="Average Profit (M)",
        )
        fig_profit.update_traces(texttemplate="$%{text:.2f}M", textposition="outside")
        fig_profit.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_profit, **STRETCH_WIDTH)

    with col2:
        fig_scatter = px.scatter(
            sorted_df,
            x="positive%",
            y="Average Profit (M)",
            size="Total Reviews",
            color="avg_price",
            hover_name="tag",
            color_continuous_scale="Viridis",
            title="Profit vs Review Sentiment",
            labels={
                "positive%": "Positive Reviews (%)",
                "Average Profit (M)": "Average Profit (Millions $)",
                "avg_price": "Average Price ($)",
            },
        )
        st.plotly_chart(fig_scatter, **STRETCH_WIDTH)

    fig_profit_per_game = px.bar(
        sorted_df,
        x="tag",
        y="Average Profit per game (M)",
        color="Game Count",
        color_continuous_scale="Blues",
        title="Average Profit per Game by Tag",
        text="Average Profit per game (M)",
    )
    fig_profit_per_game.update_traces(
        texttemplate="$%{text:.2f}M", textposition="outside"
    )
    fig_profit_per_game.update_layout(xaxis_tickangle=45)
    st.plotly_chart(fig_profit_per_game, **STRETCH_WIDTH)

    competition_metrics = build_tag_competition_metrics(df)
    if competition_metrics.empty:
        return

    st.subheader("Tag Competition vs Profitability")
    min_games = st.slider(
        "Minimum games per tag",
        min_value=1,
        max_value=max(1, int(competition_metrics["game_count"].max())),
        value=min(3, int(competition_metrics["game_count"].max())),
        key="tag_competition_min_games",
    )
    filtered_metrics = competition_metrics[
        competition_metrics["game_count"] >= min_games
    ].copy()
    if filtered_metrics.empty:
        st.info("No tags meet the minimum game-count threshold.")
        return

    median_count = filtered_metrics["game_count"].median()
    median_profit = filtered_metrics["avg_profit"].median()
    fig_competition = px.scatter(
        filtered_metrics,
        x="game_count",
        y="avg_profit",
        color="avg_positive_ratio",
        size="avg_purchases",
        hover_name="primary_tag",
        text="primary_tag",
        color_continuous_scale="RdYlGn",
        title="Tag Competition vs. Profitability Quadrant Analysis",
        labels={
            "game_count": "Number of Games (Competition)",
            "avg_profit": "Average Profit ($)",
            "avg_positive_ratio": "Avg. Positive Ratio",
        },
    )
    add_quadrant_guides(
        fig_competition,
        filtered_metrics,
        "game_count",
        "avg_profit",
        median_count,
        median_profit,
    )
    fig_competition.update_traces(
        textposition="top center",
        textfont=dict(size=9),
        marker=dict(line=dict(width=1, color="DarkSlateGrey")),
    )
    fig_competition.update_layout(
        xaxis_title="Number of Games (Competition Level)",
        yaxis_title="Average Profit ($)",
    )
    st.plotly_chart(fig_competition, **STRETCH_WIDTH)


def _render_tag_playtime_analysis(merged_data):
    if (
        merged_data is None
        or merged_data.empty
        or "tag" not in merged_data.columns
        or "total_playtime_hours" not in merged_data.columns
    ):
        st.info("Review playtime data is required for this analysis.")
        return

    playtime_df = (
        merged_data.groupby("tag", dropna=False)["total_playtime_hours"]
        .sum()
        .reset_index()
        .sort_values("total_playtime_hours", ascending=False)
    )
    top_n = st.slider(
        "Tags to rank by playtime",
        min_value=1,
        max_value=max(1, min(30, len(playtime_df))),
        value=min(15, len(playtime_df)),
        key="tag_playtime_top_n",
    )
    fig_playtime = px.bar(
        playtime_df.head(top_n),
        x="total_playtime_hours",
        y="tag",
        orientation="h",
        title="Total Playtime Hours by Game Tag",
        color="total_playtime_hours",
        color_continuous_scale="Plasma",
        labels={
            "tag": "Game Tag",
            "total_playtime_hours": "Total Playtime Hours",
        },
    )
    fig_playtime.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_playtime, **STRETCH_WIDTH)
