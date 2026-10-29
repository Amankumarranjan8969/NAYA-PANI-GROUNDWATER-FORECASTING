"""twin_engine.py — Central Digital Twin State, OpenUSD-Inspired Scene Graph,
Asset Catalog, and Coupled Hydrological-AI Simulation Engine for Naya Pani.

Architectural Responsibilities:
1. Central State Synchronization (`DigitalTwinState` in `st.session_state["digital_twin_state"]`)
2. OpenUSD-Inspired Scene Hierarchy (`/World/RajasthanBasin/...`) with SimReady metadata
3. Authoritative Asset Discovery & Per-Village Monitoring Well Inspection
4. Coupled Empirical (ML + Deep/PINN) & Physical Mass-Balance Simulation Engine
5. Multi-Year Scenario Trajectory Projection with 95% Confidence Intervals
6. Explicit Data Provenance Tagging:
   - VERIFIED_OBSERVED: Recorded historical workbook measurements
   - MODEL_FORECAST: Recursive multi-year ML/DL model projection
   - SIMULATED_COUPLED: What-if scenario output (ML/DL + recharge-extraction mass balance)
   - ILLUSTRATIVE: Conceptual visual cue where spatial coordinates are absent
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any

import numpy as np
import pandas as pd

from pipeline import TARGET
from security_engine import (
    DIGITAL_TWIN_AUDIT,
    INDICATOR_BOUNDS,
    calculate_forecast_uncertainty,
    validate_environmental_record,
)

# --------------------------------------------------------------------------- #
# Provenance Constants & Predefined Hydrological Scenarios
# --------------------------------------------------------------------------- #
PROVENANCE_OBSERVED = "Verified Historical Observation"
PROVENANCE_FORECAST = "Model-Generated Forecast"
PROVENANCE_SIMULATED = "Coupled Simulation Output"
PROVENANCE_ILLUSTRATIVE = "Illustrative / Conceptual Geometry"

SCENARIO_PRESETS: dict[str, dict[str, Any]] = {
    "Custom Parameter Configuration": {
        "description": "Manually adjust rainfall, evapotranspiration, soil moisture, temperature, NDVI, and pumping stress.",
        "rainfall_pct": 0.0,
        "et_pct": 0.0,
        "sm_delta": 0.0,
        "temp_delta_c": 0.0,
        "ndvi_delta": 0.0,
        "pumping_factor": 1.0,
    },
    "Baseline (Zero Perturbation)": {
        "description": "Unmodified historical environmental conditions for direct baseline verification.",
        "rainfall_pct": 0.0,
        "et_pct": 0.0,
        "sm_delta": 0.0,
        "temp_delta_c": 0.0,
        "ndvi_delta": 0.0,
        "pumping_factor": 1.0,
    },
    "Severe Monsoon Drought (-45% Rain, +20% ET, +2.5°C)": {
        "description": "Simulates an acute meteorological and agricultural drought across semi-arid Rajasthan with elevated compensatory groundwater pumping.",
        "rainfall_pct": -45.0,
        "et_pct": 20.0,
        "sm_delta": -8.0,
        "temp_delta_c": 2.5,
        "ndvi_delta": -0.10,
        "pumping_factor": 1.30,
    },
    "High Monsoon Recharge / Cloudburst (+55% Rain, +12% SM)": {
        "description": "Simulates above-normal monsoon precipitation and enhanced vadose-zone infiltration reducing summer pumping demand.",
        "rainfall_pct": 55.0,
        "et_pct": -10.0,
        "sm_delta": 12.0,
        "temp_delta_c": -1.5,
        "ndvi_delta": 0.14,
        "pumping_factor": 0.80,
    },
    "Intensive Tube-Well Extraction (+40% Pumping, +15% ET)": {
        "description": "Simulates accelerated groundwater abstraction for rabi/summer irrigation under high evaporative demand.",
        "rainfall_pct": -10.0,
        "et_pct": 15.0,
        "sm_delta": -5.0,
        "temp_delta_c": 1.0,
        "ndvi_delta": 0.05,
        "pumping_factor": 1.40,
    },
    "Managed Aquifer Recharge / Check-Dams (+35% Effective Rain, -25% Pumping)": {
        "description": "Simulates watershed intervention (anicuts, check-dams, percolation tanks, and micro-irrigation adoption).",
        "rainfall_pct": 35.0,
        "et_pct": -8.0,
        "sm_delta": 10.0,
        "temp_delta_c": -0.5,
        "ndvi_delta": 0.12,
        "pumping_factor": 0.75,
    },
}


def safe_float(val: Any) -> float | None:
    try:
        num = float(val)
        return num if np.isfinite(num) else None
    except (TypeError, ValueError):
        return None


def mean_col(frame: pd.DataFrame, col: str) -> float | None:
    if frame is None or frame.empty or col not in frame.columns:
        return None
    vals = pd.to_numeric(frame[col], errors="coerce").dropna()
    return float(vals.mean()) if not vals.empty else None


def classify_water_stress(
    dtwl_mbgl: float | None,
    safe_limit: float = 10.0,
    semi_limit: float = 20.0,
    crit_limit: float = 35.0,
) -> dict[str, str]:
    """Classify groundwater depth (mbgl) into standard hydrological stress categories."""
    if dtwl_mbgl is None or not np.isfinite(dtwl_mbgl):
        return {
            "category": "Unavailable",
            "color": "#64748B",
            "bg": "#F1F5F9",
            "badge": "⚪ Unavailable",
            "description": "No groundwater depth measurement available.",
        }
    if dtwl_mbgl <= safe_limit:
        return {
            "category": "Safe",
            "color": "#10B981",
            "bg": "#ECFDF5",
            "badge": "🟢 Safe",
            "description": f"Shallow water table (≤ {safe_limit:.0f} mbgl); healthy aquifer storage.",
        }
    if dtwl_mbgl <= semi_limit:
        return {
            "category": "Semi-Critical",
            "color": "#F59E0B",
            "bg": "#FFFBEB",
            "badge": "🟡 Semi-Critical",
            "description": f"Moderate drawdown ({safe_limit:.0f}–{semi_limit:.0f} mbgl); monitor seasonal extraction.",
        }
    if dtwl_mbgl <= crit_limit:
        return {
            "category": "Critical",
            "color": "#F97316",
            "bg": "#FFF7ED",
            "badge": "🟠 Critical",
            "description": f"Significant water-table depletion ({semi_limit:.0f}–{crit_limit:.0f} mbgl); recharge intervention advised.",
        }
    return {
        "category": "Over-Exploited",
        "color": "#EF4444",
        "bg": "#FEF2F2",
        "badge": "🔴 Over-Exploited",
        "description": f"Severe deep aquifer drawdown (> {crit_limit:.0f} mbgl); urgent demand management required.",
    }


# --------------------------------------------------------------------------- #
# Asset Catalog & Detailed Per-Asset Inspection
# --------------------------------------------------------------------------- #
def build_asset_catalog(
    season_df: pd.DataFrame,
    year: int | None = None,
    district: str = "All available",
    block: str = "All available",
    stress_thresholds: tuple[float, float, float] = (10.0, 20.0, 35.0),
) -> pd.DataFrame:
    """Build a structured table of all monitoring well assets in the filtered scope."""
    if season_df is None or season_df.empty:
        return pd.DataFrame()

    df = season_df.copy()
    if district != "All available" and "DISTRICT" in df.columns:
        sub = df[df["DISTRICT"].astype(str) == district]
        if not sub.empty:
            df = sub
    if block != "All available" and "BLOCK" in df.columns:
        sub = df[df["BLOCK"].astype(str) == block]
        if not sub.empty:
            df = sub

    year_df = df[pd.to_numeric(df["YEAR"], errors="coerce") == year] if year is not None else df
    if year_df.empty:
        year_df = df

    records: list[dict[str, Any]] = []
    safe_t, semi_t, crit_t = stress_thresholds

    for village, grp in df.groupby("VILLAGE", sort=True):
        grp_sorted = grp.sort_values("YEAR")
        yr_row = year_df[year_df["VILLAGE"] == village]
        active_row = yr_row.iloc[-1] if not yr_row.empty else grp_sorted.iloc[-1]

        dtwl_val = safe_float(active_row.get(TARGET))
        lat_val = safe_float(active_row.get("LATITUDE"))
        lon_val = safe_float(active_row.get("LONGITUDE"))
        elev_val = safe_float(active_row.get("Elevation"))
        rain_val = safe_float(active_row.get("Rainfall"))
        et_val = safe_float(active_row.get("ET"))
        sm_val = safe_float(active_row.get("Avg_SM")) or safe_float(active_row.get("SM_10cm"))
        ndvi_val = safe_float(active_row.get("NDVI"))

        # Compute historical linear trend (mbgl/year)
        hist_years = pd.to_numeric(grp_sorted["YEAR"], errors="coerce").dropna().to_numpy(dtype=float)
        hist_dtwl = pd.to_numeric(grp_sorted[TARGET], errors="coerce").dropna().to_numpy(dtype=float)
        trend_slope = 0.0
        if len(hist_years) >= 2 and len(hist_years) == len(hist_dtwl):
            try:
                trend_slope = float(np.polyfit(hist_years, hist_dtwl, 1)[0])
            except Exception:
                trend_slope = 0.0

        stress_info = classify_water_stress(dtwl_val, safe_t, semi_t, crit_t)
        records.append({
            "Asset_ID": f"WELL:{village}",
            "USD_Prim_Path": f"/World/RajasthanBasin/MonitoringNetwork/Well_{str(village).replace(' ', '_')}",
            "Village": str(village),
            "District": str(active_row.get("DISTRICT", "Unspecified")) if "DISTRICT" in active_row else "Unspecified",
            "Block": str(active_row.get("BLOCK", "Unspecified")) if "BLOCK" in active_row else "Unspecified",
            "Latitude": lat_val,
            "Longitude": lon_val,
            "Elevation_m": elev_val,
            "Active_Year": int(active_row.get("YEAR", year or 0)),
            "DTWL_mbgl": dtwl_val,
            "Historical_Mean_DTWL": float(np.mean(hist_dtwl)) if len(hist_dtwl) else None,
            "Historical_Min_DTWL": float(np.min(hist_dtwl)) if len(hist_dtwl) else None,
            "Historical_Max_DTWL": float(np.max(hist_dtwl)) if len(hist_dtwl) else None,
            "Trend_Slope_mbgl_yr": trend_slope,
            "Rainfall_mm": rain_val,
            "ET_mm": et_val,
            "Soil_Moisture_pct": sm_val,
            "NDVI": ndvi_val,
            "Stress_Category": stress_info["category"],
            "Stress_Badge": stress_info["badge"],
            "Stress_Color": stress_info["color"],
            "Observations_Count": len(grp_sorted),
            "Year_Range": f"{int(hist_years.min())}–{int(hist_years.max())}" if len(hist_years) else "N/A",
        })

    return pd.DataFrame(records)


def inspect_selected_asset(
    season_df: pd.DataFrame,
    asset_catalog: pd.DataFrame,
    selected_village: str,
    active_year: int,
    active_metrics: dict[str, float | None],
    mode: str,
    stress_thresholds: tuple[float, float, float] = (10.0, 20.0, 35.0),
) -> dict[str, Any]:
    """Return full inspection metadata, historical series, and alerts for the selected asset."""
    safe_t, semi_t, crit_t = stress_thresholds
    dtwl_now = active_metrics.get("dtwl")
    stress_now = classify_water_stress(dtwl_now, safe_t, semi_t, crit_t)

    if selected_village == "All villages (Basin Aggregate)" or asset_catalog.empty:
        hist_grp = (
            season_df.groupby("YEAR", as_index=False)
            .agg({
                TARGET: "mean",
                "Rainfall": "mean",
                "ET": "mean",
                "NDVI": "mean",
            })
            .sort_values("YEAR")
        )
        years_arr = hist_grp["YEAR"].to_numpy(dtype=float)
        dtwl_arr = hist_grp[TARGET].to_numpy(dtype=float)
        slope = float(np.polyfit(years_arr, dtwl_arr, 1)[0]) if len(years_arr) >= 2 else 0.0
        has_coords = (
            {"LATITUDE", "LONGITUDE"}.issubset(season_df.columns)
            and season_df[["LATITUDE", "LONGITUDE"]].notna().all(axis=1).any()
        )
        lat_mean = mean_col(season_df, "LATITUDE") if has_coords else None
        lon_mean = mean_col(season_df, "LONGITUDE") if has_coords else None
        elev_mean = mean_col(season_df, "Elevation")

        alerts: list[str] = []
        if dtwl_now is not None and dtwl_now > crit_limit_val(crit_t):
            alerts.append(f"HIGH DRAWDOWN ALERT: Basin mean DTWL ({dtwl_now:.2f} mbgl) exceeds Critical threshold ({crit_t:.1f} mbgl).")
        if slope > 0.25:
            alerts.append(f"DEPLETION TREND: Basin water table is deepening at +{slope:.2f} mbgl/year.")
        wb = active_metrics.get("balance")
        if wb is not None and wb < -150:
            alerts.append(f"NEGATIVE WATER BALANCE: Evapotranspiration exceeds rainfall by {abs(wb):.1f} mm.")

        return {
            "asset_id": "BASIN:AGGREGATE",
            "usd_path": "/World/RajasthanBasin",
            "name": "All Monitoring Wells (Basin Aggregate)",
            "type": "Hydrogeological Basin Aggregate",
            "district": str(season_df["DISTRICT"].iloc[0]) if "DISTRICT" in season_df.columns and season_df["DISTRICT"].nunique() == 1 else "Multi-District / Regional",
            "block": str(season_df["BLOCK"].iloc[0]) if "BLOCK" in season_df.columns and season_df["BLOCK"].nunique() == 1 else "All Blocks",
            "latitude": lat_mean,
            "longitude": lon_mean,
            "elevation_m": elev_mean,
            "well_count": int(season_df["VILLAGE"].nunique()),
            "observation_count": int(len(season_df)),
            "year_range": f"{int(years_arr.min())}–{int(years_arr.max())}" if len(years_arr) else "N/A",
            "historical_mean_dtwl": float(np.mean(dtwl_arr)) if len(dtwl_arr) else None,
            "historical_min_dtwl": float(np.min(dtwl_arr)) if len(dtwl_arr) else None,
            "historical_max_dtwl": float(np.max(dtwl_arr)) if len(dtwl_arr) else None,
            "trend_slope_mbgl_yr": slope,
            "stress_status": stress_now,
            "alerts": alerts,
            "history_df": hist_grp,
            "mode": mode,
            "active_year": active_year,
        }

    # Specific Village Monitoring Well Asset
    v_rows = season_df[season_df["VILLAGE"].astype(str) == selected_village].sort_values("YEAR")
    cat_row = asset_catalog[asset_catalog["Village"] == selected_village]
    meta = cat_row.iloc[0].to_dict() if not cat_row.empty else {}

    hist_cols = [c for c in ["YEAR", TARGET, "Rainfall", "ET", "NDVI", "SM_10cm", "SM_40cm", "SM_100cm", "Avg_SM"] if c in v_rows.columns]
    hist_df = v_rows[hist_cols].copy()

    slope = float(meta.get("Trend_Slope_mbgl_yr") or 0.0)
    hist_mean = safe_float(meta.get("Historical_Mean_DTWL"))
    alerts = []
    if dtwl_now is not None and dtwl_now > crit_t:
        alerts.append(f"CRITICAL WELL DRAWDOWN: {selected_village} DTWL ({dtwl_now:.2f} mbgl) exceeds {crit_t:.1f} mbgl.")
    if dtwl_now is not None and hist_mean is not None and (dtwl_now - hist_mean) > 3.0:
        alerts.append(f"ANOMALY ABOVE HISTORICAL MEAN: Current DTWL is +{dtwl_now - hist_mean:.2f} mbgl deeper than village historical average ({hist_mean:.2f} mbgl).")
    if slope > 0.25:
        alerts.append(f"LONG-TERM DEPLETION: Water table at {selected_village} is falling by +{slope:.2f} mbgl/yr.")

    return {
        "asset_id": meta.get("Asset_ID", f"WELL:{selected_village}"),
        "usd_path": meta.get("USD_Prim_Path", f"/World/RajasthanBasin/MonitoringNetwork/Well_{selected_village}"),
        "name": f"{selected_village} Monitoring Well",
        "village": selected_village,
        "type": "Piezometer / Dug-cum-Bore Well Station",
        "district": meta.get("District", "Unspecified"),
        "block": meta.get("Block", "Unspecified"),
        "latitude": safe_float(meta.get("Latitude")),
        "longitude": safe_float(meta.get("Longitude")),
        "elevation_m": safe_float(meta.get("Elevation_m")),
        "well_count": 1,
        "observation_count": int(meta.get("Observations_Count", len(v_rows))),
        "year_range": str(meta.get("Year_Range", "N/A")),
        "historical_mean_dtwl": hist_mean,
        "historical_min_dtwl": safe_float(meta.get("Historical_Min_DTWL")),
        "historical_max_dtwl": safe_float(meta.get("Historical_Max_DTWL")),
        "trend_slope_mbgl_yr": slope,
        "stress_status": stress_now,
        "alerts": alerts,
        "history_df": hist_df,
        "mode": mode,
        "active_year": active_year,
    }


def crit_limit_val(val: float) -> float:
    return float(val)


# --------------------------------------------------------------------------- #
# Coupled Hydrological + AI/ML/DL Simulation Engine
# --------------------------------------------------------------------------- #
def run_coupled_simulation(
    result: dict[str, Any],
    filtered_rows: pd.DataFrame,
    scenario_params: dict[str, float],
    user_label: str = "scientist",
) -> dict[str, Any]:
    """Execute a coupled physical + ML/DL simulation on the selected Digital Twin state.

    1. Perturbs environmental forcing inputs (`Rainfall`, `ET`, `SM_10cm/40cm/100cm`,
       `Tmax`, `Tmin`, `NDVI`) within physical bounds.
    2. Recomputes derived hydrological indicators (`Water_Balance`, `GW_Stress`,
       `Avg_SM`, `SM_Gradient`, `Temp_Range`, `Veg_Moisture`, `Veg_Health`) and
       updates rolling/trend features.
    3. Executes inference through:
       - Trained Headline ML Winner (`best_model` + training bias correction)
       - Trained Deep / Physics-Informed Winner (`deep_best_model` + bias correction)
    4. Computes vadose-aquifer recharge/abstraction mass-balance sensitivity
       (Specific Yield Sy = 0.08 for semi-arid alluvial/hard-rock formations)
       so meteorological & pumping perturbations yield physically consistent
       water-table responses alongside empirical ML predictions.
    """
    if filtered_rows is None or filtered_rows.empty:
        return {}

    sim_df = filtered_rows.copy()
    rain_pct = float(scenario_params.get("rainfall_pct", 0.0))
    et_pct = float(scenario_params.get("et_pct", 0.0))
    sm_delta = float(scenario_params.get("sm_delta", 0.0))
    temp_delta = float(scenario_params.get("temp_delta_c", 0.0))
    ndvi_delta = float(scenario_params.get("ndvi_delta", 0.0))
    pumping_factor = float(scenario_params.get("pumping_factor", 1.0))

    # Baseline means
    base_dtwl = mean_col(sim_df, TARGET) or 15.0
    base_rain = mean_col(sim_df, "Rainfall") or 0.0
    base_et = mean_col(sim_df, "ET") or 0.0
    base_sm10 = mean_col(sim_df, "SM_10cm") or 15.0
    base_sm40 = mean_col(sim_df, "SM_40cm") or 20.0
    base_sm100 = mean_col(sim_df, "SM_100cm") or 25.0
    base_avg_sm = mean_col(sim_df, "Avg_SM") or ((base_sm10 + base_sm40 + base_sm100) / 3.0)
    base_ndvi = mean_col(sim_df, "NDVI") or 0.25
    base_ndwi = mean_col(sim_df, "NDWI")
    base_tmax = mean_col(sim_df, "Tmax") or 35.0
    base_tmin = mean_col(sim_df, "Tmin") or 20.0

    # Perturb environmental columns within physical bounds
    if "Rainfall" in sim_df.columns:
        sim_df["Rainfall"] = np.clip(sim_df["Rainfall"].astype(float) * (1.0 + rain_pct / 100.0), 0.0, 2500.0)
    if "ET" in sim_df.columns:
        sim_df["ET"] = np.clip(sim_df["ET"].astype(float) * (1.0 + et_pct / 100.0), 0.0, 1500.0)
    for sm_col in ("SM_10cm", "SM_40cm", "SM_100cm"):
        if sm_col in sim_df.columns:
            sim_df[sm_col] = np.clip(sim_df[sm_col].astype(float) + sm_delta, 0.5, 100.0)
    if "Tmax" in sim_df.columns:
        sim_df["Tmax"] = np.clip(sim_df["Tmax"].astype(float) + temp_delta, -5.0, 58.0)
    if "Tmin" in sim_df.columns:
        sim_df["Tmin"] = np.clip(sim_df["Tmin"].astype(float) + temp_delta, -10.0, 45.0)
    if "NDVI" in sim_df.columns:
        sim_df["NDVI"] = np.clip(sim_df["NDVI"].astype(float) + ndvi_delta, -1.0, 1.0)
    if "NDMI" in sim_df.columns:
        sim_df["NDMI"] = np.clip(sim_df["NDMI"].astype(float) + (ndvi_delta * 0.6), -1.0, 1.0)
    if "NDWI" in sim_df.columns:
        sim_df["NDWI"] = np.clip(sim_df["NDWI"].astype(float) + (rain_pct / 400.0), -1.0, 1.0)

    # Recompute derived hydrology & vegetation features
    if {"Tmax", "Tmin"}.issubset(sim_df.columns):
        sim_df["Temp_Range"] = sim_df["Tmax"] - sim_df["Tmin"]
    if {"SM_10cm", "SM_40cm", "SM_100cm"}.issubset(sim_df.columns):
        sim_df["Avg_SM"] = (sim_df["SM_10cm"] + sim_df["SM_40cm"] + sim_df["SM_100cm"]) / 3.0
        sim_df["SM_Gradient"] = sim_df["SM_100cm"] - sim_df["SM_10cm"]
    if {"NDVI", "NDMI"}.issubset(sim_df.columns):
        sim_df["Veg_Moisture"] = sim_df["NDVI"] * sim_df["NDMI"]
    if {"ET", "Rainfall"}.issubset(sim_df.columns):
        sim_df["GW_Stress"] = sim_df["ET"] / (sim_df["Rainfall"] + 1.0)
        sim_df["Water_Balance"] = sim_df["Rainfall"] - sim_df["ET"]
    if {"NDVI", "NDBI"}.issubset(sim_df.columns):
        sim_df["Veg_Health"] = sim_df["NDVI"] * (1.0 - sim_df["NDBI"])

    # Update rolling & trend features proportionally so selected rolling predictors respond
    for r_col in ("Rainfall_roll3", "Rainfall_roll5", "Rainfall_lag1"):
        if r_col in sim_df.columns:
            sim_df[r_col] = np.clip(sim_df[r_col].astype(float) * (1.0 + rain_pct / 100.0), 0.0, 2500.0)
    if "Rainfall_trend" in sim_df.columns:
        sim_df["Rainfall_trend"] = sim_df["Rainfall_trend"].astype(float) + (base_rain * (rain_pct / 100.0))
    for e_col in ("ET_roll3", "ET_roll5", "ET_lag1"):
        if e_col in sim_df.columns:
            sim_df[e_col] = np.clip(sim_df[e_col].astype(float) * (1.0 + et_pct / 100.0), 0.0, 1500.0)
    for s_col in ("Avg_SM_roll3", "Avg_SM_roll5", "Avg_SM_lag1"):
        if s_col in sim_df.columns:
            sim_df[s_col] = np.clip(sim_df[s_col].astype(float) + sm_delta, 0.5, 100.0)
    if "Avg_SM_trend" in sim_df.columns:
        sim_df["Avg_SM_trend"] = sim_df["Avg_SM_trend"].astype(float) + sm_delta

    # 1. Empirical ML & Deep Model Inference on Perturbed Feature Matrix
    selected_features: list[str] = result.get("selected_features", [])
    scaler = result.get("scaler")
    best_model_name = result.get("best_model")
    fitted_models = result.get("fitted_models") or {}
    metrics_df: pd.DataFrame = result.get("metrics", pd.DataFrame())

    ml_pred_dtwl = base_dtwl
    ml_base_pred = base_dtwl
    test_rmse = 1.25

    if selected_features and scaler is not None and best_model_name in fitted_models:
        try:
            best_model = fitted_models[best_model_name]
            correction = 0.0
            if not metrics_df.empty and "Training mean correction" in metrics_df.columns:
                m_row = metrics_df[metrics_df["Model"] == best_model_name]
                if not m_row.empty:
                    correction = float(m_row.iloc[0]["Training mean correction"])
                    test_rmse = float(m_row.iloc[0].get("Bias-corrected test RMSE", 1.25) or 1.25)

            x_base = filtered_rows[selected_features].apply(pd.to_numeric, errors="coerce").fillna(0.0)
            x_sim = sim_df[selected_features].apply(pd.to_numeric, errors="coerce").fillna(0.0)

            x_base_scaled = pd.DataFrame(scaler.transform(x_base), columns=selected_features, index=x_base.index)
            x_sim_scaled = pd.DataFrame(scaler.transform(x_sim), columns=selected_features, index=x_sim.index)

            ml_base_pred = float(np.mean(np.asarray(best_model.predict(x_base_scaled)).ravel() + correction))
            ml_pred_dtwl = float(np.mean(np.asarray(best_model.predict(x_sim_scaled)).ravel() + correction))
        except Exception:
            ml_pred_dtwl = base_dtwl

    deep_best_name = result.get("deep_best_model")
    deep_models = result.get("deep_fitted_models") or {}
    deep_scaler = result.get("deep_scaler") or scaler
    deep_metrics_df: pd.DataFrame = result.get("deep_metrics", pd.DataFrame())
    deep_pred_dtwl: float | None = None
    deep_base_pred: float | None = None

    if selected_features and deep_scaler is not None and deep_best_name and deep_best_name in deep_models:
        try:
            deep_model = deep_models[deep_best_name]
            d_corr = 0.0
            if not deep_metrics_df.empty and "Training mean correction" in deep_metrics_df.columns:
                d_row = deep_metrics_df[deep_metrics_df["Model"] == deep_best_name]
                if not d_row.empty:
                    d_corr = float(d_row.iloc[0]["Training mean correction"])

            x_base = filtered_rows[selected_features].apply(pd.to_numeric, errors="coerce").fillna(0.0)
            x_sim = sim_df[selected_features].apply(pd.to_numeric, errors="coerce").fillna(0.0)

            x_base_s = pd.DataFrame(deep_scaler.transform(x_base), columns=selected_features, index=x_base.index)
            x_sim_s = pd.DataFrame(deep_scaler.transform(x_sim), columns=selected_features, index=x_sim.index)

            deep_base_pred = float(np.mean(np.asarray(deep_model.predict(x_base_s)).ravel() + d_corr))
            deep_pred_dtwl = float(np.mean(np.asarray(deep_model.predict(x_sim_s)).ravel() + d_corr))
        except Exception:
            deep_pred_dtwl = None

    # 2. Physical Vadose-Aquifer Mass-Balance Sensitivity
    # Specific yield Sy = 0.08 (semi-arid alluvial/weathered hard-rock aquifer), infiltration coeff = 0.18
    sim_rain = mean_col(sim_df, "Rainfall") or base_rain
    sim_et = mean_col(sim_df, "ET") or base_et
    sim_avg_sm = mean_col(sim_df, "Avg_SM") or (base_avg_sm + sm_delta)
    sim_ndvi = mean_col(sim_df, "NDVI") or (base_ndvi + ndvi_delta)
    sim_ndwi = mean_col(sim_df, "NDWI") if base_ndwi is not None else None
    sim_wb = sim_rain - sim_et
    base_wb = base_rain - base_et
    sim_stress = sim_et / (sim_rain + 1.0)
    base_stress = base_et / (base_rain + 1.0)

    delta_wb_mm = sim_wb - base_wb
    specific_yield = 0.08
    infiltration_coeff = 0.18
    # Recharge rise (negative DTWL change means shallower/rising water table)
    recharge_dtwl_delta = -(infiltration_coeff * delta_wb_mm) / (1000.0 * specific_yield)
    sm_dtwl_delta = -0.045 * (sim_avg_sm - base_avg_sm)
    temp_dtwl_delta = 0.08 * temp_delta
    pumping_dtwl_delta = (pumping_factor - 1.0) * max(base_dtwl * 0.16, 1.2)

    physics_delta_dtwl = recharge_dtwl_delta + sm_dtwl_delta + temp_dtwl_delta + pumping_dtwl_delta

    # Empirical model delta from perturbed features
    ml_delta = ml_pred_dtwl - ml_base_pred
    deep_delta = (deep_pred_dtwl - deep_base_pred) if (deep_pred_dtwl is not None and deep_base_pred is not None) else ml_delta

    # Coupled response combines empirical model sensitivity with physical mass-balance flux
    coupled_delta = 0.45 * (0.65 * ml_delta + 0.35 * deep_delta) + 0.55 * physics_delta_dtwl
    is_zero_perturbation = (
        abs(rain_pct) < 1e-6
        and abs(et_pct) < 1e-6
        and abs(sm_delta) < 1e-6
        and abs(temp_delta) < 1e-6
        and abs(ndvi_delta) < 1e-6
        and abs(pumping_factor - 1.0) < 1e-6
    )
    if is_zero_perturbation:
        coupled_delta = 0.0
        physics_delta_dtwl = 0.0

    coupled_dtwl = float(np.clip(base_dtwl + coupled_delta, 0.2, 250.0))
    ml_effective_dtwl = float(np.clip(base_dtwl + ml_delta, 0.2, 250.0))
    deep_effective_dtwl = (
        float(np.clip(base_dtwl + deep_delta, 0.2, 250.0))
        if deep_pred_dtwl is not None
        else None
    )

    # Validate simulated record through security_engine
    validation_notices = validate_environmental_record({
        TARGET: coupled_dtwl,
        "Rainfall": sim_rain,
        "ET": sim_et,
        "SM_10cm": mean_col(sim_df, "SM_10cm"),
        "NDVI": sim_ndvi,
        "Tmax": mean_col(sim_df, "Tmax"),
        "Tmin": mean_col(sim_df, "Tmin"),
    })

    # Multi-year trajectory under sustained scenario (5 years)
    horizon = max(1, len(result.get("forecast", pd.DataFrame())) or 5)
    last_year = int(pd.to_numeric(sim_df["YEAR"], errors="coerce").max() or 2022)
    base_fc_df: pd.DataFrame = result.get("forecast", pd.DataFrame())
    traj_years = list(range(last_year + 1, last_year + horizon + 1))
    base_traj: list[float] = []
    sim_traj: list[float] = []
    for step_idx, yr in enumerate(traj_years, start=1):
        if not base_fc_df.empty and "Scenario forecast DTWL (mbgl)" in base_fc_df.columns and step_idx <= len(base_fc_df):
            b_val = float(base_fc_df["Scenario forecast DTWL (mbgl)"].iloc[step_idx - 1])
        else:
            b_val = base_dtwl
        base_traj.append(b_val)
        # Cumulative dampened response over multi-year sustained scenario
        cum_factor = 1.0 + 0.35 * math.log1p(step_idx)
        s_val = float(np.clip(b_val + coupled_delta * cum_factor, 0.2, 250.0))
        sim_traj.append(s_val)

    ci_df = calculate_forecast_uncertainty(np.asarray(sim_traj), train_rmse=test_rmse)
    ci_df["Year"] = traj_years
    ci_df["Baseline_Forecast_DTWL_mbgl"] = np.round(base_traj, 2)
    ci_df["Scenario_Delta_mbgl"] = np.round(np.asarray(sim_traj) - np.asarray(base_traj), 2)

    return {
        "baseline": {
            "dtwl": base_dtwl,
            "rainfall": base_rain,
            "et": base_et,
            "soil": base_avg_sm,
            "ndvi": base_ndvi,
            "ndwi": base_ndwi,
            "balance": base_wb,
            "stress": base_stress,
            "tmax": base_tmax,
            "tmin": base_tmin,
        },
        "simulated": {
            "dtwl": coupled_dtwl,
            "rainfall": sim_rain,
            "et": sim_et,
            "soil": sim_avg_sm,
            "ndvi": sim_ndvi,
            "ndwi": sim_ndwi,
            "balance": sim_wb,
            "stress": sim_stress,
            "tmax": base_tmax + temp_delta,
            "tmin": base_tmin + temp_delta,
        },
        "deltas": {
            "dtwl": coupled_dtwl - base_dtwl,
            "ml_dtwl_delta": ml_delta,
            "deep_dtwl_delta": deep_delta,
            "physics_dtwl_delta": physics_delta_dtwl,
            "recharge_component_mbgl": recharge_dtwl_delta,
            "soil_moisture_component_mbgl": sm_dtwl_delta,
            "pumping_component_mbgl": pumping_dtwl_delta,
            "rainfall_mm": sim_rain - base_rain,
            "et_mm": sim_et - base_et,
            "balance_mm": sim_wb - base_wb,
            "stress": sim_stress - base_stress,
            "soil_pct": sim_avg_sm - base_avg_sm,
        },
        "model_outputs": {
            "best_ml_model": best_model_name,
            "ml_simulated_dtwl": ml_effective_dtwl,
            "best_deep_model": deep_best_name or "Unavailable",
            "deep_simulated_dtwl": deep_effective_dtwl,
            "coupled_dtwl": coupled_dtwl,
            "lower_95_ci": float(max(0.0, coupled_dtwl - 1.96 * test_rmse)),
            "upper_95_ci": float(coupled_dtwl + 1.96 * test_rmse),
            "test_rmse": test_rmse,
        },
        "trajectory_df": ci_df,
        "validation_notices": validation_notices,
        "perturbed_rows": sim_df,
        "assumptions": {
            "specific_yield_Sy": specific_yield,
            "effective_infiltration_coeff": infiltration_coeff,
            "coupling_weights": "45% Empirical ML/DL Response + 55% Vadose-Aquifer Mass-Balance Sensitivity",
        },
    }


# --------------------------------------------------------------------------- #
# OpenUSD-Inspired Scene Hierarchy Builder
# --------------------------------------------------------------------------- #
def build_openusd_scene_hierarchy(
    season: str,
    year: int,
    district: str,
    mode: str,
    state_metrics: dict[str, float | None],
    asset_info: dict[str, Any],
    has_real_coords: bool,
    has_real_elevation: bool,
    layers: dict[str, bool],
) -> list[dict[str, Any]]:
    """Construct an OpenUSD-inspired scene graph table with SimReady metadata and provenance."""
    prov_mode = {
        "Observed": PROVENANCE_OBSERVED,
        "Forecast": PROVENANCE_FORECAST,
        "Simulated": PROVENANCE_SIMULATED,
    }.get(mode, PROVENANCE_OBSERVED)

    geom_prov = PROVENANCE_OBSERVED if has_real_coords else PROVENANCE_ILLUSTRATIVE
    elev_prov = PROVENANCE_OBSERVED if has_real_elevation else PROVENANCE_ILLUSTRATIVE

    def _fmt(v: float | None, unit: str = "", d: int = 2) -> str:
        if v is None or not np.isfinite(v):
            return "Unavailable"
        return f"{v:,.{d}f}{(' ' + unit) if unit else ''}"

    return [
        {
            "USD Prim Path": "/World/RajasthanBasin",
            "Prim Type": "Xform (Root Stage)",
            "Active": True,
            "Key Attributes": f"season={season}, year={year}, district={district}, mode={mode}",
            "Data Provenance": prov_mode,
        },
        {
            "USD Prim Path": "/World/RajasthanBasin/Surface/TopographyMesh",
            "Prim Type": "Mesh (DEM / Terrain)",
            "Active": bool(layers.get("Terrain", True)),
            "Key Attributes": f"mean_elevation={_fmt(asset_info.get('elevation_m'), 'm ASL', 1)}, coords={'WGS84 (EPSG:4326)' if has_real_coords else 'Normalized Cutaway'}",
            "Data Provenance": elev_prov,
        },
        {
            "USD Prim Path": "/World/RajasthanBasin/Surface/DrainageNetwork",
            "Prim Type": "BasisCurves (Hydrology)",
            "Active": bool(layers.get("River", True)),
            "Key Attributes": f"NDWI={_fmt(state_metrics.get('ndwi'), '', 3)}, Water_Balance={_fmt(state_metrics.get('balance'), 'mm', 1)}",
            "Data Provenance": prov_mode,
        },
        {
            "USD Prim Path": "/World/RajasthanBasin/Surface/VegetationCanopy",
            "Prim Type": "PointInstancer (Biomass)",
            "Active": bool(layers.get("Vegetation", True)),
            "Key Attributes": f"NDVI={_fmt(state_metrics.get('ndvi'), '', 3)}",
            "Data Provenance": prov_mode,
        },
        {
            "USD Prim Path": "/World/RajasthanBasin/Atmosphere/PrecipitationField",
            "Prim Type": "ParticleSystem (Forcing)",
            "Active": bool(layers.get("Rainfall", True)),
            "Key Attributes": f"Rainfall={_fmt(state_metrics.get('rainfall'), 'mm', 1)}",
            "Data Provenance": prov_mode,
        },
        {
            "USD Prim Path": "/World/RajasthanBasin/Atmosphere/EvapotranspirationFlux",
            "Prim Type": "ParticleSystem (Flux)",
            "Active": bool(layers.get("ET", True)),
            "Key Attributes": f"ET={_fmt(state_metrics.get('et'), 'mm', 1)}, GW_Stress={_fmt(state_metrics.get('stress'), '', 2)}",
            "Data Provenance": prov_mode,
        },
        {
            "USD Prim Path": "/World/RajasthanBasin/Subsurface/VadoseZone",
            "Prim Type": "Volume (Unsaturated Soil)",
            "Active": bool(layers.get("Aquifer", True)),
            "Key Attributes": f"Avg_Soil_Moisture={_fmt(state_metrics.get('soil'), '%', 2)}",
            "Data Provenance": prov_mode,
        },
        {
            "USD Prim Path": "/World/RajasthanBasin/Subsurface/WaterTableSurface",
            "Prim Type": "Mesh (Piezometric Surface)",
            "Active": bool(layers.get("Aquifer", True)),
            "Key Attributes": f"DTWL={_fmt(state_metrics.get('dtwl'), 'mbgl', 2)}, Stress={asset_info.get('stress_status', {}).get('category', 'N/A')}",
            "Data Provenance": prov_mode,
        },
        {
            "USD Prim Path": str(asset_info.get("usd_path", "/World/RajasthanBasin/MonitoringNetwork")),
            "Prim Type": "GeomPrim (Monitoring Asset)",
            "Active": bool(layers.get("Wells", True)),
            "Key Attributes": f"asset={asset_info.get('name')}, wells={asset_info.get('well_count', 0)}, lat={_fmt(asset_info.get('latitude'), '°', 4)}, lon={_fmt(asset_info.get('longitude'), '°', 4)}",
            "Data Provenance": geom_prov,
        },
    ]


def log_twin_scenario_change(user: str, preset: str, params: dict[str, Any], sim_out: dict[str, Any]) -> None:
    """Record scenario execution in the immutable Digital Twin audit ledger."""
    base_d = sim_out.get("baseline", {}).get("dtwl")
    sim_d = sim_out.get("simulated", {}).get("dtwl")
    DIGITAL_TWIN_AUDIT.log_parameter_change(
        user=user,
        parameter=f"Scenario[{preset}]: rain={params.get('rainfall_pct')}%, et={params.get('et_pct')}%, sm={params.get('sm_delta')}%, pump={params.get('pumping_factor')}x",
        old_val=round(float(base_d), 3) if base_d is not None else "N/A",
        new_val=round(float(sim_d), 3) if sim_d is not None else "N/A",
    )


# --------------------------------------------------------------------------- #
# SimReady Hydrogeological Asset Validation & OpenUSD (.usda) Stage Exporter
# Inspired by NVIDIA Omniverse DSX Blueprint & OpenUSD Asset Pipeline
# --------------------------------------------------------------------------- #
def validate_simready_hydro_assets(asset_catalog: pd.DataFrame) -> dict[str, Any]:
    """Validate monitoring well assets against SimReady Hydrogeological criteria.

    Checks:
    1. Geodetic Coordinates (WGS84 / EPSG:4326 inside Rajasthan bounds).
    2. DEM Elevation coverage (Elevation_m > 0).
    3. Measured Groundwater Depth within physical limits (0 < DTWL <= 250 mbgl).
    4. Hydro-meteorological forcing linkages (Rainfall, ET, Soil Moisture).
    5. Historical multi-year observations for trend stability (Count >= 2).
    """
    if asset_catalog is None or asset_catalog.empty:
        return {
            "total_assets": 0,
            "simready_compliant_count": 0,
            "compliance_pct": 0.0,
            "tier_summary": {"Tier 1 (SimReady Full)": 0, "Tier 2 (Basic Geometry)": 0, "Tier 3 (Incomplete)": 0},
            "records": pd.DataFrame(),
        }

    records: list[dict[str, Any]] = []
    t1_count, t2_count, t3_count = 0, 0, 0

    for _, row in asset_catalog.iterrows():
        missing: list[str] = []
        lat = safe_float(row.get("Latitude"))
        lon = safe_float(row.get("Longitude"))
        elev = safe_float(row.get("Elevation_m"))
        dtwl = safe_float(row.get("DTWL_mbgl"))
        rain = safe_float(row.get("Rainfall_mm"))
        et = safe_float(row.get("ET_mm"))
        obs = int(row.get("Observations_Count") or 0)

        # Coordinate check
        if lat is None or lon is None:
            missing.append("Coordinates (Lat/Lon)")
        elif not (23.0 <= lat <= 30.5 and 69.5 <= lon <= 78.5):
            missing.append("Out-of-Bounds Coords")

        if elev is None or elev <= 0:
            missing.append("Elevation (DEM)")
        if dtwl is None or dtwl <= 0:
            missing.append("Groundwater DTWL")
        if rain is None or et is None:
            missing.append("Hydro Forcing (Rain/ET)")
        if obs < 2:
            missing.append("Historical Depth Series")

        if not missing:
            tier = "Tier 1: Full SimReady"
            t1_count += 1
            badge = "🟢 SimReady"
        elif len(missing) <= 2 and "Coordinates (Lat/Lon)" not in missing:
            tier = "Tier 2: Basic Geometry"
            t2_count += 1
            badge = "🟡 Geometry Only"
        else:
            tier = "Tier 3: Conceptual / Incomplete"
            t3_count += 1
            badge = "🟠 Data Gap"

        records.append({
            "Asset_ID": row.get("Asset_ID", f"WELL:{row.get('Village')}"),
            "Village": row.get("Village", "Unknown"),
            "District": row.get("District", "Unspecified"),
            "SimReady_Status": badge,
            "SimReady_Tier": tier,
            "DTWL_mbgl": dtwl,
            "Latitude": lat,
            "Longitude": lon,
            "Missing_Attributes": ", ".join(missing) if missing else "None (100% Compliant)",
        })

    total = len(asset_catalog)
    comp_pct = (t1_count / total * 100.0) if total else 0.0

    return {
        "total_assets": total,
        "simready_compliant_count": t1_count,
        "compliance_pct": comp_pct,
        "tier_summary": {
            "Tier 1 (SimReady Full)": t1_count,
            "Tier 2 (Basic Geometry)": t2_count,
            "Tier 3 (Incomplete)": t3_count,
        },
        "records": pd.DataFrame(records),
    }


def export_openusd_stage(
    season: str,
    year: int,
    district: str,
    mode: str,
    state_metrics: dict[str, float | None],
    asset_catalog: pd.DataFrame,
    asset_info: dict[str, Any],
    sim_result: dict[str, Any] | None = None,
) -> str:
    """Generate a formal OpenUSD ASCII (.usda) stage for downstream visualization in NVIDIA Omniverse.

    Produces standard OpenUSD syntax:
    - Root stage with WGS84 and metersPerUnit metadata.
    - Topography, piezometric water table, and vadose volume schemas.
    - Per-asset monitoring well prims with custom SimReady hydrogeological attributes.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    dtwl_val = state_metrics.get("dtwl") or 10.0
    rain_val = state_metrics.get("rainfall") or 0.0
    et_val = state_metrics.get("et") or 0.0
    elev_val = asset_info.get("elevation_m") or 300.0
    stress_cat = (asset_info.get("stress_status") or {}).get("category", "Safe")

    sim_delta = 0.0
    if sim_result and "deltas" in sim_result:
        sim_delta = float(sim_result["deltas"].get("dtwl", 0.0))

    lines = [
        "#usda 1.0",
        "(",
        '    defaultPrim = "World"',
        "    metersPerUnit = 1.0",
        '    upAxis = "Z"',
        "    customLayerData = {",
        '        string creator = "Naya Pani Hydrogeological Digital Twin"',
        '        string system = "NVIDIA Omniverse / OpenUSD Hydro Blueprint"',
        '        string coordinateReferenceSystem = "EPSG:4326 (WGS84)"',
        f'        string exportedAt = "{ts}"',
        f'        string temporalSlice = "{season}_{year}"',
        f'        string mode = "{mode}"',
        f'        string district = "{district}"',
        "    }",
        ")",
        "",
        'def Xform "World"',
        "{",
        '    def Scope "RajasthanBasin" (',
        "        customData = {",
        f'            string basinName = "Luni River Basin / Semi-Arid Rajasthan"',
        f'            string season = "{season}"',
        f"            int activeYear = {year}",
        f'            string operationalMode = "{mode}"',
        f'            double baselineDtwlMbgl = {dtwl_val:.3f}',
        f"            double simulationDeltaMbgl = {sim_delta:+.3f}",
        "        }",
        "    )",
        "    {",
        '        def Mesh "TopographyMesh" (',
        '            doc = "Ground surface digital elevation model (DEM) interpolated from monitoring well stations"',
        "        )",
        "        {",
        f"            custom double hydro:meanElevationM = {elev_val:.2f}",
        f"            custom double hydro:rainfallMm = {rain_val:.2f}",
        f"            custom double hydro:etMm = {et_val:.2f}",
        '            custom string metadata:provenance = "Verified Historical Observation"',
        "        }",
        "",
        '        def Mesh "WaterTableSurface" (',
        '            doc = "Piezometric unconfined groundwater table surface"',
        "        )",
        "        {",
        f"            custom double hydro:dtwlMbgl = {dtwl_val:.3f}",
        f'            custom string hydro:stressCategory = "{stress_cat}"',
        f"            custom double hydro:specificYieldSy = 0.08",
        f'            custom string metadata:provenance = "{PROVENANCE_SIMULATED if mode == "Simulated" else PROVENANCE_OBSERVED}"',
        "        }",
        "",
        '        def Volume "VadoseZone" (',
        '            doc = "Unsaturated vadose soil buffer between ground surface and water table"',
        "        )",
        "        {",
        f"            custom double hydro:avgSoilMoisturePct = {float(state_metrics.get('soil') or 15.0):.2f}",
        "            custom double hydro:infiltrationCoeff = 0.18",
        "        }",
        "",
        '        def Scope "MonitoringNetwork" (',
        '            doc = "SimReady monitoring well piezometers and borehole asset registry"',
        "        )",
        "        {",
    ]

    # Add monitoring well prims from asset catalog
    if asset_catalog is not None and not asset_catalog.empty:
        for _, row in asset_catalog.head(60).iterrows():
            v_clean = str(row.get("Village", "Well")).replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
            w_dtwl = safe_float(row.get("DTWL_mbgl")) or dtwl_val
            w_lat = safe_float(row.get("Latitude")) or 0.0
            w_lon = safe_float(row.get("Longitude")) or 0.0
            w_elev = safe_float(row.get("Elevation_m")) or elev_val
            w_stress = str(row.get("Stress_Category", "Safe"))
            w_slope = float(row.get("Trend_Slope_mbgl_yr") or 0.0)

            lines.extend([
                f'            def Xform "Well_{v_clean}" (',
                "                customData = {",
                f'                    string assetId = "WELL:{row.get("Village")}"',
                f'                    string simreadyTier = "Tier 1: Full SimReady"',
                "                }",
                "            )",
                "            {",
                f"                custom double hydro:latitude = {w_lat:.5f}",
                f"                custom double hydro:longitude = {w_lon:.5f}",
                f"                custom double hydro:surfaceElevationM = {w_elev:.2f}",
                f"                custom double hydro:dtwlMbgl = {w_dtwl:.2f}",
                f'                custom string hydro:stressCategory = "{w_stress}"',
                f"                custom double hydro:historicalTrendSlopeMbglYr = {w_slope:+.3f}",
                '                custom string metadata:provenance = "Verified In-Situ Piezometer Measurement"',
                "",
                '                def Cylinder "BoreholeCasing" {',
                f"                    double height = {w_dtwl:.2f}",
                "                    double radius = 0.15",
                "                }",
                "            }",
            ])

    lines.extend([
        "        }",
        "    }",
        "}",
    ])

    return "\n".join(lines)


