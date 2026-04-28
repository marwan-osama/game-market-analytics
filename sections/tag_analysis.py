import plotly.express as px
import streamlit as st

from ui import STRETCH_WIDTH


def render_tag_analysis(df):
    st.title("Game Tags Analysis")
    st.markdown("---")

    if "tag" not in df.columns:
        st.warning("Tag column not found in the data.")
        return

    st.subheader("Most Common Tags")
    tag_counts = df["tag"].value_counts().reset_index()
    tag_counts.columns = ["tag", "count"]

    col1, col2 = st.columns(2)
    with col1:
        top_n = st.slider("Number of tags to display", 5, 50, 20)
    with col2:
        chart_type = st.radio("Chart type", ["Bar Chart", "Treemap"], horizontal=True)

    if chart_type == "Bar Chart":
        fig_tags = px.bar(
            tag_counts.head(top_n),
            x="count",
            y="tag",
            orientation="h",
            title=f"Top {top_n} Game Tags by Count",
            color="count",
            color_continuous_scale="Viridis",
        )
        fig_tags.update_layout(xaxis_title="Count", yaxis_title="Tag")
        st.plotly_chart(fig_tags, **STRETCH_WIDTH)
    else:
        fig_treemap = px.treemap(
            tag_counts.head(top_n),
            path=["tag"],
            values="count",
            title=f"Top {top_n} Game Tags (Treemap)",
            color="count",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_treemap, **STRETCH_WIDTH)

    st.markdown("---")

    st.subheader("Positive vs Negative Reviews by Tag")

    tag_review_stats = (
        df.groupby("tag")
        .agg(
            total_positive=("total_positive", "sum"),
            total_negative=("total_negative", "sum"),
            total_reviews=("total_reviews", "sum"),
            avg_price=("price", "mean"),
        )
        .reset_index()
    )

    col1, col2 = st.columns(2)
    with col1:
        fig_pos = px.bar(
            tag_review_stats.nlargest(15, "total_positive"),
            x="tag",
            y="total_positive",
            title="Top 15 Tags by Positive Reviews",
            color="total_positive",
            color_continuous_scale="Greens",
        )
        fig_pos.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_pos, **STRETCH_WIDTH)

    with col2:
        fig_neg = px.bar(
            tag_review_stats.nlargest(15, "total_negative"),
            x="tag",
            y="total_negative",
            title="Top 15 Tags by Negative Reviews",
            color="total_negative",
            color_continuous_scale="Reds",
        )
        fig_neg.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_neg, **STRETCH_WIDTH)

    st.markdown("---")

    st.subheader("Tag Statistics Heatmap")
    genre_stats = df.groupby("tag").agg(
        {"price": "mean", "total_positive": "sum", "total_negative": "sum"}
    )

    if st.checkbox("Show Heatmap", False):
        fig_heatmap = px.imshow(
            genre_stats,
            color_continuous_scale="viridis",
            text_auto=True,
            aspect="auto",
            title="Genre Statistics Heatmap",
        )
        fig_heatmap.update_layout(coloraxis_colorbar=dict(title="Value"))
        st.plotly_chart(fig_heatmap, **STRETCH_WIDTH)
