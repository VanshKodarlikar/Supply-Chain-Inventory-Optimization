import streamlit as st
from pathlib import Path
import pandas as pd
from typing import Dict

st.set_page_config(
    title="FMCG Supply Chain & Inventory Optimization",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"

# ---------- CSS THEME ----------
CUSTOM_CSS = """
<style>
:root {
  --bg: #0f172a; /* slate-900 */
  --card: #111827; /* gray-900 */
  --accent: #22d3ee; /* cyan-400 */
  --accent-2: #34d399; /* emerald-400 */
  --warn: #fbbf24; /* amber-400 */
  --danger: #f87171; /* red-400 */
  --text: #e5e7eb; /* gray-200 */
}

.stApp { background: linear-gradient(180deg, #0b1220 0%, #0f172a 100%); }

/***** HEADERS *****/
h1, h2, h3, h4, h5, h6, .markdown-text-container, .stMarkdown p { color: var(--text) !important; }

/***** KPI CARDS *****/
.kpi-card {
  background: var(--card);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.35);
}
.kpi-title { font-size: 0.9rem; color: #a5b4fc; margin-bottom: 8px; }
.kpi-value { font-size: 1.8rem; font-weight: 800; color: var(--text); }
.kpi-sub { font-size: 0.8rem; color: #93c5fd; }

/***** TABLES *****/
.dataframe th, .dataframe td { color: var(--text) !important; }

/***** BADGES *****/
.badge { display:inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; }
.badge-warn { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.25); }
.badge-danger { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.25); }
.badge-ok { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.25); }

/***** DOWNLOAD BUTTONS *****/
.stDownloadButton button { background: linear-gradient(135deg, #22d3ee 0%, #34d399 100%);
  color: #0b1220; border: 0; border-radius: 10px; font-weight: 700; }

/***** UPLOADERS *****/
[data-testid="stFileUploaderDropzone"] { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.12); }

/***** SIDEBAR *****/
section[data-testid="stSidebar"] { background: #0b1220; border-right: 1px solid rgba(255,255,255,0.06); }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------- DATA HELPERS ----------

def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

@st.cache_data(show_spinner=False)
def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

@st.cache_data(show_spinner=False)
def get_all_data() -> Dict[str, pd.DataFrame]:
    return {
        "kpis": load_csv(DATA_DIR / "kpis.csv"),
        "forecast": load_csv(DATA_DIR / "forecast.csv"),
        "recommendations": load_csv(DATA_DIR / "recommendations.csv"),
        "sales": load_csv(DATA_DIR / "sales.csv"),
        "inventory": load_csv(DATA_DIR / "inventory.csv"),
        "procurement": load_csv(DATA_DIR / "procurement.csv"),
        "logistics": load_csv(DATA_DIR / "logistics.csv"),
    }

# ---------- UI HELPERS ----------

def kpi_card(title: str, value: str, subtext: str = "") -> None:
    st.markdown(
        f"""
        <div class='kpi-card'>
          <div class='kpi-title'>{title}</div>
          <div class='kpi-value'>{value}</div>
          <div class='kpi-sub'>{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- SIDEBAR FILTERS ----------

def sidebar_filters(df_forecast: pd.DataFrame, df_reco: pd.DataFrame):
    st.sidebar.markdown("## Filters")
    all_skus = sorted(list(set(
        df_forecast.get("sku", pd.Series(dtype=str)).dropna().unique().tolist() +
        df_reco.get("sku", pd.Series(dtype=str)).dropna().unique().tolist()
    )))
    selected_skus = st.sidebar.multiselect("Select SKUs", options=all_skus, default=all_skus[:5])

    all_suppliers = sorted(df_reco.get("supplier", pd.Series(dtype=str)).dropna().unique().tolist())
    selected_suppliers = st.sidebar.multiselect(
        "Select Suppliers", options=all_suppliers, default=all_suppliers[:5] if all_suppliers else []
    )

    date_min = pd.to_datetime(df_forecast.get("date", pd.Series([], dtype="datetime64[ns]"))).min()
    date_max = pd.to_datetime(df_forecast.get("date", pd.Series([], dtype="datetime64[ns]"))).max()
    if pd.isna(date_min) or pd.isna(date_max):
        date_range = None
    else:
        date_range = st.sidebar.date_input("Date range", value=(date_min.date(), date_max.date()))

    return selected_skus, selected_suppliers, date_range

# ---------- PAGES ----------

def page_home():
    st.title("📦 FMCG Supply Chain & Inventory Optimization")
    st.markdown(
        """
        **Welcome!** This app provides an integrated view of your FMCG supply chain:
        - Real-time KPIs and inventory health
        - 🔮 Demand forecasts per SKU
        - ✅ Smart reorder and supplier recommendations
        - 🚚 Transport mode guidance and lead times

        Use the sidebar to navigate between pages and apply filters.
        """
    )

    st.markdown("### Quick Links")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.link_button("KPI Dashboard", "#", type="primary")
    with col2: st.link_button("Forecasting", "#")
    with col3: st.link_button("Recommendations", "#")
    with col4: st.link_button("Download", "#")


def page_kpi_dashboard(data: Dict[str, pd.DataFrame], selected_skus, selected_suppliers):
    df_kpis = data["kpis"].copy()

    st.markdown("## 📊 KPI Dashboard")
    colA, colB, colC, colD, colE = st.columns(5)

    # Extract KPIs with graceful fallbacks
    total_sales = float(df_kpis.get("total_sales", pd.Series([0])).iloc[0]) if not df_kpis.empty else 0.0
    avg_inventory = float(df_kpis.get("avg_inventory_per_sku", pd.Series([0])).iloc[0]) if not df_kpis.empty else 0.0
    stockout_risk = float(df_kpis.get("stockout_risk_pct", pd.Series([0])).iloc[0]) if not df_kpis.empty else 0.0
    avg_lead_time = float(df_kpis.get("avg_lead_time_days", pd.Series([0])).iloc[0]) if not df_kpis.empty else 0.0
    avg_delivery_time = float(df_kpis.get("avg_delivery_time_days", pd.Series([0])).iloc[0]) if not df_kpis.empty else 0.0

    with colA: kpi_card("💰 Total Sales", f"${total_sales:,.0f}")
    with colB: kpi_card("📦 Avg Inventory / SKU", f"{avg_inventory:,.0f}")
    with colC: kpi_card("⚠️ Stockout Risk", f"{stockout_risk:.1f}%")
    with colD: kpi_card("⏱️ Avg Lead Time (Supplier)", f"{avg_lead_time:.1f}d")
    with colE: kpi_card("🚚 Avg Delivery Time (Transport)", f"{avg_delivery_time:.1f}d")

    st.markdown("### Inventory by SKU (Top 10)")
    df_inv = data["inventory"].copy()
    if not df_inv.empty:
        if selected_skus:
            df_inv = df_inv[df_inv["sku"].isin(selected_skus)]
        top_inv = (
            df_inv.groupby("sku", as_index=False)["inventory_qty"].sum()
            .sort_values("inventory_qty", ascending=False)
            .head(10)
        )
        st.bar_chart(top_inv.set_index("sku"))
    else:
        st.info("No inventory data available. Upload CSVs in the sidebar to see charts.")


def page_forecasting(data: Dict[str, pd.DataFrame], selected_skus, date_range):
    st.markdown("## 🔮 Forecasting")
    df_fc = data["forecast"].copy()
    if df_fc.empty:
        st.info("No forecast data available.")
        return

    df_fc["date"] = pd.to_datetime(df_fc["date"])
    if selected_skus:
        df_fc = df_fc[df_fc["sku"].isin(selected_skus)]
    if date_range and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        df_fc = df_fc[(df_fc["date"] >= start) & (df_fc["date"] <= end)]

    # Plotly interactive line chart
    import plotly.express as px
    fig = px.line(
        df_fc,
        x="date",
        y="forecast_qty",
        color="sku",
        title="Forecasted Demand by SKU",
        markers=True,
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e5e7eb")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Forecast Table")
    st.dataframe(
        df_fc.sort_values(["sku", "date"]).reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )


def page_recommendations(data: Dict[str, pd.DataFrame], selected_skus, selected_suppliers):
    st.markdown("## ✅ Recommendations")
    df_rec = data["recommendations"].copy()
    if df_rec.empty:
        st.info("No recommendation data available.")
        return

    if selected_skus:
        df_rec = df_rec[df_rec["sku"].isin(selected_skus)]
    if selected_suppliers:
        df_rec = df_rec[df_rec["supplier"].isin(selected_suppliers)]

    # Emoji urgency for visual cue and sortable text
    def urgency_label(val: str) -> str:
        v = str(val).lower()
        if v == "high":
            return "🔴 High"
        if v == "medium":
            return "🟠 Medium"
        return "🟢 Low"

    display = df_rec.copy()
    if "urgency" in display.columns:
        display["Urgency"] = display["urgency"].apply(urgency_label)

    columns_to_show = [
        "sku","current_stock","reorder_point","recommended_order_qty","supplier","transport_mode","lead_time_days","Urgency"
    ]
    columns_to_show = [c for c in columns_to_show if c in display.columns]

    st.markdown("### Reorder Suggestions")
    st.markdown("Sort columns by clicking headers. Urgent items are indicated with colored icons.")
    st.dataframe(
        display[columns_to_show].sort_values(["Urgency", "sku"]),
        use_container_width=True,
        hide_index=True,
    )

    # Highlight top 10 by forecasted demand if available
    df_fc = data.get("forecast", pd.DataFrame()).copy()
    if not df_fc.empty:
        st.markdown("### Top 10 SKUs by Forecasted Demand")
        top = (
            df_fc.groupby("sku", as_index=False)["forecast_qty"].sum().sort_values("forecast_qty", ascending=False).head(10)
        )
        st.bar_chart(top.set_index("sku"))


def page_downloads(data: Dict[str, pd.DataFrame]):
    st.markdown("## ⬇️ Downloads")
    for key, label in [("recommendations", "Recommendations CSV"), ("forecast", "Forecast CSV"), ("kpis", "KPI Snapshot CSV")]:
        df = data.get(key, pd.DataFrame())
        if df.empty:
            st.warning(f"No {label} found.")
            continue
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"Download {label}",
            data=csv,
            file_name=f"{key}.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ---------- UPLOADERS ----------

def sidebar_uploaders():
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Upload Data")
    mapping = {
        "Sales": "sales.csv",
        "Inventory": "inventory.csv",
        "Procurement": "procurement.csv",
        "Logistics": "logistics.csv",
        "KPIs": "kpis.csv",
        "Forecast": "forecast.csv",
        "Recommendations": "recommendations.csv",
    }
    for label, fname in mapping.items():
        file = st.sidebar.file_uploader(f"Upload {label} CSV", type=["csv"], key=f"u_{label}")
        if file is not None:
            ensure_data_dir()
            path = DATA_DIR / fname
            df = pd.read_csv(file)
            df.to_csv(path, index=False)
            st.sidebar.success(f"Saved {label} to {path.name}")
            st.cache_data.clear()

# ---------- ROUTER ----------

def main():
    ensure_data_dir()
    data = get_all_data()

    # Sidebar nav
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Home", "KPI Dashboard", "Forecasting", "Recommendations", "Download"],
        index=0,
    )

    # Global filters
    selected_skus, selected_suppliers, date_range = sidebar_filters(data["forecast"], data["recommendations"])
    sidebar_uploaders()

    if page == "Home":
        page_home()
    elif page == "KPI Dashboard":
        page_kpi_dashboard(data, selected_skus, selected_suppliers)
    elif page == "Forecasting":
        page_forecasting(data, selected_skus, date_range)
    elif page == "Recommendations":
        page_recommendations(data, selected_skus, selected_suppliers)
    elif page == "Download":
        page_downloads(data)

if __name__ == "__main__":
    main()