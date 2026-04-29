import math
import re
from html import escape

import pandas as pd
import streamlit as st


SORT_OPTIONS = {
    "Most reviewed": ("total_reviews", False),
    "Highest positive score": ("positive_pct", False),
    "Newest releases": ("release_date", False),
    "Oldest releases": ("release_date", True),
    "Price: low to high": ("price", True),
    "Price: high to low": ("price", False),
    "Name: A to Z": ("name", True),
}


def render_game_listing(df):
    st.title("Steam Game Storefront")
    st.markdown(
        "Browse every game as a product card, then narrow the catalog with filters."
    )

    if df is None or df.empty:
        st.info("No games are available to display.")
        return

    _inject_listing_css()

    games = _prepare_listing_dataframe(df)
    filters = _render_filters(games)
    filtered_games = _filter_games(games, filters)
    filtered_games = _sort_games(filtered_games, filters["sort_by"])

    _render_listing_summary(games, filtered_games)

    if filtered_games.empty:
        st.warning("No games match the current filters.")
        return

    page_size = filters["page_size"]
    total_pages = max(1, math.ceil(len(filtered_games) / page_size))
    if total_pages == 1:
        page_number = 1
    else:
        page_number = st.slider("Page", 1, total_pages, 1)

    start = (page_number - 1) * page_size
    end = start + page_size
    page_games = filtered_games.iloc[start:end]

    st.caption(
        f"Showing {start + 1:,}-{min(end, len(filtered_games)):,} "
        f"of {len(filtered_games):,} matching games"
    )
    _render_game_cards(page_games)


def _prepare_listing_dataframe(df):
    games = df.copy()

    if "price" in games.columns:
        games["price_numeric"] = pd.to_numeric(games["price"], errors="coerce").fillna(0)
    else:
        games["price_numeric"] = 0

    if "total_reviews" in games.columns:
        games["reviews_numeric"] = pd.to_numeric(
            games["total_reviews"], errors="coerce"
        ).fillna(0)
    else:
        games["reviews_numeric"] = 0

    if "positive_pct" in games.columns:
        games["positive_pct_numeric"] = pd.to_numeric(
            games["positive_pct"], errors="coerce"
        ).fillna(0)
    else:
        games["positive_pct_numeric"] = 0

    if "year" in games.columns:
        games["year_numeric"] = pd.to_numeric(games["year"], errors="coerce")
    elif "release_date" in games.columns:
        games["year_numeric"] = pd.to_datetime(
            games["release_date"], errors="coerce"
        ).dt.year
    else:
        games["year_numeric"] = pd.NA

    return games


def _render_filters(games):
    st.markdown("---")
    st.subheader("Filters")

    genre_options = _unique_values(games, "genres")
    tag_options = _unique_values(games, "tag")
    category_options = _unique_values(games, "categories")
    year_values = games["year_numeric"].dropna()
    max_price = float(games["price_numeric"].max())

    row1 = st.columns([2, 1, 1])
    with row1[0]:
        search = st.text_input(
            "Search",
            placeholder="Search by title, description, developer, or publisher",
        )
    with row1[1]:
        sort_by = st.selectbox("Sort by", list(SORT_OPTIONS), index=0)
    with row1[2]:
        page_size = st.selectbox("Cards per page", [12, 24, 48, 96], index=1)

    row2 = st.columns(3)
    with row2[0]:
        selected_genres = st.multiselect("Genres", genre_options)
    with row2[1]:
        selected_tags = st.multiselect("Tags", tag_options)
    with row2[2]:
        selected_categories = st.multiselect("Categories", category_options)

    row3 = st.columns(4)
    with row3[0]:
        if max_price > 0:
            price_range = st.slider(
                "Price range",
                0.0,
                max_price,
                (0.0, max_price),
                step=1.0,
                format="$%.0f",
            )
        else:
            price_range = (0.0, 0.0)
            st.caption("All listed games are free or missing price data.")
    with row3[1]:
        if year_values.empty:
            year_range = None
            st.caption("Release year data is unavailable.")
        else:
            min_year = int(year_values.min())
            max_year = int(year_values.max())
            if min_year == max_year:
                year_range = (min_year, max_year)
                st.caption(f"Release year: {min_year}")
            else:
                year_range = st.slider(
                    "Release years",
                    min_year,
                    max_year,
                    (min_year, max_year),
                )
    with row3[2]:
        min_positive = st.slider("Minimum positive score", 0, 100, 0, format="%d%%")
    with row3[3]:
        free_only = st.checkbox("Free games only")
        has_dlc_only = st.checkbox(
            "Has DLC only", disabled="dlc_count" not in games.columns
        )

    return {
        "search": search.strip(),
        "sort_by": sort_by,
        "page_size": page_size,
        "genres": selected_genres,
        "tags": selected_tags,
        "categories": selected_categories,
        "price_range": price_range,
        "year_range": year_range,
        "min_positive": min_positive,
        "free_only": free_only,
        "has_dlc_only": has_dlc_only,
    }


