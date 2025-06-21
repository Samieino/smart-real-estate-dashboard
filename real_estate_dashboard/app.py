import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

###############################################################################
# Smart Real Estate Dashboard – Graduation Project (Egypt)                    #
# Author: Team – Smart Real Estate Platform                                  #
# This Streamlit app offers an interactive, professional‑grade dashboard     #
# showcasing key insights, filtering, comparison tools, and export options.  #
###############################################################################

# ──────────────────────────────  PAGE CONFIG  ────────────────────────────── #
st.set_page_config(
    page_title="Smart Real Estate Dashboard – Egypt 🇪🇬",
    page_icon="🏘️",
    layout="wide",
)

# ───────────────────────────────  LOAD DATA  ─────────────────────────────── #
@st.cache_data
def load_data(path: str = "clean_data_readable.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    # Ensure numeric columns are correct dtype
    num_cols = ["price", "area", "bedrooms", "bathrooms", "level"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df.dropna(subset=["price", "area"], inplace=True)
    # Feature engineering
    df["rooms"] = df["bedrooms"] + df["bathrooms"]
    df["price_per_m2"] = df["price"] / df["area"]
    df["log_price"] = np.log1p(df["price"])
    return df

# Path can be changed from sidebar if needed
data_path_default = r"C:\Users\Alhandsya\Downloads\beforeencoding_data.csv"

df = load_data(data_path_default)

# ───────────────────────────── SIDEBAR FILTERS ───────────────────────────── #
st.sidebar.header("🔍 Filter Options")

# City filter
cities = st.sidebar.multiselect(
    "City", options=sorted(df["city"].unique()), default=sorted(df["city"].unique()))

# Property type filter
prop_types = st.sidebar.multiselect(
    "Property Type", options=sorted(df["type"].unique()), default=sorted(df["type"].unique()))

# Rent/Sale filter
rent_opts = st.sidebar.multiselect(
    "Listing Type", options=sorted(df["rent"].unique()), default=sorted(df["rent"].unique()))

# Furnished filter
furn_opts = st.sidebar.multiselect(
    "Furnished Status", options=sorted(df["furnished"].unique()), default=sorted(df["furnished"].unique()))

# Numeric sliders
price_min, price_max = int(df["price"].min()), int(df["price"].max())
sel_price = st.sidebar.slider("Price range (EGP)", price_min, price_max, (price_min, price_max), step=5000)

area_min, area_max = int(df["area"].min()), int(df["area"].max())
sel_area = st.sidebar.slider("Area range (m²)", area_min, area_max, (area_min, area_max), step=5)

# Bedrooms & bathrooms
sel_bed = st.sidebar.select_slider(
    "Bedrooms", options=sorted(df["bedrooms"].unique()), value=(df["bedrooms"].min(), df["bedrooms"].max()))
sel_bath = st.sidebar.select_slider(
    "Bathrooms", options=sorted(df["bathrooms"].unique()), value=(df["bathrooms"].min(), df["bathrooms"].max()))

# Apply filters
df_filtered = df[
    (df["city"].isin(cities))
    & (df["type"].isin(prop_types))
    & (df["rent"].isin(rent_opts))
    & (df["furnished"].isin(furn_opts))
    & (df["price"].between(*sel_price))
    & (df["area"].between(*sel_area))
    & (df["bedrooms"].between(*sel_bed))
    & (df["bathrooms"].between(*sel_bath))
]

st.sidebar.markdown("---")
# Comparison selector
compare_ids = st.sidebar.multiselect("🔄 Compare by Ad ID", options=df_filtered["ad_id"].unique())

# Download button
csv = df_filtered.to_csv(index=False).encode("utf-8")
st.sidebar.download_button("📥 Download Filtered Data", csv, "filtered_listings.csv", "text/csv")

# ─────────────────────────────  MAIN DASHBOARD  ──────────────────────────── #
st.title("🏘️ Smart Real Estate Dashboard – Egypt")

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Listings", f"{len(df_filtered):,}")
col2.metric("Average Price", f"{df_filtered['price'].mean():,.0f} EGP")
col3.metric("Median Area", f"{df_filtered['area'].median():.0f} m²")
col4.metric("Average Price per m²", f"{df_filtered['price_per_m2'].mean():,.0f} EGP")

# Tabs
overview_tab, listings_tab, compare_tab = st.tabs(["📊 Overview", "📄 Listings", "⚖️ Compare"])

# ────────────────────────────────  OVERVIEW TAB  ──────────────────────────── #
with overview_tab:
    st.subheader("Price Distribution")
    bins = st.slider("Number of bins", 10, 100, 50, 5)
    fig_hist = px.histogram(df_filtered, x="price", nbins=bins, color_discrete_sequence=["indianred"])
    fig_hist.update_layout(xaxis_title="Price (EGP)", yaxis_title="Count")
    st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader("Average Price by Property Type")
    type_price = (
        df_filtered.groupby("type")["price"].mean().sort_values(ascending=False).reset_index()
    )
    st.plotly_chart(px.bar(type_price, x="type", y="price", color="type"), use_container_width=True)

    st.subheader("Listings per City – Top 15")
    top_cities = df_filtered["city"].value_counts().head(15).reset_index()
    top_cities.columns = ["city", "count"]
    st.plotly_chart(px.bar(top_cities, x="city", y="count", color="city"), use_container_width=True)

    st.subheader("Correlation Heatmap (numeric)")
    corr_cols = ["log_price", "area", "bedrooms", "bathrooms", "rooms", "price_per_m2"]
    corr = df_filtered[corr_cols].corr()
    fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu", origin="lower")
    st.plotly_chart(fig_corr, use_container_width=True)

# ───────────────────────────────  LISTINGS TAB  ───────────────────────────── #
with listings_tab:
    st.subheader("Filtered Listings")
    st.dataframe(df_filtered.reset_index(drop=True))

    st.markdown("### Top 20 Most Expensive (Filtered)")
    st.dataframe(df_filtered.sort_values("price", ascending=False).head(20))

# ────────────────────────────────  COMPARE TAB  ───────────────────────────── #
with compare_tab:
    st.subheader("Compare Selected Listings")
    if len(compare_ids) < 2:
        st.info("Select at least two Ad IDs from the sidebar to compare.")
    else:
        comp_df = df_filtered[df_filtered["ad_id"].isin(compare_ids)]
        st.write("### Comparison Table")
        st.dataframe(comp_df.set_index("ad_id"))
        # Simple radar chart comparison for numeric features
        if len(compare_ids) <= 5:
            radar_cols = ["price", "area", "bedrooms", "bathrooms", "rooms"]
            fig = go.Figure()
            for _, row in comp_df.iterrows():
                fig.add_trace(go.Scatterpolar(
                    r=[row[c] for c in radar_cols],
                    theta=radar_cols,
                    fill="toself",
                    name=row["ad_id"][:12]
                ))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

# ───────────────────────────────  FOOTER  ─────────────────────────────────── #
st.markdown("---")
st.markdown(
    "Developed by **Smart Real Estate Platform Team** – Faculty of Engineering, Al‑Azhar University Cairo"
)
