import os
from urllib.error import URLError
from urllib.request import urlopen

import pandas as pd
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
from sklearn.preprocessing import LabelEncoder


DEFAULT_COLLECTIONS = {
    "games": ("cleaned_games_data", "games", "games_data", "cleaned_games"),
    "dlcs": ("cleaned_DLCS_data", "cleaned_dlcs_data", "dlcs", "dlc"),
    "reviews": ("reviews_data_cleaned", "reviews", "reviews_data", "cleaned_reviews"),
}


def get_mongodb_config():
    """Read MongoDB settings from env vars first, then Streamlit secrets."""
    secrets = {}
    try:
        secrets = st.secrets.get("mongodb", {})
    except Exception:
        secrets = {}

    return {
        "uri": os.getenv("MONGODB_URI") or secrets.get("uri", ""),
        "database": os.getenv("MONGODB_DATABASE") or secrets.get("database", ""),
        "games_collection": os.getenv("MONGODB_GAMES_COLLECTION")
        or secrets.get("games_collection", ""),
        "dlcs_collection": os.getenv("MONGODB_DLCS_COLLECTION")
        or secrets.get("dlcs_collection", ""),
        "reviews_collection": os.getenv("MONGODB_REVIEWS_COLLECTION")
        or secrets.get("reviews_collection", ""),
    }


def normalize_name(name):
    return name.lower().replace("-", "_")


def resolve_database_name(client, configured_database):
    if configured_database:
        return configured_database

    database_names = [
        name
        for name in client.list_database_names()
        if name not in {"admin", "config", "local"}
    ]
    return database_names[0] if database_names else None


def resolve_collection_name(db, configured_collection, candidates):
    if configured_collection:
        return configured_collection

    collection_names = db.list_collection_names()
    collection_lookup = {normalize_name(name): name for name in collection_names}

    for candidate in candidates:
        match = collection_lookup.get(normalize_name(candidate))
        if match:
            return match

    for collection_name in collection_names:
        normalized = normalize_name(collection_name)
        if any(normalize_name(candidate) in normalized for candidate in candidates):
            return collection_name

    return None


def collection_to_dataframe(db, collection_name):
    if not collection_name:
        return None

    documents = list(db[collection_name].find({}, {"_id": 0}))
    return pd.DataFrame(documents)


def get_public_ip():
    try:
        with urlopen("https://api.ipify.org", timeout=3) as response:
            return response.read().decode("utf-8").strip()
    except (OSError, URLError):
        return None


@st.cache_data(show_spinner="Loading data from MongoDB...", ttl=600)
def load_mongodb_data(uri, database, games_collection, dlcs_collection, reviews_collection):
    if not uri:
        raise ValueError(
            "MongoDB URI is missing. Set MONGODB_URI, .streamlit/secrets.toml, "
            "or ~/.streamlit/secrets.toml."
        )

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")

    database_name = resolve_database_name(client, database)
    if database_name is None:
        raise ValueError("No user databases were found in this MongoDB cluster.")

    db = client[database_name]
    resolved_games_collection = resolve_collection_name(
        db, games_collection, DEFAULT_COLLECTIONS["games"]
    )
    resolved_dlcs_collection = resolve_collection_name(
        db, dlcs_collection, DEFAULT_COLLECTIONS["dlcs"]
    )
    resolved_reviews_collection = resolve_collection_name(
        db, reviews_collection, DEFAULT_COLLECTIONS["reviews"]
    )

    games_data = collection_to_dataframe(db, resolved_games_collection)
    dlcs_data = collection_to_dataframe(db, resolved_dlcs_collection)
    reviews_data = collection_to_dataframe(db, resolved_reviews_collection)

    if games_data is None or games_data.empty:
        raise ValueError(
            "Games collection was not found or is empty. Configure mongodb.games_collection."
        )
    if dlcs_data is not None and dlcs_data.empty:
        dlcs_data = None
    if reviews_data is not None and reviews_data.empty:
        reviews_data = None

    return {
        "database": database_name,
        "collections": {
            "games": resolved_games_collection,
            "dlcs": resolved_dlcs_collection,
            "reviews": resolved_reviews_collection,
        },
        "games_data": games_data,
        "dlcs_data": dlcs_data,
        "reviews_data": reviews_data,
    }