def _filter_games(games, filters):
    filtered = games.copy()

    if filters["search"]:
        search_columns = [
            column
            for column in ["name", "short_description", "developers", "publishers"]
            if column in filtered.columns
        ]
        if search_columns:
            query = filters["search"].casefold()
            search_text = (
                filtered[search_columns]
                .fillna("")
                .astype(str)
                .agg(" ".join, axis=1)
                .str.casefold()
            )
            filtered = filtered[search_text.str.contains(query, regex=False)]

    if filters["genres"]:
        filtered = filtered[
            filtered["genres"].apply(lambda value: _contains_any(value, filters["genres"]))
        ]

    if filters["tags"]:
        filtered = filtered[
            filtered["tag"].apply(lambda value: _contains_any(value, filters["tags"]))
        ]

    if filters["categories"]:
        filtered = filtered[
            filtered["categories"].apply(
                lambda value: _contains_any(value, filters["categories"])
            )
        ]

    price_min, price_max = filters["price_range"]
    filtered = filtered[
        filtered["price_numeric"].between(price_min, price_max, inclusive="both")
    ]

    if filters["free_only"]:
        filtered = filtered[filtered["price_numeric"] == 0]

    if filters["year_range"] is not None:
        year_min, year_max = filters["year_range"]
        filtered = filtered[
            filtered["year_numeric"].between(year_min, year_max, inclusive="both")
        ]

    if filters["min_positive"] > 0:
        filtered = filtered[
            filtered["positive_pct_numeric"] >= filters["min_positive"]
        ]

    if filters["has_dlc_only"] and "dlc_count" in filtered.columns:
        dlc_count = pd.to_numeric(filtered["dlc_count"], errors="coerce").fillna(0)
        filtered = filtered[dlc_count > 0]

    return filtered


def _sort_games(games, sort_by):
    column, ascending = SORT_OPTIONS[sort_by]

    if column == "price":
        return games.sort_values("price_numeric", ascending=ascending)
    if column == "total_reviews":
        return games.sort_values("reviews_numeric", ascending=ascending)
    if column == "positive_pct":
        return games.sort_values("positive_pct_numeric", ascending=ascending)
    if column in games.columns:
        return games.sort_values(column, ascending=ascending, na_position="last")

    return games


def _render_listing_summary(games, filtered_games):
    st.markdown("---")
    total_games = len(games)
    filtered_total = len(filtered_games)
    free_games = int((filtered_games["price_numeric"] == 0).sum())
    avg_price = filtered_games["price_numeric"].mean() if filtered_total else 0
    avg_score = (
        filtered_games["positive_pct_numeric"].mean() if filtered_total else 0
    )

    cols = st.columns(4)
    cols[0].metric("Matching Games", f"{filtered_total:,}", f"of {total_games:,}")
    cols[1].metric("Free Games", f"{free_games:,}")
    cols[2].metric("Average Price", _format_price(avg_price))
    cols[3].metric("Average Positive", f"{avg_score:.1f}%")


def _render_game_cards(games):
    for start in range(0, len(games), 3):
        columns = st.columns(3)
        for column, (_, game) in zip(columns, games.iloc[start : start + 3].iterrows()):
            with column:
                st.markdown(_build_card_html(game), unsafe_allow_html=True)


