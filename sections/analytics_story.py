import streamlit as st


PROBLEM_POINTS = [
    (
        "Market saturation",
        "Steam releases keep rising, making discoverability the core strategic "
        "problem for new studios.",
    ),
    (
        "Asymmetric financial risk",
        "Games can require years of development before revenue returns, while "
        "failure rates remain high.",
    ),
    (
        "Fast-moving player demand",
        "Development cycles are slower than trend cycles on Steam, Twitch, "
        "TikTok, and community platforms.",
    ),
    (
        "Big Data disconnect",
        "Useful market signals exist, but they are fragmented across reviews, "
        "tags, prices, DLCs, languages, and player behavior.",
    ),
]


PAGE_FINDINGS = {
    "Overview & Summary": [
        "The dashboard turns scattered Steam market data into one navigable view for product, pricing, and positioning decisions.",
        "Core risk indicators are release volume, review traction, pricing spread, and player approval.",
        "The dataset supports pre-production validation before a studio commits budget to a genre or feature set.",
    ],
    "Tag Analysis": [
        "AAA_Action generates the loudest signal: very high positive review volume, but also high negative volume because scale amplifies criticism.",
        "Indie tags often show strong approval rates, especially platformer, puzzle, and casual niches.",
        "High price does not guarantee satisfaction; expensive tags set higher expectations and can attract harsher reviews.",
    ],
    "Profit Analysis": [
        "Estimated profit is driven by audience size, price, and review-derived purchase estimates.",
        "AAA_Action leads on total scale, while niche AAA tags can outperform on profit per game when competition is lower.",
        "Approval alone is not a profit signal; a beloved title with a small audience can still underperform financially.",
        "Treemap outliers usually reveal franchise concentration, not broad genre safety.",
    ],
    "Genre Analysis": [
        "Action attracts both large audiences and high endorsement, making it the strongest broad genre signal.",
        "Low competition is only useful when players also spend and review positively; empty niches can be empty for a reason.",
        "Competition quadrants highlight where a genre combines lower supply with stronger average profit.",
    ],
    "Release Trends": [
        "Release volume trends upward over time, reinforcing the discoverability crisis.",
        "Recent years show stronger saturation, so planning should account for crowded launch windows.",
        "Yearly review and price movement help identify whether growth is broad-based or concentrated in a few releases.",
    ],
    "Language & Categories": [
        "English remains the essential baseline language for reach.",
        "French, German, Simplified Chinese, Spanish, Japanese, Russian, Portuguese-Brazil, Korean, and Italian are priority expansion markets.",
        "Common features such as single-player, family sharing, achievements, cloud saves, and co-op indicate player expectations for modern releases.",
    ],
    "DLC Impact": [
        "More DLCs do not automatically create more positive reviews or higher engagement.",
        "A strong base game is the primary driver; DLC should extend demand, not compensate for weak fundamentals.",
        "Diminishing returns appear when add-on volume grows without clear player value.",
    ],
    "ML Model Trainer": [
        "Review and playtime features can predict likely tag positioning for a game.",
        "Tree-based models are the strongest fit for non-linear player-behavior patterns in this dashboard.",
        "Model comparison turns exploratory analysis into a repeatable classification workflow.",
    ],
}


def render_problem_description():
    st.markdown("#### Problem Description")
    st.markdown(
        "Small studios face a hyper-competitive market where supply grows "
        "faster than discoverability, while production costs and trend risk "
        "make intuition-only decisions expensive."
    )
    cols = st.columns(4)
    for col, (title, body) in zip(cols, PROBLEM_POINTS):
        with col:
            st.markdown(f"**{title}**")
            st.caption(body)
    st.markdown("---")


def render_key_findings(page_name):
    findings = PAGE_FINDINGS.get(page_name, [])
    if not findings:
        return

    st.markdown("#### Key Analysis Findings")
    for finding in findings:
        st.markdown(f"- {finding}")
    st.markdown("---")