def load_dashboard_data():
    config = get_mongodb_config()

    try:
        result = load_mongodb_data(
            config["uri"],
            config["database"],
            config["games_collection"],
            config["dlcs_collection"],
            config["reviews_collection"],
        )
    except ServerSelectionTimeoutError as e:
        public_ip = get_public_ip()
        st.error(
            "Could not connect to MongoDB Atlas. Atlas is rejecting the TLS handshake "
            "before authentication."
        )
        if public_ip:
            st.warning(
                "Add this machine's current IP to Atlas Network Access: "
                f"`{public_ip}/32`"
            )
        st.markdown(
            """
            In MongoDB Atlas, open **Security > Network Access > Add IP Address**,
            add the IP above, wait for the rule to become active, then click
            **Refresh MongoDB data** in the sidebar.
            """
        )
        with st.expander("Connection error details"):
            st.code(str(e))
        return None, None, None
    except (PyMongoError, ValueError) as e:
        st.error(f"Could not load MongoDB data: {e}")
        return None, None, None

    games_data = result["games_data"]
    dlcs_data = result["dlcs_data"]
    reviews_data = result["reviews_data"]

    st.success(
        f"Games data loaded from MongoDB: {games_data.shape[0]} rows, {games_data.shape[1]} columns"
    )
    if dlcs_data is not None:
        st.success(
            f"DLCs data loaded from MongoDB: {dlcs_data.shape[0]} rows, {dlcs_data.shape[1]} columns"
        )
    if reviews_data is not None:
        st.success(
            f"Reviews data loaded from MongoDB: {reviews_data.shape[0]} rows, {reviews_data.shape[1]} columns"
        )

    st.caption(
        "MongoDB source: "
        f"{result['database']} / "
        f"{', '.join(name for name in result['collections'].values() if name)}"
    )
    return games_data, dlcs_data, reviews_data


def get_dataframe_summary(dataframe):
    """Return display-friendly schema details without writing to stdout."""
    return pd.DataFrame(
        {
            "Column": dataframe.columns,
            "Non-Null Count": dataframe.notna().sum().values,
            "Dtype": dataframe.dtypes.astype(str).values,
        }
    )


def preprocess_data(games_data, dlcs_data, reviews_data):
    """Preprocess all datasets."""
    if games_data is None:
        return None, None

    cols_to_drop = [
        "description",
        "developers",
        "header_image",
        "publishers",
        "short_description",
        "total_english_reviews",
        "url",
        "website",
    ]
    games_clean = games_data.drop(
        [col for col in cols_to_drop if col in games_data.columns], axis=1
    ).copy()

    if "release_date" in games_clean.columns:
        games_clean["release_date"] = pd.to_datetime(
            games_clean["release_date"], format="%b %d, %Y", errors="coerce"
        )
        games_clean["year"] = games_clean["release_date"].dt.year

    review_cols = {"total_positive", "total_negative", "total_reviews"}
    if review_cols.issubset(games_clean.columns):
        total_reviews = games_clean["total_reviews"].where(
            games_clean["total_reviews"] != 0
        )
        games_clean["positive_pct"] = (
            games_clean["total_positive"].div(total_reviews).mul(100)
        )
        games_clean["negative_pct"] = (
            games_clean["total_negative"].div(total_reviews).mul(100)
        )

    if "tag" in games_clean.columns:
        games_clean["tag"] = games_clean["tag"].fillna("").astype(str)
        games_clean["primary_tag"] = (
            games_clean["tag"].str.split(",").str[0].str.strip()
        )
        games_clean.loc[games_clean["primary_tag"] == "", "primary_tag"] = None

    if "genres" in games_clean.columns:
        games_clean["genres"] = games_clean["genres"].apply(
            lambda x: [g.strip() for g in x.split(",")] if isinstance(x, str) else x
        )

    if "categories" in games_clean.columns:
        games_clean["categories"] = games_clean["categories"].apply(
            lambda x: [c.strip() for c in x.split(",")] if isinstance(x, str) else x
        )

    if dlcs_data is not None and {"parent_app_id", "app_id", "price"}.issubset(
        dlcs_data.columns
    ):
        dlcs_agg = (
            dlcs_data.groupby("parent_app_id")
            .agg(dlc_count=("app_id", "count"), total_dlc_price=("price", "sum"))
            .reset_index()
        )
        games_clean = games_clean.merge(
            dlcs_agg, left_on="app_id", right_on="parent_app_id", how="left"
        )
    elif dlcs_data is not None:
        st.warning(
            "DLC collection was loaded but is missing parent_app_id, app_id, or price."
        )

    merged_data = None
    if reviews_data is not None and "parent_app_id" in reviews_data.columns:
        reviews_clean = reviews_data.drop(
            ["recommendationid", "review_text", "received_for_free"],
            axis=1,
            errors="ignore",
        ).copy()

        enc = LabelEncoder()
        for col in [
            "recommendation",
            "review_score",
            "steam_purchase",
            "written_during_early_access",
        ]:
            if col in reviews_clean.columns:
                reviews_clean[col] = enc.fit_transform(reviews_clean[col].astype(str))

        merged_data = reviews_clean.merge(
            games_clean,
            left_on="parent_app_id",
            right_on="app_id",
            how="left",
            suffixes=("_review", "_game"),
        )

        if (
            "parent_app_id" in merged_data.columns
            and "steam_purchase" in merged_data.columns
        ):
            purchased_data = (
                merged_data.groupby("parent_app_id")["steam_purchase"]
                .sum()
                .reset_index()
            )
            purchased_data.columns = ["parent_app_id", "total_steam_purchases"]
            merged_data = merged_data.merge(
                purchased_data,
                left_on="app_id_game",
                right_on="parent_app_id",
                how="left",
            )
    elif reviews_data is not None:
        st.warning("Reviews collection was loaded but is missing parent_app_id.")

    return games_clean, merged_data
