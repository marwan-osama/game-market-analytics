import plotly.express as px
import streamlit as st

from ui import STRETCH_WIDTH


def render_dlc_impact(df):
    st.title("🎮 DLC Impact Analysis")
    st.markdown("---")

    if "dlc_count" not in df.columns:
        st.warning("DLC data not available. Please upload the DLCs dataset.")
        return

    st.subheader("📊 DLCs vs Positive Reviews")

    game_with_dlcs = df.dropna(subset=["dlc_count"])

    if len(game_with_dlcs) > 0:
        fig_dlc = px.scatter(
            game_with_dlcs,
            x="dlc_count",
            y="total_positive",
            title="Number of DLCs vs. Total Positive Reviews",
            hover_name="name",
            color="price",
            size="price",
            color_continuous_scale="Viridis",
        )
        fig_dlc.update_xaxes(type="log")
        fig_dlc.update_yaxes(type="log")
        st.plotly_chart(fig_dlc, **STRETCH_WIDTH)

        st.markdown("---")
        st.subheader("📋 DLC Summary Statistics")
        dlc_summary = (
            game_with_dlcs.groupby("dlc_count")
            .agg(
                {
                    "total_positive": ["mean", "sum"],
                    "total_negative": "mean",
                    "price": "mean",
                    "app_id": "count",
                }
            )
            .reset_index()
        )
        dlc_summary.columns = [
            "DLC Count",
            "Avg Positive",
            "Total Positive",
            "Avg Negative",
            "Avg Price",
            "Game Count",
        ]
        st.dataframe(dlc_summary, **STRETCH_WIDTH)
    else:
        st.info("No data with DLC information available.")