def _build_card_html(game):
    name = _safe_text(game.get("name", "Untitled game"))
    description = _safe_text(
        _truncate_text(game.get("short_description", ""), max_length=150)
    )
    image = _safe_url(game.get("header_image", ""))
    game_url = _safe_url(game.get("url", ""))
    website_url = _safe_url(game.get("website", ""))
    release = _format_release(game)
    price = _format_price(game.get("price_numeric", game.get("price")))
    reviews = _format_count(game.get("reviews_numeric", game.get("total_reviews")))
    positive_score = _format_percent(
        game.get("positive_pct_numeric", game.get("positive_pct"))
    )
    developer = _safe_text(_first_value(game.get("developers", "")))
    publisher = _safe_text(_first_value(game.get("publishers", "")))
    primary_genre = _safe_text(_first_value(game.get("genres", "")))
    primary_tag = _safe_text(_first_value(game.get("tag", "")))
    review_summary = _safe_text(game.get("review_summary", ""))
    link_url = game_url or website_url

    image_html = (
        f'<img class="game-card__image" src="{image}" alt="{name} cover">'
        if image
        else '<div class="game-card__image game-card__image--empty">No image</div>'
    )
    genre_chip = (
        f'<span class="game-card__chip">{primary_genre}</span>' if primary_genre else ""
    )
    tag_chip = f'<span class="game-card__chip">{primary_tag}</span>' if primary_tag else ""
    developer_html = (
        f'<p class="game-card__maker">Developer: <strong>{developer}</strong></p>'
        if developer
        else ""
    )
    publisher_html = (
        f'<p class="game-card__maker">Publisher: <strong>{publisher}</strong></p>'
        if publisher
        else ""
    )
    review_html = (
        f'<div class="game-card__summary">{review_summary}</div>'
        if review_summary
        else ""
    )
    action_html = (
        f'<a class="game-card__action" href="{link_url}" target="_blank" '
        'rel="noopener noreferrer">View Game</a>'
        if link_url
        else '<span class="game-card__action game-card__action--disabled">No Link</span>'
    )

    return f"""
    <article class="game-card">
        <div class="game-card__media">{image_html}</div>
        <div class="game-card__body">
            <div class="game-card__chips">{genre_chip}{tag_chip}</div>
            <h3>{name}</h3>
            <p class="game-card__description">{description or "No description available."}</p>
            {review_html}
            <div class="game-card__price-row">
                <span>Price</span>
                <strong>{price}</strong>
            </div>
            <div class="game-card__stats">
                <span><strong>{positive_score}</strong> positive</span>
                <span><strong>{reviews}</strong> reviews</span>
                <span><strong>{release}</strong></span>
            </div>
            {developer_html}
            {publisher_html}
            {action_html}
        </div>
    </article>
    """