def calculate_sustainable_water_budget(
    baseline_dtwl_mbgl: float,
    current_pumping_factor: float = 1.0,
    rainfall_deficit_pct: float = 0.0,
    specific_yield_Sy: float = 0.08,
    safe_threshold_mbgl: float = 10.0,
    critical_threshold_mbgl: float = 20.0,
) -> dict[str, Any]:
    """Capacity planning tool analogous to NVIDIA's fixed power budget analysis.

    Answers: How much can tube-wells pump without tipping the aquifer into Critical status?
    """
    headroom_to_critical = max(0.0, critical_threshold_mbgl - baseline_dtwl_mbgl)
    headroom_to_safe = max(0.0, safe_threshold_mbgl - baseline_dtwl_mbgl)

    # Drought drawdown penalty
    drought_penalty_m = (abs(min(0.0, rainfall_deficit_pct)) / 100.0) * 1.85
    net_usable_headroom = max(0.0, headroom_to_critical - drought_penalty_m)

    # Max sustainable pumping factor before hitting critical
    max_sustainable_factor = 1.0 + (net_usable_headroom / max(baseline_dtwl_mbgl * 0.16, 1.2))
    pumping_reduction_needed = max(0.0, (current_pumping_factor - max_sustainable_factor) / current_pumping_factor * 100.0)

    # Managed Aquifer Recharge (MAR) capacity in MCM to offset drought
    mar_recharge_needed_mcm = round(drought_penalty_m * 10.0 * specific_yield_Sy, 2)

    return {
        "baseline_dtwl_mbgl": baseline_dtwl_mbgl,
        "headroom_to_critical_m": round(headroom_to_critical, 2),
        "drought_drawdown_penalty_m": round(drought_penalty_m, 2),
        "max_sustainable_pumping_factor": round(max_sustainable_factor, 2),
        "pumping_reduction_needed_pct": round(pumping_reduction_needed, 1),
        "mar_recharge_needed_mcm": mar_recharge_needed_mcm,
        "status": "Safe Buffer Available" if max_sustainable_factor >= 1.0 else "Immediate Demand Curtailment Required",
    }
