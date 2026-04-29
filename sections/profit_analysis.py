import pandas as pd
import plotly.express as px
import streamlit as st

from ui import STRETCH_WIDTH


def render_profit_analysis(df, merged_data):
    st.title("Profit Analysis")
    st.markdown("---")

    if "tag" not in df.columns:
        st.warning("Tag column not found. Cannot compute profit analysis.")
        return

    tags_dummies = df["tag"].str.get_dummies(";")

    results = []
    for tag_name in tags_dummies.columns:
        mask = tags_dummies[tag_name] == 1
        tagged_games = df.loc[mask]

        if tagged_games.empty:
            continue

        results.append(
            {
                "tag": tag_name,
                "positive%": tagged_games.get("positive_pct", pd.Series([0]))
                .mean()
                .round(2),
                "negative%": tagged_games.get("negative_pct", pd.Series([0]))
                .mean()
                .round(2),
                "avg_price": tagged_games["price"].mean().round(2),
                "Total Reviews": tagged_games["total_reviews"].sum(),
                "Game Count": len(tagged_games),
            }
        )

    tag_df = pd.DataFrame(results)
    tag_df = tag_df.sort_values("Total Reviews", ascending=False).reset_index(drop=True)

    if "total_reviews" in df.columns:
        tag_df["Average Profit (M)"] = (
            (tag_df["avg_price"] * tag_df["Total Reviews"] * 0.4) / 1000000
        ).round(2)
        tag_df["Average Profit per game (M)"] = (
            tag_df["Average Profit (M)"] / tag_df["Game Count"]
        ).round(2)

    st.subheader("Profit Metrics by Tag")
    st.dataframe(
        tag_df.style.format(
            {
                "avg_price": lambda value: f"${value:.2f}",
                "Average Profit (M)": lambda value: f"${value:.2f}M",
                "Average Profit per game (M)": lambda value: f"${value:.2f}M",
            }
        ),
        **STRETCH_WIDTH,
    )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            ["Average Profit (M)", "Total Reviews", "Game Count", "avg_price"],
        )
    with col2:
        top_n = st.slider("Number of tags", 5, 30, 15)
    with col3:
        chart_type = st.radio(
            "Chart type", ["Bar Chart", "Scatter Plot"], horizontal=True
        )

    sorted_df = tag_df.sort_values(sort_by, ascending=False).head(top_n)

    if chart_type == "Bar Chart":
        fig_profit = px.bar(
            sorted_df,
            x="tag",
            y="Average Profit (M)",
            title=f"Average Profit by Tag (Top {top_n})",
            color="Average Profit (M)",
            color_continuous_scale="Viridis",
            text="Average Profit (M)",
        )
        fig_profit.update_traces(texttemplate="$%{text:.2f}M", textposition="outside")
        fig_profit.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_profit, **STRETCH_WIDTH)
    else:
        fig_scatter = px.scatter(
            sorted_df,
            x="positive%",
            y="Average Profit (M)",
            size="Total Reviews",
            color="avg_price",
            hover_name="tag",
            title="Profit vs Review Sentiment",
            color_continuous_scale="Viridis",
            labels={
                "positive%": "Positive Review %",
                "Average Profit (M)": "Avg Profit ($M)",
            },
        )
        st.plotly_chart(fig_scatter, **STRETCH_WIDTH)

    st.markdown("---")

    st.subheader("Average Profit per Game by Tag")
    fig_profit_game = px.bar(
        sorted_df,
        x="tag",
        y="Average Profit per game (M)",
        title=f"Average Profit per Game by Tag (Top {top_n})",
        color="Game Count",
        color_continuous_scale="Blues",
        text="Average Profit per game (M)",
    )
    fig_profit_game.update_traces(texttemplate="$%{text:.2f}M", textposition="outside")
    fig_profit_game.update_layout(xaxis_tickangle=45)
    st.plotly_chart(fig_profit_game, **STRETCH_WIDTH)

    if merged_data is not None and "primary_tag" in merged_data.columns:
        st.markdown("---")
        st.subheader("Top Games by Estimated Profit")

        if (
            "total_steam_purchases" in merged_data.columns
            and "price" in merged_data.columns
        ):
            merged_data["Profit"] = (
                merged_data["price"] * merged_data["total_steam_purchases"] * 0.4
            )

            top_profit = merged_data.sort_values("Profit", ascending=False).head(15)

            fig_top = px.bar(
                top_profit,
                x="Profit",
                y="name",
                color="primary_tag",
                hover_data=["price", "total_reviews"],
                title="Top 15 Games by Estimated Profit",
                labels={"name": "Game Name", "Profit": "Profit ($)"},
            )
            fig_top.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_top, **STRETCH_WIDTH)
