
import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="NIRF 2025 | Analytics",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0b1120 0%, #111827 100%);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }
    h1, h2, h3 {
        letter-spacing: -0.5px;
    }
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid #334155;
        padding: 18px;
        border-radius: 14px;
    }
    div[data-testid="stMetricLabel"] {
        color: #cbd5e1;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
    }
    div[data-testid="stTabs"] button {
        font-weight: 600;
    }
    .subtitle {
        color: #94a3b8;
        font-size: 1rem;
    }
    .note {
        background: #172033;
        border-left: 4px solid #38bdf8;
        padding: 12px 16px;
        border-radius: 6px;
        color: #dbeafe;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
@st.cache_data
def load_data():
    data = pd.read_csv("nirf_master_2025.csv")

    data["Score"] = pd.to_numeric(data["Score"], errors="coerce")
    data["Rank"] = pd.to_numeric(data["Rank"], errors="coerce")
    data["Year"] = pd.to_numeric(data["Year"], errors="coerce")

    for col in ["Institute ID", "Name", "City", "State", "Category"]:
        data[col] = data[col].astype("string").str.strip()

    return data.dropna(
        subset=["Institute ID", "Name", "Category", "Score", "Rank"]
    )

df = load_data()

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("🎓 NIRF India Rankings 2025")
st.markdown(
    '<p class="subtitle">Explore institutional rankings, '
    'performance patterns and geographic distribution.</p>',
    unsafe_allow_html=True
)

st.caption("Data scope: selected top-100 records from six ranking categories.")

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.title("⚙️ Dashboard Controls")
st.sidebar.caption("Filters apply to the Overview, Performance and Explorer tabs.")

all_categories = sorted(df["Category"].dropna().unique())
all_states = sorted(df["State"].dropna().unique())

selected_categories = st.sidebar.multiselect(
    "Ranking categories",
    all_categories,
    default=all_categories
)

selected_states = st.sidebar.multiselect(
    "States and UTs",
    all_states,
    default=all_states
)

max_rank = st.sidebar.slider(
    "Maximum rank",
    min_value=1,
    max_value=100,
    value=100
)

score_range = st.sidebar.slider(
    "Score range",
    min_value=0.0,
    max_value=100.0,
    value=(0.0, 100.0),
    step=1.0
)

search_text = st.sidebar.text_input(
    "Search institution",
    placeholder="e.g. IIT Madras"
)

filtered = df[
    df["Category"].isin(selected_categories)
    & df["State"].isin(selected_states)
    & (df["Rank"] <= max_rank)
    & df["Score"].between(score_range[0], score_range[1])
].copy()

if search_text.strip():
    filtered = filtered[
        filtered["Name"].str.contains(
            search_text.strip(), case=False, na=False
        )
    ]

# --------------------------------------------------
# HELPER
# --------------------------------------------------
def show_empty():
    st.info("No records match these filters. Try widening your selections.")

# --------------------------------------------------
# TABS
# --------------------------------------------------
overview_tab, performance_tab, compare_tab, explorer_tab, about_tab = st.tabs([
    "📊 Overview",
    "📈 Performance Analysis",
    "🏛️ Institution Comparison",
    "🔎 Data Explorer",
    "ℹ️ Methodology"
])

# --------------------------------------------------
# TAB 1: OVERVIEW
# --------------------------------------------------
with overview_tab:
    st.subheader("Dataset at a glance")

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Ranking Records", f"{len(filtered):,}")
    k2.metric(
        "Unique Institutions",
        f"{filtered['Institute ID'].nunique():,}"
    )
    k3.metric("Categories", f"{filtered['Category'].nunique()}")
    k4.metric("States / UTs", f"{filtered['State'].nunique()}")

    st.markdown("### Ranking landscape")

    if filtered.empty:
        show_empty()
    else:
        left, right = st.columns(2)

        with left:
            category_counts = (
                filtered.groupby("Category", as_index=False)
                .size()
                .rename(columns={"size": "Records"})
                .sort_values("Records", ascending=False)
            )

            fig = px.bar(
                category_counts,
                x="Category",
                y="Records",
                color="Category",
                text="Records",
                title="Records by ranking category",
                template="plotly_dark"
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with right:
            state_counts = (
                filtered.groupby("State", as_index=False)
                .size()
                .rename(columns={"size": "Records"})
                .sort_values("Records", ascending=False)
                .head(10)
                .sort_values("Records")
            )

            fig = px.bar(
                state_counts,
                x="Records",
                y="State",
                orientation="h",
                text="Records",
                title="Top 10 states by record count",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Highest-ranked institutions in the selection")

        top_records = filtered.sort_values(
            ["Category", "Rank", "Name"]
        ).groupby("Category", group_keys=False).head(3)

        st.dataframe(
            top_records[
                ["Category", "Rank", "Name", "Score", "City", "State"]
            ],
            hide_index=True,
            use_container_width=True
        )

    st.markdown(
        '<div class="note">A record represents an institution in a particular '
        'ranking category. Institutions listed in multiple categories are '
        'counted once per category in the record total.</div>',
        unsafe_allow_html=True
    )

# --------------------------------------------------
# TAB 2: PERFORMANCE ANALYSIS
# --------------------------------------------------
with performance_tab:
    st.subheader("Performance patterns")

    available_categories = sorted(filtered["Category"].dropna().unique())

    if filtered.empty:
        show_empty()
    else:
        analysis_category = st.selectbox(
            "Choose one category for score and rank analysis",
            available_categories,
            key="performance_category"
        )

        cat_df = filtered[
            filtered["Category"] == analysis_category
        ].copy()

        left, right = st.columns(2)

        with left:
            score_fig = px.histogram(
                cat_df,
                x="Score",
                nbins=15,
                title=f"Score distribution — {analysis_category}",
                labels={"Score": "NIRF score"},
                template="plotly_dark"
            )
            st.plotly_chart(score_fig, use_container_width=True)

        with right:
            scatter_fig = px.scatter(
                cat_df,
                x="Rank",
                y="Score",
                hover_name="Name",
                hover_data=["City", "State", "Institute ID"],
                title="Rank versus score",
                labels={"Rank": "NIRF rank", "Score": "NIRF score"},
                template="plotly_dark"
            )
            scatter_fig.update_xaxes(autorange="reversed")
            st.plotly_chart(scatter_fig, use_container_width=True)

        st.markdown("### Score summary for selected category")

        summary = cat_df["Score"].describe().to_frame().T
        summary.index = [analysis_category]
        st.dataframe(summary.round(2), use_container_width=True)

        st.caption(
            "Analysis is category-specific. A score in one NIRF category "
            "should not be interpreted as directly equivalent to a score "
            "in another category."
        )

# --------------------------------------------------
# TAB 3: INSTITUTION COMPARISON
# --------------------------------------------------
with compare_tab:
    st.subheader("Compare institutions")

    comparison_category = st.selectbox(
        "Select ranking category",
        all_categories,
        key="comparison_category"
    )

    comparison_df = df[
        df["Category"] == comparison_category
    ].copy()

    # Use IDs as selection values so similarly named institutions
    # remain distinguishable.
    name_lookup = comparison_df.set_index("Institute ID")["Name"].to_dict()
    location_lookup = comparison_df.set_index("Institute ID").apply(
        lambda row: f"{row['Name']} — {row['City']}, {row['State']}",
        axis=1
    ).to_dict()

    chosen_ids = st.multiselect(
        "Choose up to 10 institutions",
        options=comparison_df["Institute ID"].tolist(),
        format_func=lambda x: f"{location_lookup.get(x, name_lookup.get(x, x))} [{x}]",
        max_selections=10,
        key="comparison_ids"
    )

    if chosen_ids:
        chosen = comparison_df[
            comparison_df["Institute ID"].isin(chosen_ids)
        ].copy()

        chosen = chosen.sort_values("Rank")

        left, right = st.columns(2)

        with left:
            fig = px.bar(
                chosen.sort_values("Score", ascending=False),
                x="Name",
                y="Score",
                color="Score",
                hover_data=["Institute ID", "City", "State", "Rank"],
                title="Score comparison",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            fig = px.bar(
                chosen.sort_values("Rank"),
                x="Name",
                y="Rank",
                hover_data=["Institute ID", "City", "State", "Score"],
                title="Rank comparison (lower is better)",
                template="plotly_dark"
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            chosen[
                ["Rank", "Name", "Institute ID", "Score", "City", "State"]
            ],
            hide_index=True,
            use_container_width=True
        )

        st.download_button(
            "⬇️ Download comparison",
            data=chosen.to_csv(index=False).encode("utf-8"),
            file_name="nirf_institution_comparison.csv",
            mime="text/csv"
        )
    else:
        st.info("Select institutions above to compare their scores and ranks.")

    st.caption(
        "Comparison is limited to the selected category and available top-100 records."
    )

# --------------------------------------------------
# TAB 4: DATA EXPLORER
# --------------------------------------------------
with explorer_tab:
    st.subheader("Explore ranking records")

    if filtered.empty:
        show_empty()
    else:
        st.write(f"Showing **{len(filtered):,}** matching records.")

        sort_column = st.selectbox(
            "Sort table by",
            ["Rank", "Score", "Name", "State", "Category"],
            key="sort_column"
        )

        ascending = sort_column in ["Rank", "Name", "State", "Category"]

        table = filtered.sort_values(
            sort_column,
            ascending=ascending
        )

        st.dataframe(
            table[
                ["Rank", "Name", "Category", "Score",
                 "City", "State", "Institute ID", "Year"]
            ],
            hide_index=True,
            use_container_width=True,
            height=520
        )

        st.download_button(
            "⬇️ Download filtered records",
            data=table.to_csv(index=False).encode("utf-8"),
            file_name="nirf_2025_filtered_records.csv",
            mime="text/csv"
        )

# --------------------------------------------------
# TAB 5: METHODOLOGY
# --------------------------------------------------
with about_tab:
    st.subheader("About this project")

    st.markdown("""
    **Objective**

    Explore selected institutional ranking records published under NIRF India
    Rankings 2025 using interactive data analysis and visualization.

    **Dataset scope**

    - Overall
    - Universities
    - Engineering
    - Colleges
    - Management
    - Pharmacy

    Each category contributes up to 100 records to this dataset.

    **How to interpret the dashboard**

    - Rank 1 represents the highest position within a category.
    - Score comparisons should be made within the same category.
    - State record counts show the geographic distribution of the selected records,
      not the complete distribution of all Indian institutions.
    - An institution may appear in multiple categories.
    - Repeated rank numbers can occur and should not automatically be treated as errors.

    **Technology stack**

    Python, Pandas, Streamlit and Plotly.

    **Data quality**

    The dataset was checked for missing values, invalid score and rank ranges,
    duplicate IDs within categories, and inconsistent names for the same ID.

    **Limitations**

    This dashboard analyzes selected top-100 records in six categories, not the
    complete NIRF database. Results are descriptive and do not establish causal
    relationships or predict future rankings.
    """)

    st.markdown(
        "[Official NIRF India Rankings](https://www.nirfindia.org/Rankings/2025/Ranking.html)"
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()
st.caption(
    "NIRF India Rankings 2025 • Educational analytics project • "
    "Interpret comparisons within the relevant ranking category."
)
