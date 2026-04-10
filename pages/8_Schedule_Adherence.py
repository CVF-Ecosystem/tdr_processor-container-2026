# pages/8_Schedule_Adherence.py
"""Schedule Adherence — Planned vs Actual (ETB/ATB, ETD/ATD, ATC vs ETD)."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard_shared import (
    apply_chart_theme, init_lang, kpi_card, load_all_data,
    render_export_sidebar, render_language_selector, render_sidebar_filters,
    render_aggrid_table, t,
)

_DT_COLS = ["ETB", "ATB", "ETD", "ATD", "Completed Loading", "Lashing Finished"]
_THRESHOLD_MIN = 30  # ±30 phút → xem là "đúng giờ"


def _delta_min(later: pd.Series, earlier: pd.Series) -> pd.Series:
    """Return signed difference in minutes (later − earlier). NaT → NaN."""
    return (later - earlier).dt.total_seconds().div(60).round(1)


def _status(val: float) -> str:
    if pd.isna(val):
        return "—"
    if val > _THRESHOLD_MIN:
        return t("sa_late")
    if val < -_THRESHOLD_MIN:
        return t("sa_early")
    return t("sa_on_time")


def _bar_diverging(df: pd.DataFrame, x_col: str, y_col: str, title: str):
    """Bar chart với màu: đỏ = trễ (>0), xanh lá = sớm (<0)."""
    colors = df[y_col].apply(
        lambda v: "#DC2626" if v > _THRESHOLD_MIN
        else ("#16A34A" if v < -_THRESHOLD_MIN else "#D97706")
    )
    fig = go.Figure(go.Bar(
        x=df[x_col], y=df[y_col],
        marker_color=colors,
        text=df[y_col].apply(lambda v: f"{v:+.0f}" if not pd.isna(v) else ""),
        textposition="outside",
    ))
    fig.add_hline(y=_THRESHOLD_MIN,  line_dash="dot", line_color="#DC2626", annotation_text=f"+{_THRESHOLD_MIN} min")
    fig.add_hline(y=-_THRESHOLD_MIN, line_dash="dot", line_color="#16A34A", annotation_text=f"−{_THRESHOLD_MIN} min")
    fig.add_hline(y=0, line_color="#94a3b8", line_width=1)
    apply_chart_theme(fig, title)
    return fig


# ── Main ──────────────────────────────────────────────────────────────────────
init_lang()
render_language_selector()
df_vessel_raw, df_qc, df_delay, df_container, df_qc_operator = load_all_data()
df_vessel = render_sidebar_filters(df_vessel_raw)
render_export_sidebar(df_vessel_raw, df_qc, df_qc_operator, df_delay, df_container)

st.title(f"🕐 {t('sa_header')}")
st.caption(t("sa_info"))
st.markdown("---")

if df_vessel.empty:
    st.warning(t("data_not_found_warning"))
    st.stop()

# Kiểm tra cột ETB/ETD
missing_cols = [c for c in ["ETB", "ETD"] if c not in df_vessel.columns]
if missing_cols:
    st.warning(t("sa_no_etb"))
    st.info(t("sa_current_cols") + ": " + ", ".join(df_vessel.columns.tolist()))
    st.stop()

# Parse datetime
df = df_vessel.copy()
for col in _DT_COLS:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

# Tính các chỉ số lệch thời gian
df["_berth_delay"]  = _delta_min(df["ATB"], df["ETB"])          # ATB − ETB
df["_depart_delay"] = _delta_min(df["ATD"], df["ETD"])          # ATD − ETD

if "Completed Loading" in df.columns:
    df["_atc_vs_etd"] = _delta_min(df["Completed Loading"], df["ETD"])  # ATC − ETD  (<0 = xong sớm hơn ETD)
    df["_idle"]       = _delta_min(df["ATD"], df["Completed Loading"])  # ATD − ATC
else:
    df["_atc_vs_etd"] = pd.NA
    df["_idle"]       = pd.NA

# ── KPI cards ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

avg_berth  = df["_berth_delay"].mean()
avg_depart = df["_depart_delay"].mean()
avg_atc    = df["_atc_vs_etd"].mean()
avg_idle   = df["_idle"].mean()

with c1:
    color = "#DC2626" if avg_berth > _THRESHOLD_MIN else "#16A34A"
    kpi_card(t("sa_metric_berth_delay"), f"{avg_berth:+.0f}" if not pd.isna(avg_berth) else "N/A", color=color)
with c2:
    color = "#DC2626" if avg_depart > _THRESHOLD_MIN else "#16A34A"
    kpi_card(t("sa_metric_depart_delay"), f"{avg_depart:+.0f}" if not pd.isna(avg_depart) else "N/A", color=color)
with c3:
    color = "#16A34A" if not pd.isna(avg_atc) and avg_atc < 0 else "#D97706"
    kpi_card(t("sa_metric_atc_vs_etd"), f"{avg_atc:+.0f}" if not pd.isna(avg_atc) else "N/A", color=color)
with c4:
    color = "#D97706" if not pd.isna(avg_idle) and avg_idle > 60 else "#2563EB"
    kpi_card(t("sa_metric_idle"), f"{avg_idle:.0f}" if not pd.isna(avg_idle) else "N/A", color=color)

st.caption(t("sa_threshold_caption", min=_THRESHOLD_MIN))
st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_tbl, tab_berth, tab_depart, tab_idle = st.tabs([
    t("sa_tab_table"), t("sa_tab_berth"), t("sa_tab_depart"), t("sa_tab_idle")
])

# Label columns
_LABEL_MAP = {
    "Vessel Name":        t("sa_col_vessel"),
    "Voyage":             t("sa_col_voyage"),
    "Operator":           "Operator",
    "Berth":              "Berth",
    "ETB":                t("sa_col_etb"),
    "ATB":                t("sa_col_atb"),
    "_berth_delay":       t("sa_col_berth_delay"),
    "ETD":                t("sa_col_etd"),
    "ATD":                t("sa_col_atd"),
    "_depart_delay":      t("sa_col_depart_delay"),
    "Completed Loading":  t("sa_col_atc"),
    "_atc_vs_etd":        t("sa_col_atc_vs_etd"),
    "_idle":              t("sa_col_idle"),
}

_display_cols = [c for c in _LABEL_MAP if c in df.columns or c.startswith("_")]
df_display = df[_display_cols].rename(columns=_LABEL_MAP).copy()

# Thêm cột trạng thái
df_display[t("sa_status_berth")] = df["_berth_delay"].apply(_status)
df_display[t("sa_status_depart")] = df["_depart_delay"].apply(_status)

# Định dạng datetime → str cho hiển thị
for col_orig, col_label in _LABEL_MAP.items():
    if col_label in df_display.columns and col_orig in _DT_COLS:
        df_display[col_label] = df_display[col_label].dt.strftime("%d/%m %H:%M").fillna("—")

with tab_tbl:
    st.subheader(t("sa_tab_table"))
    st.dataframe(
        df_display,
        use_container_width=True,
        column_config={
            t("sa_col_berth_delay"):  st.column_config.NumberColumn(format="%.0f min"),
            t("sa_col_depart_delay"): st.column_config.NumberColumn(format="%.0f min"),
            t("sa_col_atc_vs_etd"):   st.column_config.NumberColumn(format="%.0f min"),
            t("sa_col_idle"):         st.column_config.NumberColumn(format="%.0f min"),
        },
    )

with tab_berth:
    df_b = df[["Vessel Name", "_berth_delay"]].dropna()
    if df_b.empty:
        st.info(t("no_data_etb_atb"))
    else:
        df_b = df_b.groupby("Vessel Name", as_index=False)["_berth_delay"].mean().round(1)
        df_b = df_b.sort_values("_berth_delay", ascending=False)
        st.plotly_chart(
            _bar_diverging(df_b, "Vessel Name", "_berth_delay", t("sa_chart_berth")),
            use_container_width=True,
        )
        st.caption(t("sa_legend_diverging"))

with tab_depart:
    df_d = df[["Vessel Name", "_depart_delay"]].dropna()
    if df_d.empty:
        st.info(t("no_data_etd_atd"))
    else:
        df_d = df_d.groupby("Vessel Name", as_index=False)["_depart_delay"].mean().round(1)
        df_d = df_d.sort_values("_depart_delay", ascending=False)
        st.plotly_chart(
            _bar_diverging(df_d, "Vessel Name", "_depart_delay", t("sa_chart_depart")),
            use_container_width=True,
        )
        st.caption(t("sa_legend_diverging"))

with tab_idle:
    df_i = df[["Vessel Name", "_idle", "_atc_vs_etd"]].dropna(subset=["_idle"])
    if df_i.empty:
        st.info(t("no_data_atc"))
    else:
        df_i = df_i.groupby("Vessel Name", as_index=False).agg(
            _idle=("_idle", "mean"), _atc_vs_etd=("_atc_vs_etd", "mean")
        ).round(1)
        df_i = df_i.sort_values("_idle", ascending=False)
        fig_idle = px.bar(
            df_i, x="Vessel Name", y="_idle",
            text="_idle",
            title=t("sa_chart_idle"),
            labels={"_idle": t("sa_col_idle"), "Vessel Name": t("sa_col_vessel")},
            color="_idle",
            color_continuous_scale=["#16A34A", "#D97706", "#DC2626"],
        )
        fig_idle.update_traces(texttemplate="%{text:.0f} min", textposition="outside")
        apply_chart_theme(fig_idle)
        st.plotly_chart(fig_idle, use_container_width=True)

        st.subheader(t("sa_atc_vs_etd_subheader"))
        df_atc = df_i.dropna(subset=["_atc_vs_etd"])
        if not df_atc.empty:
            df_atc = df_atc.sort_values("_atc_vs_etd")
            st.plotly_chart(
                _bar_diverging(df_atc, "Vessel Name", "_atc_vs_etd", t("sa_col_atc_vs_etd")),
                use_container_width=True,
            )
            st.caption(t("sa_atc_legend"))