def _inject_listing_css():
    st.markdown(
        """
        <style>
        .game-card {
            background: linear-gradient(160deg, #111827 0%, #1f2937 58%, #263647 100%);
            border: 1px solid rgba(148, 163, 184, 0.24);
            border-radius: 22px;
            box-shadow: 0 18px 38px rgba(15, 23, 42, 0.22);
            color: #f8fafc;
            display: flex;
            flex-direction: column;
            min-height: 560px;
            margin-bottom: 1.25rem;
            overflow: hidden;
        }

        .game-card__media {
            background: #0f172a;
            min-height: 160px;
        }

        .game-card__image {
            display: block;
            height: 160px;
            object-fit: cover;
            width: 100%;
        }

        .game-card__image--empty {
            align-items: center;
            background:
                radial-gradient(circle at 20% 20%, rgba(56, 189, 248, 0.28), transparent 30%),
                linear-gradient(135deg, #172033, #0f172a);
            color: #94a3b8;
            display: flex;
            font-weight: 700;
            justify-content: center;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .game-card__body {
            display: flex;
            flex: 1;
            flex-direction: column;
            gap: 0.72rem;
            padding: 1rem;
        }

        .game-card h3 {
            color: #f8fafc;
            font-size: 1.12rem;
            line-height: 1.25;
            margin: 0;
        }

        .game-card__description {
            color: #cbd5e1;
            font-size: 0.9rem;
            line-height: 1.45;
            margin: 0;
            min-height: 4rem;
        }

        .game-card__chips {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            min-height: 1.75rem;
        }

        .game-card__chip {
            background: rgba(56, 189, 248, 0.14);
            border: 1px solid rgba(125, 211, 252, 0.32);
            border-radius: 999px;
            color: #bae6fd;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.2rem 0.58rem;
            text-transform: uppercase;
        }

        .game-card__summary {
            background: rgba(15, 23, 42, 0.5);
            border-left: 3px solid #38bdf8;
            border-radius: 10px;
            color: #dbeafe;
            font-size: 0.82rem;
            padding: 0.45rem 0.6rem;
        }

        .game-card__price-row,
        .game-card__stats {
            display: grid;
            gap: 0.5rem;
        }

        .game-card__price-row {
            align-items: center;
            border-top: 1px solid rgba(148, 163, 184, 0.2);
            color: #cbd5e1;
            grid-template-columns: 1fr auto;
            padding-top: 0.75rem;
        }

        .game-card__price-row strong {
            color: #86efac;
            font-size: 1.18rem;
        }

        .game-card__stats {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }

        .game-card__stats span {
            background: rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            color: #cbd5e1;
            font-size: 0.76rem;
            padding: 0.48rem;
        }

        .game-card__stats strong {
            color: #f8fafc;
            display: block;
            font-size: 0.88rem;
        }

        .game-card__maker {
            color: #94a3b8;
            font-size: 0.8rem;
            margin: 0;
        }

        .game-card__maker strong {
            color: #e2e8f0;
        }

        .game-card__action {
            background: linear-gradient(135deg, #38bdf8, #22c55e);
            border-radius: 13px;
            color: #04111d !important;
            display: block;
            font-weight: 800;
            margin-top: auto;
            padding: 0.68rem 0.85rem;
            text-align: center;
            text-decoration: none !important;
        }

        .game-card__action--disabled {
            background: rgba(148, 163, 184, 0.22);
            color: #cbd5e1 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _unique_values(games, column):
    if column not in games.columns:
        return []

    values = set()
    for value in games[column].dropna():
        values.update(_as_list(value))

    return sorted(values, key=lambda item: item.casefold())


def _contains_any(value, selected_values):
    normalized_values = {item.casefold() for item in _as_list(value)}
    selected = {item.casefold() for item in selected_values}
    return bool(normalized_values & selected)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, float) and pd.isna(value):
        return []
    if isinstance(value, (list, tuple, set)):
        raw_values = value
    else:
        raw_values = re.split(r"[;,]", str(value))

    cleaned_values = []
    for item in raw_values:
        text = str(item).strip().strip("[]'\"")
        if text and text.casefold() not in {"nan", "none"}:
            cleaned_values.append(text)
    return cleaned_values


def _first_value(value):
    values = _as_list(value)
    return values[0] if values else ""


def _truncate_text(value, max_length):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""

    text = re.sub(r"\s+", " ", str(value)).strip()
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 1].rstrip()}..."


def _format_price(value):
    numeric_value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric_value):
        return "N/A"
    if numeric_value == 0:
        return "Free"
    return f"${numeric_value:,.2f}"


def _format_count(value):
    numeric_value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric_value):
        return "0"
    return f"{int(numeric_value):,}"


def _format_percent(value):
    numeric_value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric_value):
        return "N/A"
    return f"{numeric_value:.0f}%"


def _format_release(game):
    if "release_date" in game.index and pd.notna(game.get("release_date")):
        release_date = pd.to_datetime(game.get("release_date"), errors="coerce")
        if pd.notna(release_date):
            return str(release_date.year)

    year = pd.to_numeric(pd.Series([game.get("year_numeric")]), errors="coerce").iloc[0]
    if pd.notna(year):
        return str(int(year))

    return "Unknown"


def _safe_text(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return escape(str(value), quote=True)


def _safe_url(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""

    text = str(value).strip()
    if not text.startswith(("http://", "https://")):
        return ""
    return escape(text, quote=True)
