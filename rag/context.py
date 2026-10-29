"""rag/context.py — summarise a dashboard run and Digital Twin state for grounding the assistant."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _fmt(value: Any, digits: int = 3) -> str:
    try:
        numeric = float(value)
        return "—" if not np.isfinite(numeric) else f"{numeric:.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def summarize_results(results: dict[str, dict[str, Any]]) -> str:
    """A detailed text summary of every season's headline results, model rankings, and LOFO drivers."""
    if not results:
        return "No analysis has been run yet."

    lines: list[str] = []
    for season, result in results.items():
        metrics = result.get("metrics")
        if isinstance(metrics, pd.DataFrame) and not metrics.empty:
            best_model = result.get("best_model", metrics.iloc[0]["Model"])
            ranked = ", ".join(
                f"{row['Model']} (R²={_fmt(row['Bias-corrected test R2'])}, RMSE={_fmt(row['Bias-corrected test RMSE'])} mbgl, KGE={_fmt(row.get('Bias-corrected test KGE'))})"
                for _, row in metrics.iterrows()
            )
            sel_feats = ", ".join(result.get("selected_features", []))
            lofo = result.get("lofo")
            lofo_str = ""
            if isinstance(lofo, pd.DataFrame) and not lofo.empty and "Feature" in lofo.columns:
                top_lofo = [
                    f"{r['Feature']} (Δr={_fmt(r.get('Correlation drop'), 4)})"
                    for _, r in lofo.head(3).iterrows()
                ]
                lofo_str = f" Top LOFO Sensitivity Drivers: {', '.join(top_lofo)}."
            lines.append(
                f"**{season}**: Headline Winner = {best_model}. Full Model Rankings: {ranked}. "
                f"Selected Features: {sel_feats}.{lofo_str}"
            )
        else:
            lines.append(f"**{season}**: No headline results available.")

        if result.get("low_data_rescue_used"):
            lines.append(
                f"  (Note for {season}: dataset was small; missing lag values were imputed instead of dropped.)"
            )
    return "\n".join(lines)


def summarize_forecasts(results: dict[str, dict[str, Any]]) -> str:
    """A text summary of multi-year scenario forecasts for headline and deep models."""
    if not results:
        return ""
    lines: list[str] = []
    for season, result in results.items():
        fc = result.get("forecast")
        if isinstance(fc, pd.DataFrame) and not fc.empty:
            year_col = "Year" if "Year" in fc.columns else ("YEAR" if "YEAR" in fc.columns else None)
            val_col = "Scenario forecast DTWL (mbgl)" if "Scenario forecast DTWL (mbgl)" in fc.columns else None
            if year_col and val_col:
                fc_str = ", ".join(f"{int(r[year_col])}: {float(r[val_col]):.2f} mbgl" for _, r in fc.iterrows())
                lines.append(f"Headline Model Forecast ({result.get('best_model')}) for {season}: {fc_str}.")

        deep_fc = result.get("deep_forecast")
        if isinstance(deep_fc, pd.DataFrame) and not deep_fc.empty:
            year_col = "Year" if "Year" in deep_fc.columns else ("YEAR" if "YEAR" in deep_fc.columns else None)
            val_col = "Scenario forecast DTWL (mbgl)" if "Scenario forecast DTWL (mbgl)" in deep_fc.columns else None
            if year_col and val_col:
                dfc_str = ", ".join(f"{int(r[year_col])}: {float(r[val_col]):.2f} mbgl" for _, r in deep_fc.iterrows())
                lines.append(f"Deep Model Forecast ({result.get('deep_best_model')}) for {season}: {dfc_str}.")
    return "\n".join(lines)


def summarize_deep_results(results: dict[str, dict[str, Any]]) -> str:
    """A compact text summary of the separate PINN / ESN / SARIMA / LSTM tab."""
    lines: list[str] = []
    for season, result in results.items():
        deep_metrics = result.get("deep_metrics")
        if deep_metrics is None or deep_metrics.empty:
            continue
        top = deep_metrics.iloc[0]
        ranked = ", ".join(
            f"{row['Model']} (R²={_fmt(row['Bias-corrected test R2'])}, RMSE={_fmt(row['Bias-corrected test RMSE'])} mbgl)"
            for _, row in deep_metrics.iterrows()
        )
        lines.append(
            f"**{season} (Deep Learning Tab)**: Best = {result.get('deep_best_model')}, "
            f"Bias-Corrected Test R² = {_fmt(top['Bias-corrected test R2'])}, "
            f"RMSE = {_fmt(top['Bias-corrected test RMSE'])} mbgl. All Deep Models: {ranked}."
        )
    if not lines:
        return ""
    return "\n".join(lines)


def summarize_dataset(payload: dict[str, Any]) -> str:
    """A compact text summary of the uploaded workbook including geospatial coverage."""
    data = payload.get("clean_data")
    if data is None or data.empty:
        return "No dataset is loaded."
    districts = (
        f", districts: {', '.join(sorted(data['DISTRICT'].dropna().astype(str).unique()))}"
        if "DISTRICT" in data.columns and data["DISTRICT"].notna().any()
        else ""
    )
    coords_note = (
        " (WGS84 LATITUDE/LONGITUDE coordinates available)"
        if {"LATITUDE", "LONGITUDE"}.issubset(data.columns) and data[["LATITUDE", "LONGITUDE"]].notna().all(axis=1).any()
        else " (no spatial coordinates in workbook)"
    )
    return (
        f"Uploaded workbook: {len(data):,} rows, "
        f"{data['VILLAGE'].nunique()} villages{districts}, "
        f"years {int(data['YEAR'].min())}–{int(data['YEAR'].max())}, "
        f"seasons present: {', '.join(sorted(data['Season'].unique()))}{coords_note}."
    )


