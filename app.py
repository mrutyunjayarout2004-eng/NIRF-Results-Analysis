import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="NIRF 2025 Analytics",
    page_icon="🎓",
    layout="wide"
)

# Load dataset
@st.cache_data
def load_data():
    df = pd.read_csv("nirf_master_2025.csv")
    df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
    df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    return df

df = load_data()

# Header
st.title("🎓 NIRF India Rankings 2025")
st.caption(
    "Interactive analysis of the selected top-100 records "
    "in six NIRF ranking categories."
)

# Sidebar filters
st.sidebar.header("Dashboard Filters")

categories = sorted(df["Category"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Select categories",
    categories,
    default=categories
)

states = sorted(df["State"].dropna().unique())
selected_states = st.sidebar.multiselect(
    "Select states",
    states,
    default=states
)

max_rank = st.sidebar.slider(
    "Maximum rank",
    min_value=1,
    max_value=100,
    value=100
)

search = st.sidebar.text_input("Search institution")

filtered = df[
    df["Category"].isin(selected_categories)
    & df["State"].isin(selected_states)
    & (df["Rank"] <= max_rank)
].copy()

if search.strip():
    filtered = filtered[
        filtered["Name"].str.contains(
            search.strip(), case=False, na=False
        )
    ]

# KPI cards
c1, c2, c3, c4 = st.columns(4)

c1.metric("Ranking Records", f"{len(filtered):,}")
c2.metric(
    "Unique Institutions",
    f"{filtered['Institute ID'].nunique():,}"
)
c3.metric("Categories", f"{filtered['Category'].nunique()}")
c4.metric(
    "Average Score",
    f"{filtered['Score'].mean():.2f}"
    if not filtered.empty else "N/A"
)

st.divider()

# Charts
left, right = st.columns(2)

with left:
    st.subheader("Average Score by Category")
    if not filtered.empty:
        category_scores = (
            filtered.groupby("Category", as_index=False)["Score"]
            .mean()
            .sort_values("Score", ascending=False)
        )

        fig1 = px.bar(
            category_scores,
            x="Category",
            y="Score",
            color="Category",
            title="Mean score of filtered records",
            text_auto=".2f"
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No records match the selected filters.")

with right:
    st.subheader("Top States by Record Count")
    if not filtered.empty:
        state_counts = (
            filtered.groupby("State", as_index=False)
            .size()
            .rename(columns={"size": "Records"})
            .sort_values("Records", ascending=False)
            .head(10)
        )

        fig2 = px.bar(
            state_counts,
            x="Records",
            y="State",
            orientation="h",
            title="Top 10 states in filtered records",
            text="Records"
        )
        fig2.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No records match the selected filters.")

# Data table
st.subheader("Institution Rankings")
st.caption(
    "Institutions may appear in multiple categories. "
    "Scores should be compared within the relevant ranking category."
)

if not filtered.empty:
    table = filtered.sort_values(
        ["Category", "Rank", "Name"]
    )

    st.dataframe(
        table[
            ["Rank", "Name", "Category", "Score",
             "City", "State", "Institute ID", "Year"]
        ],
        use_container_width=True,
        hide_index=True
    )

    csv = table.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download filtered data (CSV)",
        data=csv,
        file_name="nirf_2025_filtered.csv",
        mime="text/csv"
    )
else:
    st.warning("No institutions found. Change your filters.")
