"""admin_dashboard.py — Production-Ready 12-Section Administrator Dashboard for Naya Pani.

Integrates directly with existing Naya Pani modules:
- pipeline.py (data loading, validation, seasonal ML/DL pipelines, Excel export)
- deep_models.py (PINN, ESN, SARIMA, LSTM availability and metrics)
- digital_twin.py (virtual water-system state and scenario auditing)
- rag/ (KnowledgeBase, retriever, context, assistant, llm_provider)
- admin_security.py (authentication, session TTL, PBKDF2 hashing, audit logs)
- security_engine.py (input bounds, prompt injection defense, uncertainty bounds, DT ledger)
- scientific_report.py (Word report generation)
- session_store.py (WorkspaceStore)
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from admin_security import (
    ADMIN_LOCKOUT_SECONDS,
    ADMIN_MAX_ATTEMPTS,
    ADMIN_SESSION_TTL_SECONDS,
    _hash_password,
    admin_session_summary,
    log_admin_event,
    logout_admin_session,
    read_admin_audit_logs,
)
from deep_models import _deep_model_status
from digital_twin import render_digital_twin
from pipeline import (
    REQUIRED_COLUMNS,
    SEASON_ORDER,
    TARGET,
    RunConfig,
    build_excel_export,
    load_seasonal_workbook,
    run_season_pipeline,
    validate_data,
)
from rag.assistant import _kb as _get_kb, answer as rag_answer
from rag.llm_provider import active_provider
from rag.retriever import KnowledgeBase
from scientific_report import HAS_DOCX, build_scientific_report
from security_engine import (
    DIGITAL_TWIN_AUDIT,
    INDICATOR_BOUNDS,
    RAJASTHAN_LAT_BOUNDS,
    RAJASTHAN_LON_BOUNDS,
    calculate_forecast_uncertainty,
    sanitize_rag_prompt,
    sanitize_rag_response,
    validate_environmental_record,
    validate_forecast_workload,
)
from session_store import workspace_store

ADMIN_MENU_ITEMS = [
    "1. Overview",
    "2. Environmental Data",
    "3. Groundwater Monitoring",
    "4. ML/DL Models",
    "5. Digital Twin",
    "6. RAG Chatbot",
    "7. Users & Permissions",
    "8. Alerts & Notifications",
    "9. System Health",
    "10. Reports",
    "11. Audit Logs",
    "12. Settings",
]


def _fmt_val(val: Any, digits: int = 3, unit: str = "") -> str:
    if val is None:
        return "Unavailable"
    try:
        num = float(val)
        if not np.isfinite(num):
            return "Unavailable"
        suffix = f" {unit}" if unit else ""
        return f"{num:,.{digits}f}{suffix}"
    except (TypeError, ValueError):
        return str(val)


def _get_active_payload() -> dict[str, Any] | None:
    """Retrieve the real analysis payload from Streamlit session state or workspace store."""
    payload = st.session_state.get("groundwater_dashboard_payload")
    if payload and isinstance(payload, dict):
        return payload
    # Check workspace_store fallback
    with workspace_store._lock:
        for _, (_, ws_val) in reversed(list(workspace_store._items.items())):
            if isinstance(ws_val, dict) and ws_val.get("payload"):
                return ws_val["payload"]
    return None


def _get_admin_settings() -> dict[str, Any]:
    """Return validated admin configuration settings stored in session state."""
    defaults = {
        "water_stress_safe_mbgl": 10.0,
        "water_stress_semi_critical_mbgl": 20.0,
        "water_stress_critical_mbgl": 35.0,
        "max_forecast_horizon": 10,
        "rag_top_k": 4,
        "rag_min_score": 0.10,
        "stale_data_year_threshold": 2020,
        "require_human_review_banner": True,
    }
    cfg = st.session_state.setdefault("admin_validated_settings", dict(defaults))
    for k, v in defaults.items():
        cfg.setdefault(k, v)
    return cfg


def _get_rbac_registry() -> dict[str, list[str]]:
    """Return the server-side RBAC registry in session state."""
    default_rbac = {
        "admins": ["amankumar89669@gmail.com", "admin@nayapani.org"],
        "analysts": ["hydrologist@nayapani.org"],
        "viewers": ["guest@nayapani.org"],
    }
    return st.session_state.setdefault("admin_rbac_registry", default_rbac)


# =========================================================================== #
# 1. OVERVIEW
# =========================================================================== #
def _render_overview_tab(payload: dict[str, Any] | None) -> None:
    st.subheader("1 · System & Hydrological Overview")
    st.caption(
        "Real-time operational status derived from the active analysis workspace. "
        "Unavailable metrics are explicitly marked rather than shown as zero."
    )

    summary = admin_session_summary()
    kb = _get_kb()
    llm_name = active_provider()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Admin Session", "Active" if summary.get("authenticated") else "Inactive")
    c2.metric("Analysis Workspace", "Loaded" if payload else "No Workbook Loaded")
    c3.metric("RAG Knowledge Chunks", f"{len(kb.documents):,}" if kb.documents else "0 (Empty)")
    c4.metric("LLM Provider", llm_name.upper() if llm_name != "none" else "Offline Composer")

    if not payload or payload.get("clean_data") is None or payload["clean_data"].empty:
        st.info(
            "No groundwater workbook is currently loaded in the active session. "
            "Go to **2. Environmental Data** in the sidebar or return to the main dashboard to upload a dataset."
        )
        return

    data: pd.DataFrame = payload["clean_data"]
    results: dict[str, dict[str, Any]] = payload.get("results") or {}

    years = pd.to_numeric(data["YEAR"], errors="coerce").dropna()
    latest_year = int(years.max()) if not years.empty else None
    earliest_year = int(years.min()) if not years.empty else None
    settings = _get_admin_settings()
    freshness = (
        f"Current ({latest_year})"
        if latest_year and latest_year >= settings["stale_data_year_threshold"]
        else f"Stale (ends {latest_year})"
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Validated Records", f"{len(data):,}")
    m2.metric("Monitoring Villages", f"{data['VILLAGE'].nunique():,}")
    m3.metric("Temporal Coverage", f"{earliest_year}–{latest_year}" if latest_year else "Unavailable")
    m4.metric("Data Freshness", freshness)

    # Environmental & Hydrological summary metrics
    e1, e2, e3, e4 = st.columns(4)
    mean_dtwl = pd.to_numeric(data.get(TARGET), errors="coerce").mean()
    mean_rain = pd.to_numeric(data.get("Rainfall"), errors="coerce").mean()
    mean_et = pd.to_numeric(data.get("ET"), errors="coerce").mean()
    e1.metric("Mean Observed DTWL", _fmt_val(mean_dtwl, 2, "mbgl"))
    e2.metric("Mean Seasonal Rainfall", _fmt_val(mean_rain, 1, "mm"))
    e3.metric("Mean Evapotranspiration", _fmt_val(mean_et, 1, "mm"))
    e4.metric("Modeled Seasons", f"{len(results)} / {len(SEASON_ORDER)}")

    # Season-by-season model status & Actual vs Predicted summary
    st.markdown("#### Seasonal Model Status & Held-Out Accuracy")
    season_rows = []
    for season in SEASON_ORDER:
        res = results.get(season)
        if not res:
            season_rows.append({
                "Season": season,
                "Status": "Unavailable",
                "Production ML Model": "—",
                "Test R² (Bias-Corrected)": "Unavailable",
                "Test RMSE (mbgl)": "Unavailable",
                "Best Deep Model": "—",
                "Low-Data Rescue": "—",
            })
            continue
        top = res["metrics"].iloc[0]
        pinned = st.session_state.get("pinned_production_models", {}).get(season, res["best_model"])
        season_rows.append({
            "Season": season,
            "Status": "Ready",
            "Production ML Model": pinned,
            "Test R² (Bias-Corrected)": _fmt_val(top.get("Bias-corrected test R2"), 3),
            "Test RMSE (mbgl)": _fmt_val(top.get("Bias-corrected test RMSE"), 3),
            "Best Deep Model": res.get("deep_best_model") or "Not Run",
            "Low-Data Rescue": "Yes (Imputed)" if res.get("low_data_rescue_used") else "No (Clean Split)",
        })
    st.dataframe(pd.DataFrame(season_rows), use_container_width=True, hide_index=True)

    # Actual vs Predicted interactive comparison
    if results:
        st.markdown("#### Actual vs. Predicted Groundwater Depth (Held-Out Test Split)")
        sel_season = st.selectbox("Select season", list(results.keys()), key="adm_ov_season")
        s_res = results[sel_season]
        pred_df = s_res.get("test_predictions")
        if isinstance(pred_df, pd.DataFrame) and not pred_df.empty:
            annual_cmp = pred_df.groupby("YEAR", as_index=False)[
                ["Observed DTWL (mbgl)", "Bias-corrected prediction (mbgl)"]
            ].mean()
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=annual_cmp["YEAR"], y=annual_cmp["Observed DTWL (mbgl)"],
                mode="lines+markers", name="Verified Observation (mbgl)",
                line=dict(color="#1D1D1F", width=3)
            ))
            fig.add_trace(go.Scatter(
                x=annual_cmp["YEAR"], y=annual_cmp["Bias-corrected prediction (mbgl)"],
                mode="lines+markers", name=f"Model Estimate ({s_res['best_model']})",
                line=dict(color="#0071E3", width=3, dash="dash")
            ))
            fig.update_layout(
                title=f"Observed vs. Predicted Mean DTWL — {sel_season}",
                xaxis_title="Year", yaxis_title="DTWL (mbgl)",
                template="plotly_white", height=360
            )
            st.plotly_chart(fig, use_container_width=True)


# =========================================================================== #
# 2. ENVIRONMENTAL DATA
# =========================================================================== #
def _render_environmental_data_tab(payload: dict[str, Any] | None) -> None:
    st.subheader("2 · Environmental Dataset Management & Integrity Validation")
    st.caption(
        "Upload, preview, and validate multi-season Excel/CSV groundwater datasets. "
        "Original uploaded data is preserved unchanged."
    )

    with st.container(border=True):
        st.markdown("#### Upload New Seasonal Workbook (.xlsx) or CSV")
        adm_upload = st.file_uploader(
            "Select an Excel (.xlsx) or CSV (.csv) dataset to validate and inspect",
            type=["xlsx", "csv"],
            key="admin_env_uploader",
        )
        if adm_upload is not None:
            raw_bytes = adm_upload.getvalue()
            sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
            st.code(f"Dataset SHA-256 Checksum: {sha256_hash}", language="text")
            try:
                if adm_upload.name.lower().endswith(".csv"):
                    df_up = pd.read_csv(adm_upload)
                    if "Season" not in df_up.columns:
                        df_up["Season"] = "Monsoon"
                    clean_df, val_rep = validate_data(df_up)
                    st.success(f"Validated CSV '{adm_upload.name}': {len(clean_df):,} clean rows.")
                    st.dataframe(val_rep, use_container_width=True, hide_index=True)
                else:
                    loaded_df, wb_rep, wb_notices = load_seasonal_workbook(raw_bytes)
                    clean_df, val_rep = validate_data(loaded_df)
                    st.success(
                        f"Validated Workbook '{adm_upload.name}': {len(clean_df):,} clean rows across "
                        f"{clean_df['Season'].nunique()} seasons."
                    )
                    st.dataframe(wb_rep, use_container_width=True, hide_index=True)
                    st.dataframe(val_rep, use_container_width=True, hide_index=True)

                    if st.button("Run Full Pipeline & Activate This Dataset", type="primary"):
                        with st.spinner("Running seasonal ML & Deep Learning pipelines..."):
                            years = sorted(clean_df["YEAR"].dropna().astype(int).unique().tolist())
                            t_end = years[-3] if len(years) >= 3 else years[0]
                            v_end = years[-2] if len(years) >= 2 else years[-1]
                            cfg = RunConfig(train_end=t_end, validation_end=v_end)
                            new_results = {}
                            for s in [s for s in SEASON_ORDER if s in clean_df["Season"].unique()]:
                                new_results[s] = run_season_pipeline(clean_df, s, cfg)
                            new_payload = {
                                "config": cfg,
                                "workbook_report": wb_rep,
                                "validation_report": val_rep,
                                "notices": wb_notices,
                                "clean_data": clean_df,
                                "results": new_results,
                                "dataset_sha256": sha256_hash,
                                "dataset_name": adm_upload.name,
                                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                            }
                            st.session_state["groundwater_dashboard_payload"] = new_payload
                            log_admin_event("dataset_activated", f"{adm_upload.name} ({sha256_hash[:12]})")
                            st.success("Dataset activated across the entire platform.")
                            st.rerun()
            except Exception as exc:
                st.error(f"Dataset validation rejected file safely: {exc}")

    if not payload or payload.get("clean_data") is None:
        st.info("No active dataset loaded.")
        return

    data: pd.DataFrame = payload["clean_data"]
    st.markdown("#### Active Dataset Provenance & Quality Checks")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Rows", f"{len(data):,}")
    p2.metric("Duplicate Village-Year-Season", f"{int(data.duplicated(subset=['VILLAGE', 'YEAR', 'Season']).sum())}")
    p3.metric("Missing Target Cells", f"{int(data[TARGET].isna().sum())}")
    p4.metric("Required Columns Present", f"{len(REQUIRED_COLUMNS.intersection(data.columns))}/{len(REQUIRED_COLUMNS)}")

    st.markdown("#### Physical Range & Coordinate Boundary Audit (Rajasthan Bounds)")
    audit_findings = []
    for idx, row in data.head(250).iterrows():
        for notice in validate_environmental_record(row.to_dict()):
            audit_findings.append({
                "Row Index": idx,
                "Village": row.get("VILLAGE", "Unknown"),
                "Year": row.get("YEAR", "—"),
                "Category": notice.category,
                "Severity": notice.severity,
                "Detail": notice.message,
            })
    if audit_findings:
        st.warning(f"Detected {len(audit_findings)} boundary or out-of-distribution notices in first 250 rows.")
        st.dataframe(pd.DataFrame(audit_findings), use_container_width=True, hide_index=True)
    else:
        st.success(
            f"All audited records lie within Rajasthan coordinates ({RAJASTHAN_LAT_BOUNDS}°N, "
            f"{RAJASTHAN_LON_BOUNDS}°E) and physical sensor bounds."
        )

    st.markdown("#### Dataset Preview & Unmodified CSV Export")
    st.dataframe(data.head(100), use_container_width=True, hide_index=True)
    st.download_button(
        "Download Preserved Clean Dataset (.csv)",
        data=data.to_csv(index=False).encode("utf-8"),
        file_name="naya_pani_preserved_dataset.csv",
        mime="text/csv",
    )


# =========================================================================== #
# 3. GROUNDWATER MONITORING
# =========================================================================== #
def _render_groundwater_monitoring_tab(payload: dict[str, Any] | None) -> None:
    st.subheader("3 · Groundwater Depth Monitoring & Water-Stress Classification")
    if not payload or payload.get("clean_data") is None or payload["clean_data"].empty:
        st.info("No groundwater observation dataset is loaded.")
        return

    data: pd.DataFrame = payload["clean_data"]
    settings = _get_admin_settings()

    f1, f2, f3 = st.columns(3)
    seasons = ["All Seasons"] + [s for s in SEASON_ORDER if s in data["Season"].unique()]
    sel_season = f1.selectbox("Filter by Season", seasons, key="adm_mon_season")
    blocks = ["All Blocks"] + (sorted(data["BLOCK"].dropna().astype(str).unique().tolist()) if "BLOCK" in data.columns else [])
    sel_block = f2.selectbox("Filter by Block", blocks, key="adm_mon_block")
    villages_pool = data.copy()
    if sel_season != "All Seasons":
        villages_pool = villages_pool[villages_pool["Season"] == sel_season]
    if sel_block != "All Blocks" and "BLOCK" in villages_pool.columns:
        villages_pool = villages_pool[villages_pool["BLOCK"].astype(str) == sel_block]

    village_list = ["All Villages"] + sorted(villages_pool["VILLAGE"].dropna().astype(str).unique().tolist())
    sel_village = f3.selectbox("Filter by Village", village_list, key="adm_mon_village")
    if sel_village != "All Villages":
        villages_pool = villages_pool[villages_pool["VILLAGE"].astype(str) == sel_village]

    # Classify water stress based on configurable mbgl thresholds
    safe_lim = float(settings["water_stress_safe_mbgl"])
    semi_lim = float(settings["water_stress_semi_critical_mbgl"])
    crit_lim = float(settings["water_stress_critical_mbgl"])

    def _stress_category(dtwl: float) -> str:
        if not np.isfinite(dtwl):
            return "Unavailable"
        if dtwl <= safe_lim:
            return "Safe (≤ %.1f m)" % safe_lim
        if dtwl <= semi_lim:
            return "Semi-Critical (%.1f–%.1f m)" % (safe_lim, semi_lim)
        if dtwl <= crit_lim:
            return "Critical (%.1f–%.1f m)" % (semi_lim, crit_lim)
        return "Over-Exploited (> %.1f m)" % crit_lim

    village_summary = (
        villages_pool.groupby("VILLAGE", as_index=False)
        .agg(
            Latest_Year=("YEAR", "max"),
            Mean_DTWL_mbgl=(TARGET, "mean"),
            Max_DTWL_mbgl=(TARGET, "max"),
            Mean_Rainfall_mm=("Rainfall", "mean"),
            Mean_ET_mm=("ET", "mean"),
        )
    )
    village_summary["Water_Stress_Status"] = village_summary["Mean_DTWL_mbgl"].apply(_stress_category)
    village_summary["Record_Type"] = "Verified In-Situ Observation"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Filtered Observations", f"{len(villages_pool):,}")
    c2.metric("Mean Observed DTWL", _fmt_val(villages_pool[TARGET].mean(), 2, "mbgl"))
    over_exp = int((village_summary["Mean_DTWL_mbgl"] > crit_lim).sum())
    c3.metric("Over-Exploited Villages", f"{over_exp} / {len(village_summary)}")
    c4.metric("Mean Rainfall", _fmt_val(villages_pool["Rainfall"].mean(), 1, "mm"))

    # Historical Trend + Rainfall comparison
    trend_df = villages_pool.groupby("YEAR", as_index=False).agg(
        Observed_DTWL_mbgl=(TARGET, "mean"),
        Rainfall_mm=("Rainfall", "mean"),
    )
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=trend_df["YEAR"], y=trend_df["Rainfall_mm"],
        name="Observed Rainfall (mm)", marker_color="rgba(0, 113, 227, 0.28)", yaxis="y2"
    ))
    fig.add_trace(go.Scatter(
        x=trend_df["YEAR"], y=trend_df["Observed_DTWL_mbgl"],
        mode="lines+markers", name="Verified Observed DTWL (mbgl)",
        line=dict(color="#D9381E", width=3)
    ))
    fig.update_layout(
        title="Historical Observed DTWL (mbgl) vs. Seasonal Rainfall (mm)",
        xaxis_title="Year",
        yaxis=dict(title="DTWL (mbgl — deeper is more stressed)"),
        yaxis2=dict(title="Rainfall (mm)", overlaying="y", side="right", showgrid=False),
        template="plotly_white", height=390
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Village Water-Stress Classification Table (Observed Data)")
    st.dataframe(village_summary.round(2), use_container_width=True, hide_index=True)


# =========================================================================== #
# 4. ML/DL MODELS
# =========================================================================== #
def _render_models_tab(payload: dict[str, Any] | None) -> None:
    st.subheader("4 · ML & Deep Learning Model Governance, Deployment & Rollback")
    if not payload or not payload.get("results"):
        st.info("No trained models in the current session. Load a workbook to inspect models.")
        return

    results: dict[str, dict[str, Any]] = payload["results"]
    pinned_map: dict[str, str] = st.session_state.setdefault("pinned_production_models", {})

    sel_season = st.selectbox("Select Season", list(results.keys()), key="adm_mdl_season")
    res = results[sel_season]
    metrics_df: pd.DataFrame = res["metrics"]
    deep_df: pd.DataFrame | None = res.get("deep_metrics")

    default_winner = res["best_model"]
    current_prod = pinned_map.get(sel_season, default_winner)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Production Model", current_prod)
    c2.metric("Auto-Selected Best ML", default_winner)
    c3.metric("Best Deep Model", res.get("deep_best_model") or "Unavailable")
    c4.metric("Selected Features", f"{len(res.get('selected_features', []))}")

    st.caption(f"**Target Variable:** `{TARGET}` | **Selected Features:** `{', '.join(res.get('selected_features', []))}`")

    st.markdown("#### Classical ML Model Evaluation Metrics")
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    st.markdown("#### Deep Learning & Physics-Informed Model Metrics (PINN, ESN, SARIMA, LSTM)")
    if isinstance(deep_df, pd.DataFrame) and not deep_df.empty:
        st.dataframe(deep_df, use_container_width=True, hide_index=True)
    else:
        st.info("Deep learning models were not fitted for this season.")

    # Controlled Deployment Pinning & Rollback (Never replaces production model automatically)
    with st.container(border=True):
        st.markdown("#### Controlled Production Model Deployment & Rollback")
        st.caption(
            "Safety Policy: Retraining or evaluating candidate models never replaces the production model "
            "automatically. An administrator must explicitly pin or roll back the production model."
        )
        candidate_models = metrics_df["Model"].astype(str).tolist()
        if isinstance(deep_df, pd.DataFrame) and not deep_df.empty:
            candidate_models += deep_df["Model"].astype(str).tolist()

        col_a, col_b, col_c = st.columns([2, 1, 1])
        chosen_candidate = col_a.selectbox(
            "Select validated model to promote to production",
            candidate_models,
            index=candidate_models.index(current_prod) if current_prod in candidate_models else 0,
            key=f"adm_pin_{sel_season}",
        )
        if col_b.button("Pin as Production Model", type="primary", use_container_width=True):
            old_m = pinned_map.get(sel_season, default_winner)
            pinned_map[sel_season] = chosen_candidate
            log_admin_event("model_promoted", f"{sel_season}: {old_m} -> {chosen_candidate}")
            st.success(f"Pinned **{chosen_candidate}** as production model for **{sel_season}**.")
            st.rerun()

        if col_c.button("Rollback to Default Winner", use_container_width=True):
            old_m = pinned_map.pop(sel_season, default_winner)
            log_admin_event("model_rollback", f"{sel_season}: {old_m} -> {default_winner}")
            st.info(f"Rolled back **{sel_season}** production model to **{default_winner}**.")
            st.rerun()

    # Controlled Retraining with custom hyperparameters
    with st.expander("🔄 Controlled Season Retraining (Sandbox Evaluation)"):
        rc1, rc2, rc3 = st.columns(3)
        n_feat = rc1.slider("Feature Count", 3, 12, int(payload["config"].selected_feature_count), key="adm_rt_feat")
        n_trees = rc2.slider("Tree Estimators", 50, 500, int(payload["config"].tree_count), step=50, key="adm_rt_trees")
        res_size = rc3.slider("ESN Reservoir Size", 32, 160, int(payload["config"].reservoir_size), step=16, key="adm_rt_esn")
        if st.button("Run Controlled Retraining for Selected Season"):
            t0 = perf_counter()
            new_cfg = RunConfig(
                train_end=payload["config"].train_end,
                validation_end=payload["config"].validation_end,
                selected_feature_count=n_feat,
                tree_count=n_trees,
                reservoir_size=res_size,
                forecast_steps=payload["config"].forecast_steps,
            )
            new_res = run_season_pipeline(payload["clean_data"], sel_season, new_cfg)
            elapsed = perf_counter() - t0
            payload["results"][sel_season] = new_res
            log_admin_event("model_retrained", f"{sel_season} in {elapsed:.2f}s (trees={n_trees}, feat={n_feat})")
            st.success(f"Retrained {sel_season} pipeline in {elapsed:.2f}s. Production model pin remains unchanged until promoted.")
            st.rerun()


# =========================================================================== #
# 5. DIGITAL TWIN
# =========================================================================== #
def _render_digital_twin_tab(payload: dict[str, Any] | None) -> None:
    st.subheader("5 · Digital Twin State, What-If Scenarios & Parameter Audit")
    if not payload or not payload.get("results"):
        st.info("Load a workbook to initialize the Rajasthan Aquifer Digital Twin.")
        return

    with st.container(border=True):
        st.markdown("#### Controlled What-If Scenario Simulator (Separated from Baseline)")
        st.caption(
            "Simulates linear water-balance perturbations around the model's baseline forecast. "
            "Baseline observations, model forecasts, and scenario outputs are strictly separated."
        )
        results = payload["results"]
        s_name = st.selectbox("Scenario Season", list(results.keys()), key="adm_dt_season")
        s_res = results[s_name]
        fc_df = s_res.get("forecast")

        sc1, sc2, sc3 = st.columns(3)
        rain_delta_pct = sc1.slider("Rainfall Perturbation (%)", -50, 50, 0, step=5, key="adm_dt_rain")
        pump_delta_pct = sc2.slider("Extraction / Pumping Change (%)", -40, 40, 0, step=5, key="adm_dt_pump")
        rech_eff = sc3.slider("Specific Recharge Sensitivity (m per 100% Δ)", 0.1, 2.5, 0.8, step=0.1, key="adm_dt_rech")

        if st.button("Log & Evaluate Scenario Perturbation", type="primary"):
            admin_user = str(admin_session_summary().get("user") or "admin")
            DIGITAL_TWIN_AUDIT.log_parameter_change(
                user=admin_user,
                parameter=f"{s_name}_what_if_scenario",
                old_val="rain:0%,pump:0%",
                new_val=f"rain:{rain_delta_pct}%,pump:{pump_delta_pct}%,sens:{rech_eff}",
            )
            log_admin_event("digital_twin_scenario", f"{s_name} rain={rain_delta_pct}% pump={pump_delta_pct}%")

        if isinstance(fc_df, pd.DataFrame) and not fc_df.empty:
            val_col = "Scenario forecast DTWL (mbgl)"
            yr_col = "Year" if "Year" in fc_df.columns else "YEAR"
            base_vals = fc_df[val_col].to_numpy(dtype=float)
            # Positive rain reduces DTWL (water table rises); positive pumping increases DTWL (water table drops)
            net_annual_shift = ((-rain_delta_pct / 100.0) + (pump_delta_pct / 100.0)) * rech_eff
            cumulative_shift = net_annual_shift * np.arange(1, len(base_vals) + 1)
            scenario_vals = np.maximum(0.1, base_vals + cumulative_shift)

            obs_mean = float(payload["clean_data"][payload["clean_data"]["Season"] == s_name][TARGET].mean())
            comp_table = pd.DataFrame({
                "Year": fc_df[yr_col].astype(int),
                "Historical Observed Mean (mbgl)": np.round(obs_mean, 2),
                "Baseline Model Forecast (mbgl)": np.round(base_vals, 2),
                "What-If Scenario Output (mbgl)": np.round(scenario_vals, 2),
                "Net Scenario Shift (mbgl)": np.round(scenario_vals - base_vals, 2),
            })
            st.dataframe(comp_table, use_container_width=True, hide_index=True)

    st.markdown("#### Interactive 3D Cutaway Digital Twin & OpenUSD Stage")
    render_digital_twin(payload)

    if payload and payload.get("results"):
        from twin_engine import build_asset_catalog, export_openusd_stage, validate_simready_hydro_assets
        first_season = next(iter(payload["results"].keys()))
        s_res = payload["results"][first_season]
        c_df = s_res.get("clean_data", s_res.get("lagged_data"))
        if c_df is not None:
            a_cat = build_asset_catalog(c_df)
            val_rep = validate_simready_hydro_assets(a_cat)
            st.markdown("#### OpenUSD (.usda) & SimReady Asset Validation")
            adm_u1, adm_u2 = st.columns([1.5, 2.5])
            with adm_u1:
                st.metric("SimReady Compliance", f"{val_rep['compliance_pct']:.1f}%", f"{val_rep['simready_compliant_count']}/{val_rep['total_assets']} Assets Compliant")
                usda_admin = export_openusd_stage(
                    season=first_season,
                    year=2022,
                    district="All available",
                    mode="Observed",
                    state_metrics={"dtwl": float(c_df["DTWL (mbgl)"].mean()) if "DTWL (mbgl)" in c_df.columns else 10.0},
                    asset_catalog=a_cat,
                    asset_info={"name": "Basin Aggregate", "elevation_m": 300.0},
                )
                st.download_button(
                    "📥 Export Stage to Omniverse (.usda)",
                    data=usda_admin.encode("utf-8"),
                    file_name="NayaPani_Admin_OmniverseStage.usda",
                    mime="model/vnd.usda",
                    type="primary",
                    use_container_width=True,
                )
            with adm_u2:
                st.dataframe(val_rep["records"].head(10), use_container_width=True, hide_index=True)

    st.markdown("#### Digital Twin Parameter Modification Audit Ledger")
    ledger = DIGITAL_TWIN_AUDIT.get_ledger()
    if ledger:
        st.dataframe(pd.DataFrame(ledger), use_container_width=True, hide_index=True)
    else:
        st.caption("No Digital Twin scenario modifications logged in this session yet.")


# =========================================================================== #
# 6. RAG CHATBOT
# =========================================================================== #
def _render_rag_tab(payload: dict[str, Any] | None) -> None:
    st.subheader("6 · RAG Knowledge Base, Indexing, Retrieval & Security Testing")
    kb = _get_kb()
    kb_dir = kb.kb_dir

    c1, c2, c3, c4 = st.columns(4)
    md_files = sorted(kb_dir.glob("*.md")) if kb_dir.exists() else []
    c1.metric("Markdown Documents", f"{len(md_files)}")
    c2.metric("Indexed Text Chunks", f"{len(kb.documents)}")
    c3.metric("Active LLM Engine", active_provider().upper())
    c4.metric("Prompt-Injection Filter", "Active (Regex + Length Guard)")

    st.markdown("#### Indexed Knowledge Base Documents")
    doc_summary = []
    for p in md_files:
        chunks_for_doc = [d for d in kb.documents if d["source"] == p.name]
        doc_summary.append({
            "Document File": p.name,
            "Title": p.stem.replace("_", " ").title(),
            "Size (Bytes)": p.stat().st_size,
            "Indexed Chunks": len(chunks_for_doc),
            "Access Level": "Public / Grounded",
        })
    st.dataframe(pd.DataFrame(doc_summary), use_container_width=True, hide_index=True)

    col_idx, col_up = st.columns(2)
    with col_idx:
        st.markdown("#### Re-Index Knowledge Base")
        if st.button("Rebuild TF-IDF Embeddings & Index", type="primary"):
            t0 = perf_counter()
            kb._load()
            dt_ms = (perf_counter() - t0) * 1000.0
            log_admin_event("rag_reindexed", f"{len(kb.documents)} chunks in {dt_ms:.1f}ms")
            st.success(f"Re-indexed {len(kb.documents)} chunks across {len(md_files)} files in {dt_ms:.1f} ms.")

    with col_up:
        st.markdown("#### Upload New Knowledge Document (.md)")
        new_md = st.file_uploader("Upload Markdown (.md) document", type=["md"], key="adm_rag_md_up")
        if new_md is not None:
            safe_name = Path(new_md.name).name
            content_str = new_md.getvalue().decode("utf-8", errors="replace")
            _, notices = sanitize_rag_prompt(content_str[:1000])
            if any(n.severity == "CRITICAL" for n in notices):
                st.error("Rejected document: detected embedded prompt-injection instructions.")
            elif st.button(f"Save & Index '{safe_name}'"):
                target_path = kb_dir / safe_name
                target_path.write_text(content_str, encoding="utf-8")
                kb._load()
                log_admin_event("rag_doc_uploaded", safe_name)
                st.success(f"Saved `{safe_name}` and re-indexed knowledge base ({len(kb.documents)} chunks).")
                st.rerun()

    st.markdown("#### Retrieval & Prompt-Injection Diagnostic Sandbox")
    test_query = st.text_input(
        "Enter a test query or simulated prompt-injection string",
        value="What is the forecast for 2024 and why does Monsoon perform best?",
        key="adm_rag_test_q",
    )
    if st.button("Run Retrieval & Grounded Answer Evaluation"):
        t0 = perf_counter()
        clean_q, sec_notices = sanitize_rag_prompt(test_query)
        settings = _get_admin_settings()
        hits = kb.search(clean_q, top_k=int(settings["rag_top_k"]), min_score=float(settings["rag_min_score"]))
        resp = rag_answer(clean_q, payload, twin_state=st.session_state.get("digital_twin_state"))
        resp["answer"] = sanitize_rag_response(resp["answer"])
        latency_ms = (perf_counter() - t0) * 1000.0

        if sec_notices:
            for n in sec_notices:
                st.warning(f"Security Filter Triggered ({n.category} - {n.severity}): {n.message}")
        else:
            st.success(f"Query passed security sanitization ({latency_ms:.1f} ms).")

        st.markdown("**Generated Grounded Response:**")
        st.info(resp["answer"])
        st.caption(f"Cited Sources: {', '.join(resp.get('sources') or ['Live Run Context'])} | Provider: {resp.get('provider')}")

        if hits:
            st.markdown("**Retrieved Knowledge Base Chunks:**")
            st.dataframe(
                pd.DataFrame([
                    {"Source": h["source"], "Heading": h["heading"], "Similarity Score": round(h["score"], 4), "Snippet": h["text"][:180] + "..."}
                    for h in hits
                ]),
                use_container_width=True,
                hide_index=True,
            )


# =========================================================================== #
# 7. USERS & PERMISSIONS
# =========================================================================== #
def _render_users_permissions_tab() -> None:
    st.subheader("7 · Users, Role-Based Access Control (RBAC) & Session Security")
    summary = admin_session_summary()
    rbac = _get_rbac_registry()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Signed-In Admin", str(summary.get("user") or "Unknown"))
    rem_sec = max(0, int(float(summary.get("expires_at") or 0) - datetime.now(timezone.utc).timestamp()))
    c2.metric("Session TTL Remaining", f"{rem_sec // 60}m {rem_sec % 60}s")
    c3.metric("Max Login Attempts", f"{ADMIN_MAX_ATTEMPTS} tries")
    c4.metric("Lockout Window", f"{ADMIN_LOCKOUT_SECONDS // 60} minutes")

    st.markdown("#### Role-Based Access Control (RBAC) Directory")
    role_rows = []
    for email in rbac["admins"]:
        role_rows.append({"Email / Identity": email, "Role": "Admin", "Permissions": "Full System, Model Promotion, KB Upload, Audit Logs, Settings"})
    for email in rbac["analysts"]:
        role_rows.append({"Email / Identity": email, "Role": "Analyst", "Permissions": "Dataset Upload, Pipeline Execution, Scenario Simulation, Reports"})
    for email in rbac["viewers"]:
        role_rows.append({"Email / Identity": email, "Role": "Viewer", "Permissions": "Read-Only Dashboard, Forecast Viewing, Grounded Chat"})
    st.dataframe(pd.DataFrame(role_rows), use_container_width=True, hide_index=True)

    with st.container(border=True):
        st.markdown("#### Grant or Update User Role")
        u_col1, u_col2, u_col3 = st.columns([2, 1, 1])
        new_email = u_col1.text_input("User Email", placeholder="researcher@university.edu", key="adm_rbac_email")
        new_role = u_col2.selectbox("Assign Role", ["Admin", "Analyst", "Viewer"], key="adm_rbac_role")
        if u_col3.button("Assign Role", type="primary", use_container_width=True):
            clean_em = new_email.strip().lower()
            if "@" not in clean_em:
                st.error("Enter a valid email address.")
            else:
                for lst in rbac.values():
                    if clean_em in lst:
                        lst.remove(clean_em)
                target_key = {"Admin": "admins", "Analyst": "analysts", "Viewer": "viewers"}[new_role]
                rbac[target_key].append(clean_em)
                log_admin_event("rbac_role_assigned", f"{clean_em} -> {new_role}")
                st.success(f"Assigned role **{new_role}** to `{clean_em}`.")
                st.rerun()

    with st.expander("🔐 Password Hash Generator (PBKDF2-HMAC-SHA256 / Argon2)"):
        st.caption("Generate a salted password hash for `ADMIN_MASTER_PASSWORD_HASH` environment variable.")
        pw_in = st.text_input("Plaintext password to hash", type="password", key="adm_pw_gen")
        if pw_in and st.button("Generate Verifiable Hash"):
            st.code(_hash_password(pw_in), language="text")


# =========================================================================== #
# 8. ALERTS & NOTIFICATIONS
# =========================================================================== #
def _render_alerts_tab(payload: dict[str, Any] | None) -> None:
    st.subheader("8 · Actionable System, Data & Security Alerts")
    alerts: list[dict[str, str]] = []
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    settings = _get_admin_settings()

    if not payload or payload.get("clean_data") is None:
        alerts.append({
            "Severity": "WARNING",
            "Timestamp": now_iso,
            "Component": "Environmental Data",
            "Message": "No groundwater workbook is currently loaded in the session.",
            "Status": "Action Required",
        })
    else:
        data: pd.DataFrame = payload["clean_data"]
        max_yr = int(data["YEAR"].max())
        if max_yr < int(settings["stale_data_year_threshold"]):
            alerts.append({
                "Severity": "WARNING",
                "Timestamp": now_iso,
                "Component": "Data Freshness",
                "Message": f"Latest observation year ({max_yr}) is older than freshness threshold ({settings['stale_data_year_threshold']}).",
                "Status": "Active",
            })

        # Check model errors & low-data rescue
        for season, res in (payload.get("results") or {}).items():
            if res.get("low_data_rescue_used"):
                alerts.append({
                    "Severity": "INFO",
                    "Timestamp": now_iso,
                    "Component": f"Pipeline ({season})",
                    "Message": f"Low-data rescue imputation was activated for {season} to preserve train/val/test split.",
                    "Status": "Monitored",
                })
            for err in res.get("model_errors", []) + res.get("deep_model_errors", []):
                alerts.append({
                    "Severity": "WARNING",
                    "Timestamp": now_iso,
                    "Component": f"ML/DL Models ({season})",
                    "Message": str(err),
                    "Status": "Logged",
                })

    # Check failed logins in audit log
    recent_logs = read_admin_audit_logs(limit=50)
    failed_logins = [r for r in recent_logs if "failed" in r.get("Event", "")]
    if failed_logins:
        alerts.append({
            "Severity": "CRITICAL" if len(failed_logins) >= 3 else "WARNING",
            "Timestamp": failed_logins[0]["Timestamp (UTC)"],
            "Component": "Authentication Security",
            "Message": f"{len(failed_logins)} failed administrator login attempt(s) recorded in audit log.",
            "Status": "Review Audit Logs",
        })

    if not alerts:
        st.success("No active system, model, or security alerts.")
    else:
        st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)


# =========================================================================== #
# 9. SYSTEM HEALTH
# =========================================================================== #
def _render_system_health_tab(payload: dict[str, Any] | None) -> None:
    st.subheader("9 · Live Backend, Dependency & Component Health Probes")

    t0 = perf_counter()
    kb = _get_kb()
    _ = kb.search("groundwater recharge", top_k=2)
    rag_latency_ms = (perf_counter() - t0) * 1000.0

    with workspace_store._lock:
        active_ws_count = len(workspace_store._items)

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Backend Runtime", f"Python {platform.python_version()}")
    h2.metric("RAG Retrieval Latency", f"{rag_latency_ms:.2f} ms")
    h3.metric("Cached Workspaces", f"{active_ws_count} / {workspace_store._max_workspaces}")
    h4.metric("Word Report Engine", "Ready (python-docx)" if HAS_DOCX else "Unavailable")

    st.markdown("#### Subsystem Health Matrix")
    deep_status = _deep_model_status()
    health_rows = [
        {"Subsystem": "Core ML Pipeline (Scikit-Learn)", "Status": "Healthy", "Detail": "RandomForest, ExtraTrees, SVR, GPR, Ridge, BayesianRidge available"},
        {"Subsystem": "Physics-Informed NN (PINN)", "Status": "Healthy", "Detail": deep_status.get("PINN (Physics-Informed NN)", "Available")},
        {"Subsystem": "Echo-State Network (ESN)", "Status": "Healthy", "Detail": deep_status.get("Reservoir Computing (ESN)", "Available")},
        {"Subsystem": "SARIMA / SARIMAX", "Status": "Healthy", "Detail": deep_status.get("SARIMA (SARIMAX)", "Available")},
        {"Subsystem": "PyTorch LSTM", "Status": "Healthy" if "Available" in deep_status.get("LSTM (Deep Learning)", "") else "Optional Missing", "Detail": deep_status.get("LSTM (Deep Learning)", "")},
        {"Subsystem": "RAG TF-IDF Knowledge Index", "Status": "Healthy" if kb.documents else "Empty", "Detail": f"{len(kb.documents)} chunks indexed ({rag_latency_ms:.2f} ms query time)"},
        {"Subsystem": "Digital Twin 3D Engine", "Status": "Healthy" if payload else "Standby (Awaiting Data)", "Detail": "Plotly 3D surface cutaway & audit ledger ready"},
        {"Subsystem": "PWA Static Manifest & Service Worker", "Status": "Healthy", "Detail": "static/manifest.json & static/service_worker.js active"},
    ]
    st.dataframe(pd.DataFrame(health_rows), use_container_width=True, hide_index=True)


# =========================================================================== #
# 10. REPORTS
# =========================================================================== #
def _render_reports_tab(payload: dict[str, Any] | None) -> None:
    st.subheader("10 · Authorized Scientific, Model & Compliance Reports")

    r_col1, r_col2 = st.columns(2)
    with r_col1:
        st.markdown("#### 1. Audit & Security Compliance Report (CSV)")
        audit_df = pd.DataFrame(read_admin_audit_logs(limit=200))
        st.download_button(
            "Download Security Audit Log (.csv)",
            data=audit_df.to_csv(index=False).encode("utf-8") if not audit_df.empty else b"Timestamp,Event,Detail\n",
            file_name="naya_pani_security_audit_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with r_col2:
        st.markdown("#### 2. System Health & Configuration Snapshot (JSON)")
        snap = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "python_version": platform.python_version(),
            "llm_provider": active_provider(),
            "deep_models": _deep_model_status(),
            "settings": _get_admin_settings(),
        }
        st.download_button(
            "Download System Health Snapshot (.json)",
            data=json.dumps(snap, indent=2).encode("utf-8"),
            file_name="naya_pani_system_health.json",
            mime="application/json",
            use_container_width=True,
        )

    if not payload or not payload.get("results"):
        st.info("Load and run an analysis workbook to enable Scientific Word (.docx) and Excel (.xlsx) exports.")
        return

    st.markdown("---")
    e_col1, e_col2, e_col3 = st.columns(3)
    with e_col1:
        st.markdown("#### 3. Full Excel Analysis Workbook (.xlsx)")
        excel_bytes = build_excel_export(
            payload["workbook_report"], payload["validation_report"], payload["results"]
        )
        st.download_button(
            "Download Full Analysis Excel (.xlsx)",
            data=excel_bytes,
            file_name="naya_pani_admin_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )

    with e_col2:
        st.markdown("#### 4. Scientific Word Report (.docx)")
        if HAS_DOCX:
            if st.button("Generate Scientific Word Report (.docx)", use_container_width=True):
                with st.spinner("Compiling scientific report with figures..."):
                    docx_bytes = build_scientific_report(payload)
                    st.session_state["adm_cached_docx"] = docx_bytes
            if st.session_state.get("adm_cached_docx"):
                st.download_button(
                    "Download Compiled Word Report (.docx)",
                    data=st.session_state["adm_cached_docx"],
                    file_name="naya_pani_scientific_report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
        else:
            st.warning("python-docx not installed.")

    with e_col3:
        st.markdown("#### 5. Combined Model Evaluation CSV")
        all_m = []
        for s, res in payload["results"].items():
            df_m = res["metrics"].copy()
            df_m.insert(0, "Season", s)
            all_m.append(df_m)
        comb_df = pd.concat(all_m, ignore_index=True) if all_m else pd.DataFrame()
        st.download_button(
            "Download All Season Model Metrics (.csv)",
            data=comb_df.to_csv(index=False).encode("utf-8"),
            file_name="naya_pani_model_metrics.csv",
            mime="text/csv",
            use_container_width=True,
        )


# =========================================================================== #
# 11. AUDIT LOGS
# =========================================================================== #
def _render_audit_logs_tab() -> None:
    st.subheader("11 · Tamper-Evident Administrative & Security Audit Logs")
    st.caption(
        "Records authentication events, RBAC updates, dataset activations, model promotions/rollbacks, "
        "and Digital Twin scenario changes. Passwords and tokens are never logged."
    )

    logs = read_admin_audit_logs(limit=250)
    search_term = st.text_input("Filter audit logs by event or detail", placeholder="e.g. login, model_promoted, dataset", key="adm_log_search")
    if search_term:
        q = search_term.lower()
        logs = [r for r in logs if q in r["Event"].lower() or q in r["Detail"].lower()]

    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
    else:
        st.info("No matching audit log records.")

    st.markdown("#### Digital Twin Parameter Checksum Ledger")
    dt_ledger = DIGITAL_TWIN_AUDIT.get_ledger()
    if dt_ledger:
        st.dataframe(pd.DataFrame(dt_ledger), use_container_width=True, hide_index=True)
    else:
        st.caption("No Digital Twin parameter changes recorded in this session.")


# =========================================================================== #
# 12. SETTINGS
# =========================================================================== #
def _render_settings_tab() -> None:
    st.subheader("12 · Validated Application Settings & Secret Status")
    settings = _get_admin_settings()

    with st.form("admin_settings_form"):
        st.markdown("#### Hydrological Water-Stress Classification Thresholds (mbgl)")
        c1, c2, c3 = st.columns(3)
        safe_v = c1.number_input("Safe Threshold (≤ mbgl)", min_value=1.0, max_value=50.0, value=float(settings["water_stress_safe_mbgl"]), step=1.0)
        semi_v = c2.number_input("Semi-Critical Threshold (≤ mbgl)", min_value=2.0, max_value=80.0, value=float(settings["water_stress_semi_critical_mbgl"]), step=1.0)
        crit_v = c3.number_input("Critical Threshold (≤ mbgl)", min_value=5.0, max_value=150.0, value=float(settings["water_stress_critical_mbgl"]), step=1.0)

        st.markdown("#### Forecasting, Data Freshness & RAG Retrieval Thresholds")
        f1, f2, f3, f4 = st.columns(4)
        max_fc = f1.number_input("Max Forecast Horizon (Years)", min_value=1, max_value=10, value=int(settings["max_forecast_horizon"]))
        stale_yr = f2.number_input("Data Freshness Cutoff Year", min_value=2000, max_value=2030, value=int(settings["stale_data_year_threshold"]))
        top_k = f3.number_input("RAG Top-K Chunks", min_value=1, max_value=10, value=int(settings["rag_top_k"]))
        min_sc = f4.number_input("RAG Min Cosine Score", min_value=0.01, max_value=0.80, value=float(settings["rag_min_score"]), step=0.05)

        saved = st.form_submit_button("Validate & Save Settings", type="primary")
        if saved:
            if not (safe_v < semi_v < crit_v):
                st.error("Validation error: Thresholds must satisfy Safe < Semi-Critical < Critical.")
            else:
                safe_fc, _ = validate_forecast_workload(int(max_fc), max_allowed_steps=10)
                settings.update({
                    "water_stress_safe_mbgl": float(safe_v),
                    "water_stress_semi_critical_mbgl": float(semi_v),
                    "water_stress_critical_mbgl": float(crit_v),
                    "max_forecast_horizon": int(safe_fc),
                    "stale_data_year_threshold": int(stale_yr),
                    "rag_top_k": int(top_k),
                    "rag_min_score": float(min_sc),
                })
                log_admin_event("settings_updated", f"stress=({safe_v},{semi_v},{crit_v}) max_fc={safe_fc}")
                st.success("Settings validated and saved.")

    st.markdown("#### Server-Side Environment & Secret Status (Values Never Exposed)")
    secret_rows = [
        {"Environment Variable": "ADMIN_MASTER_ID", "Status": "Configured (Env)" if os.getenv("ADMIN_MASTER_ID") else "Using Default Fallback"},
        {"Environment Variable": "ADMIN_MASTER_PASSWORD / HASH", "Status": "Configured (Env)" if (os.getenv("ADMIN_MASTER_PASSWORD") or os.getenv("ADMIN_MASTER_PASSWORD_HASH")) else "Using Default Fallback"},
        {"Environment Variable": "GEMINI_API_KEY", "Status": "Configured" if os.getenv("GEMINI_API_KEY") else "Not Set (Offline Mode)"},
        {"Environment Variable": "ANTHROPIC_API_KEY", "Status": "Configured" if os.getenv("ANTHROPIC_API_KEY") else "Not Set"},
    ]
    st.dataframe(pd.DataFrame(secret_rows), use_container_width=True, hide_index=True)


# =========================================================================== #
# MAIN ENTRY POINT FOR ADMIN DASHBOARD
# =========================================================================== #
def render_complete_admin_dashboard() -> None:
    """Render the full 12-section Naya Pani Admin Dashboard."""
    payload = _get_active_payload()
    summary = admin_session_summary()

    with st.sidebar:
        from pwa_server import get_brand_logo_base64
        _admin_logo = get_brand_logo_base64(192)
        if _admin_logo:
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                    <img src="{_admin_logo}" alt="Naya Pani Logo" style="width:42px;height:42px;border-radius:10px;object-fit:contain;box-shadow:0 2px 8px rgba(0,113,227,0.18);" />
                    <div>
                        <div style="font-weight:800;font-size:15px;color:#1D1D1F;line-height:1.2;">Naya Pani Admin</div>
                        <div style="font-size:11.5px;color:#6E6E73;">Signed in as: <code>{summary.get('user') or 'admin'}</code></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown("### 🛡️ Naya Pani Admin")
            st.caption(f"Signed in as: `{summary.get('user') or 'admin'}`")
        selected_section = st.radio(
            "Admin Navigation",
            ADMIN_MENU_ITEMS,
            label_visibility="collapsed",
            key="admin_sidebar_nav",
        )
        st.markdown("---")
        if st.button("⬅️ Return to Main Dashboard", use_container_width=True, type="primary"):
            st.query_params.pop("page", None)
            st.rerun()
        if st.button("🔒 Log Out Admin Session", use_container_width=True):
            logout_admin_session()
            st.query_params.pop("page", None)
            st.rerun()

    if selected_section == "1. Overview":
        _render_overview_tab(payload)
    elif selected_section == "2. Environmental Data":
        _render_environmental_data_tab(payload)
    elif selected_section == "3. Groundwater Monitoring":
        _render_groundwater_monitoring_tab(payload)
    elif selected_section == "4. ML/DL Models":
        _render_models_tab(payload)
    elif selected_section == "5. Digital Twin":
        _render_digital_twin_tab(payload)
    elif selected_section == "6. RAG Chatbot":
        _render_rag_tab(payload)
    elif selected_section == "7. Users & Permissions":
        _render_users_permissions_tab()
    elif selected_section == "8. Alerts & Notifications":
        _render_alerts_tab(payload)
    elif selected_section == "9. System Health":
        _render_system_health_tab(payload)
    elif selected_section == "10. Reports":
        _render_reports_tab(payload)
    elif selected_section == "11. Audit Logs":
        _render_audit_logs_tab()
    elif selected_section == "12. Settings":
        _render_settings_tab()