def summarize_digital_twin_state(twin_state: dict[str, Any] | None) -> str:
    """Format the active Digital Twin state, selected asset, and simulation outputs for RAG grounding."""
    if not twin_state or not isinstance(twin_state, dict):
        return ""
    season = twin_state.get("season", "N/A")
    year = twin_state.get("year", "N/A")
    district = twin_state.get("district", "All available")
    block = twin_state.get("block", "All available")
    mode = twin_state.get("mode", "Observed")
    provenance = twin_state.get("provenance", "Verified Historical Observation")
    asset_info = twin_state.get("asset_info") or {}
    state = twin_state.get("state") or {}
    base = twin_state.get("baseline_state") or {}

    asset_name = asset_info.get("name", twin_state.get("selected_asset", "All villages"))
    usd_path = asset_info.get("usd_path", "/World/RajasthanBasin")
    stress_cat = (asset_info.get("stress_status") or {}).get("category", "N/A")
    hist_mean = _fmt(asset_info.get("historical_mean_dtwl"), 2)
    hist_min = _fmt(asset_info.get("historical_min_dtwl"), 2)
    hist_max = _fmt(asset_info.get("historical_max_dtwl"), 2)
    slope = _fmt(asset_info.get("trend_slope_mbgl_yr"), 3)
    lat = asset_info.get("latitude")
    lon = asset_info.get("longitude")
    coords = f"({lat:.4f}°N, {lon:.4f}°E)" if (lat is not None and lon is not None) else "Basin aggregate"

    lines = [
        f"Active Digital Twin State [Mode: {mode} | Provenance: {provenance}]:",
        f"- Selected Asset: {asset_name} (USD Path: `{usd_path}`, Coordinates: {coords}, District: {district}, Block: {block})",
        f"- Temporal Slice: Season = {season}, Year = {year}",
        f"- Active Measurements: DTWL = {_fmt(state.get('dtwl'), 2)} mbgl (Water Stress Status: {stress_cat}), "
        f"Rainfall = {_fmt(state.get('rainfall'), 2)} mm, ET = {_fmt(state.get('et'), 2)} mm, "
        f"Soil Moisture = {_fmt(state.get('soil'), 2)}%, NDVI = {_fmt(state.get('ndvi'), 3)}, "
        f"Water Balance = {_fmt(state.get('balance'), 2)} mm, GW Stress Ratio = {_fmt(state.get('stress'), 2)}",
        f"- Asset Historical Profile ({asset_info.get('year_range', 'N/A')}): "
        f"Mean DTWL = {hist_mean} mbgl, Range = {hist_min}–{hist_max} mbgl, Long-Term Trend Slope = {slope} mbgl/yr",
    ]

    alerts = asset_info.get("alerts") or []
    if alerts:
        lines.append(f"- Active Asset Alerts: {' | '.join(alerts)}")

    sim_summary = twin_state.get("simulation_summary")
    if mode == "Simulated" and isinstance(sim_summary, dict):
        params = twin_state.get("scenario_params") or {}
        deltas = sim_summary.get("deltas") or {}
        m_out = sim_summary.get("model_outputs") or {}
        lines.append(
            f"- Active Simulation Scenario ({twin_state.get('scenario_preset', 'Custom')}): "
            f"Rainfall {params.get('rainfall_pct', 0):+.1f}%, ET {params.get('et_pct', 0):+.1f}%, "
            f"Soil Moisture {params.get('sm_delta', 0):+.1f}%, Temp {params.get('temp_delta_c', 0):+.1f}°C, "
            f"Pumping Factor {params.get('pumping_factor', 1.0):.2f}x"
        )
        lines.append(
            f"- Coupled Simulation Outputs vs Baseline ({_fmt(base.get('dtwl'), 2)} mbgl): "
            f"Coupled DTWL = {_fmt(m_out.get('coupled_dtwl'), 2)} mbgl (Δ = {_fmt(deltas.get('dtwl'), 2)} mbgl, "
            f"95% CI: [{_fmt(m_out.get('lower_95_ci'), 2)}–{_fmt(m_out.get('upper_95_ci'), 2)}] mbgl), "
            f"Headline ML ({m_out.get('best_ml_model')}) = {_fmt(m_out.get('ml_simulated_dtwl'), 2)} mbgl, "
            f"Deep/PINN ({m_out.get('best_deep_model')}) = {_fmt(m_out.get('deep_simulated_dtwl'), 2)} mbgl."
        )
    return "\n".join(lines)


def build_job_context(payload: dict[str, Any] | None, twin_state: dict[str, Any] | None = None) -> str:
    """Assemble the full grounding context: dataset + Digital Twin state + per-season results + forecasts."""
    if not payload:
        return "No analysis has been run in this session yet."
    parts = [summarize_dataset(payload)]
    twin_summary = summarize_digital_twin_state(twin_state)
    if twin_summary:
        parts.append(twin_summary)
    results = payload.get("results") or {}
    if results:
        parts.append("Season-wise Headline Model Results & Rankings:")
        parts.append(summarize_results(results))
        fc_summary = summarize_forecasts(results)
        if fc_summary:
            parts.append("Multi-Year Scenario Forecasts (Headline & Deep Models):")
            parts.append(fc_summary)
        deep_summary = summarize_deep_results(results)
        if deep_summary:
            parts.append("Season-wise Deep Learning & Physics-Informed Model Results (PINN, ESN, SARIMA, LSTM):")
            parts.append(deep_summary)
    return "\n\n".join(parts)
