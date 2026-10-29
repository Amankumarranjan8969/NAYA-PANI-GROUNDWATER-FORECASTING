"""rag/assistant.py — grounded, conversational assistant for the Naya Pani Digital Twin & ML dashboard.

Two answer paths:
  1. Small talk → instant canned reply (rag.smalltalk), no retrieval, no LLM.
  2. Everything else → structured Digital Twin / pipeline telemetry + KB retrieval
     + (LLM if a key is set, otherwise deterministic offline composer).

Default LLM: Gemini (GEMINI_API_KEY). Falls back to Anthropic if configured,
or to a deterministic composer that mixes live numbers with knowledge-base background.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any
import pandas as pd

from .context import build_job_context
from .llm_provider import active_provider, complete
from .retriever import KnowledgeBase
from .smalltalk import reply_for as smalltalk_reply

try:
    from security_engine import sanitize_rag_prompt, sanitize_rag_response
except Exception:
    def sanitize_rag_prompt(prompt: str) -> tuple[str, list[Any]]:
        return (prompt or "").strip(), []

    def sanitize_rag_response(text: str) -> str:
        return (text or "").strip()


# --------------------------------------------------------------------------- #
# System prompt for the LLM path
# --------------------------------------------------------------------------- #
_SYSTEM_PROMPT = """You are the AI Hydrogeological Assistant embedded in the Naya Pani
Seasonal Groundwater & Digital Twin platform for semi-arid Rajasthan. The user is
inspecting a seasonal ML/DL groundwater analysis and an interactive 3D Hydrogeological
Digital Twin. Talk like a clear, friendly, knowledgeable colleague who makes complex
groundwater science easy for ANYONE (including farmers, students, local planners, and
researchers) to understand at a glance.

HOW TO ANSWER
- Always start with a **Plain-English Summary** in simple, everyday language before
  giving technical numbers.
- Whenever you mention groundwater depth (`DTWL` in `mbgl`), explain what it means in
  plain words: **meters below ground level** (how deep you must dig or pump from the
  surface to reach water; a **smaller number** = water is closer to the surface and
  plentiful, while a **larger number** = water has dropped deeper underground).
- When explaining forecasts or simulations, clearly state whether the underground water
  level is **rising closer to the surface (recovery/recharge)**, **staying steady**, or
  **dropping deeper underground (depletion/stress)**, and by how many meters.
- Quote exact values, units (`mbgl` / meters deep), model names, and seasons from CONTEXT.
- Explicitly distinguish between:
  1. Verified Historical Observation (workbook DTWL measurements),
  2. Model-Generated Forecast (ML/DL seasonal projections), and
  3. Coupled Simulation Output (Digital Twin what-if scenario perturbations).
- If the question is conceptual (e.g. "what is KGE", "how does the coupled simulation
  work"), give a one-sentence plain-English analogy first, then 1-3 short points.

STYLE
- Write in clear, natural, human-friendly sentences rather than raw data dumps.
- Use markdown purposefully: **bold** for key takeaways, metric names, or model names.
- Never invent numbers, coordinates, model names, or seasons.
"""


_OPENERS = [
    "Quick answer:",
    "Short answer:",
    "From this run:",
    "This session shows:",
]

_NO_ANSWER = (
    "I don't have verified data on that specific query in the current session. "
    "I can help with: a metric like R² or KGE, which ML or Deep Learning model won a season, "
    "the active Digital Twin scenario and selected monitoring well, what-if recharge/drought "
    "simulations, LOFO feature drivers, or a summary of the uploaded Rajasthan workbook."
)

_SHORT_CONFIRMATIONS = {
    "yes", "yeah", "yep", "yup", "sure", "ok", "okay",
    "go on", "please do", "tell me more", "more", "continue",
}


# --------------------------------------------------------------------------- #
# Lazy knowledge-base singleton
# --------------------------------------------------------------------------- #
_KB = None


def _kb() -> KnowledgeBase:
    global _KB
    if _KB is None:
        _KB = KnowledgeBase()
    return _KB


def _resolve_twin_state(twin_state: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return explicit twin_state or inspect st.session_state['digital_twin_state'] if available."""
    if twin_state is not None:
        return twin_state
    try:
        import streamlit as st
        state = st.session_state.get("digital_twin_state")
        if isinstance(state, dict) and state:
            return state
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------- #
# Small utilities
# --------------------------------------------------------------------------- #
def _pick(options: list[str], seed_text: str) -> str:
    """Stable-but-not-fixed choice: same question → same phrasing."""
    h = int(hashlib.md5(seed_text.encode()).hexdigest(), 16)
    return options[h % len(options)]


def _format_history(history: list[dict] | None, max_turns: int = 4) -> str:
    """Return the last N turns as a compact transcript for the LLM."""
    if not history:
        return ""
    recent = history[-max_turns * 2:]
    lines = []
    for turn in recent:
        role = "User" if turn.get("role") == "user" else "Assistant"
        content = str(turn.get("content", "")).strip().replace("\n", " ")
        if len(content) > 240:
            content = content[:240].rsplit(" ", 1)[0] + "…"
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    """Remove duplicate sources while keeping their first occurrence."""
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        name = (item or "").strip()
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        output.append(name)
    return output


def _last_user_question(history: list[dict] | None) -> str | None:
    """Grab the most recent user message for follow-up resolution."""
    if not history:
        return None
    for turn in reversed(history):
        if turn.get("role") == "user":
            text = str(turn.get("content", "")).strip()
            if text:
                return text
    return None


def _with_followup_context(question: str, history: list[dict] | None) -> str:
    """Expand obvious follow-up questions using the previous user turn."""
    text = question.strip()
    if not text or not history:
        return text
    lowered = text.lower()
    if not any(lowered.startswith(prefix) for prefix in (
        "and ", "also ", "what about ", "how about ", "then ", "what about the ", "how about the "
    )):
        return text
    prior = _last_user_question(history)
    if not prior:
        return text
    return f"{prior} {text}"


# --------------------------------------------------------------------------- #
# Detection helpers
# --------------------------------------------------------------------------- #
_METRIC_ALIASES = {
    "r²": "Bias-corrected test R2",
    "r2": "Bias-corrected test R2",
    "rmse": "Bias-corrected test RMSE",
    "mae": "Bias-corrected test MAE",
    "kge": "Bias-corrected test KGE",
    "nse": "Bias-corrected test NSE",
    "bias": "Bias-corrected test Bias",
    "pearson": "Bias-corrected test Pearson r",
}

_SEASON_ALIASES = {
    "premonsoon": "Pre-Monsoon",
    "monsoon": "Monsoon",
    "rainy": "Monsoon",
    "postmonsoon": "Post-Monsoon",
    "nonmonsoon": "Non-Monsoon",
    "dry": "Non-Monsoon",
    "winter": "Non-Monsoon",
}


def _detect_season(question_lower: str, seasons: list[str]) -> str | None:
    """Return the season named in the question (longest-first match)."""
    q_compact = question_lower.replace("-", "").replace(" ", "").replace("_", "")

    ranked = sorted(
        seasons,
        key=lambda s: len(s.replace("-", "").replace(" ", "").replace("_", "")),
        reverse=True,
    )
    for season in ranked:
        s_compact = season.lower().replace("-", "").replace(" ", "").replace("_", "")
        if s_compact in q_compact:
            return season

    for token, canonical in _SEASON_ALIASES.items():
        if token in q_compact and canonical in seasons:
            return canonical
    return None


def _detect_metric(question_lower: str) -> tuple[str, str] | None:
    """Return (alias, column_name) for the first metric named, else None."""
    q_clean = question_lower
    for conceptual in ("bias correction", "bias corrected", "bias-corrected"):
        q_clean = q_clean.replace(conceptual, "")
    for alias, column in _METRIC_ALIASES.items():
        if alias in q_clean:
            return alias, column
    return None


def _detect_model(question_lower: str, model_names: list[str]) -> str | None:
    """Return the model named in the question, if any."""
    q_norm = question_lower.replace("_", " ")
    for name in model_names:
        n_lower = name.lower().strip()
        if len(n_lower) < 4:
            continue
        if n_lower in q_norm:
            return name
    return None


_DEEP_MODEL_ALIASES = {
    "physics-informed neural network": "PINN (Physics-Informed NN)",
    "physics informed neural network": "PINN (Physics-Informed NN)",
    "physics-informed": "PINN (Physics-Informed NN)",
    "physics informed": "PINN (Physics-Informed NN)",
    "pinn": "PINN (Physics-Informed NN)",
    "reservoir computing": "Reservoir Computing (ESN)",
    "echo state network": "Reservoir Computing (ESN)",
    "echo state": "Reservoir Computing (ESN)",
    "reservoir": "Reservoir Computing (ESN)",
    "esn": "Reservoir Computing (ESN)",
    "sarimax": "SARIMA (SARIMAX)",
    "sarima": "SARIMA (SARIMAX)",
    "lstm": "LSTM (Deep Learning)",
}
_DEEP_FAMILY_KEYWORDS = ["deep learning", "deep-learning"] + list(_DEEP_MODEL_ALIASES)


def _detect_deep_model(question_lower: str) -> str | None:
    """Return the canonical deep-learning-tab model named in the question, if any."""
    q_norm = question_lower.replace("_", " ")
    for alias in sorted(_DEEP_MODEL_ALIASES, key=len, reverse=True):
        if alias in q_norm:
            return _DEEP_MODEL_ALIASES[alias]
    return None


def _mentions_deep_family(question_lower: str) -> bool:
    q_norm = question_lower.replace("_", " ")
    return any(keyword in q_norm for keyword in _DEEP_FAMILY_KEYWORDS)


# --------------------------------------------------------------------------- #
# Plain-English NLP Synthesis Helpers (Human-Readable Groundwater Interpretation)
# --------------------------------------------------------------------------- #
_SEASON_PLAIN_ROLE = {
    "Pre-Monsoon": "Hot Dry Summer Before the Rains (March–May)",
    "Monsoon": "Rainy Recharge Season (June–September)",
    "Post-Monsoon": "Post-Rain Aquifer Storage Season (October–December)",
    "Non-Monsoon": "Dry Winter Irrigation Season (January–February)",
}


def _plain_depth_status(dtwl_mbgl: float) -> str:
    """Translate a DTWL (mbgl) number into an everyday water-availability description."""
    if dtwl_mbgl <= 5.0:
        return "very shallow & healthy — water is close to the ground surface and easy to pump"
    if dtwl_mbgl <= 10.0:
        return "safe & moderate depth — healthy underground water storage"
    if dtwl_mbgl <= 20.0:
        return "semi-critical depth — moderate drawdown; deeper borewells required"
    if dtwl_mbgl <= 35.0:
        return "critical depth — significant groundwater depletion"
    return "over-exploited deep water table — severe groundwater stress"


def _plain_r2_phrase(r2: float) -> str:
    """Translate R² into plain-English accuracy terms."""
    if r2 >= 0.75:
        return "high accuracy"
    if r2 >= 0.45:
        return "moderate accuracy"
    if r2 >= 0.0:
        return "modest accuracy"
    return "noisy/hard-to-predict season"


def _synthesize_forecast_story(
    season: str,
    model_name: str,
    fc_df: pd.DataFrame,
    year_col: str,
    val_col: str,
    family_label: str = "Model-Generated Forecast",
) -> str:
    """Turn a raw forecast table into a clear, human-friendly NLP explanation + exact figures."""
    years = [int(r[year_col]) for _, r in fc_df.iterrows()]
    vals = [float(r[val_col]) for _, r in fc_df.iterrows()]
    start_y, end_y = years[0], years[-1]
    start_v, end_v = vals[0], vals[-1]
    delta = end_v - start_v
    season_desc = _SEASON_PLAIN_ROLE.get(season, season)
    status_desc = _plain_depth_status(end_v)

    if delta > 0.20:
        trend_sentence = (
            f"Water is projected to **drop {delta:.2f} meters deeper underground** "
            f"(from **{start_v:.2f} m** in {start_y} down to **{end_v:.2f} m** in {end_y}), "
            f"which warns of **gradual groundwater depletion**."
        )
    elif delta < -0.20:
        trend_sentence = (
            f"Water is projected to **rise {abs(delta):.2f} meters closer to the surface** "
            f"(from **{start_v:.2f} m** in {start_y} up to **{end_v:.2f} m** in {end_y}), "
            f"showing **groundwater recovery/recharge**."
        )
    else:
        trend_sentence = (
            f"Water depth is expected to **stay steady around {end_v:.2f} meters below the ground** "
            f"from {start_y} through {end_y} ({status_desc})."
        )

    year_by_year = "; ".join(f"in {y}: {v:.2f} mbgl" for y, v in zip(years, vals))
    return (
        f"**[{family_label}] {season}** — *{season_desc}* (`{model_name}`):\n"
        f"  • **Plain-English Meaning:** {trend_sentence}\n"
        f"  • **Year-by-Year Depth:** {year_by_year}"
    )


# --------------------------------------------------------------------------- #
# Live-number & Digital Twin telemetry extraction
# --------------------------------------------------------------------------- #
def _extract_live_numbers(
    question: str,
    payload: dict | None,
    twin_state: dict[str, Any] | None = None,
) -> list[str]:
    """Return a list of verified live facts from the pipeline payload and Digital Twin state."""
    if not payload and not twin_state:
        return []
    results = (payload or {}).get("results") or {}
    q = question.lower()
    seasons = list(results.keys())
    facts: list[str] = []

    detected_season = _detect_season(q, seasons) if seasons else None
    detected_metric = _detect_metric(q)

    # ---- Priority Case 0: Digital Twin / Selected Asset / Coupled What-If Simulation ----
    twin_keywords = [
        "digital twin", "twin", "what-if", "what if", "coupled", "simulation", "simulated",
        "scenario", "drought", "recharge", "cloudburst", "pumping", "extraction", "check-dam",
        "check dam", "mar", "selected asset", "selected well", "selected village", "borehole",
        "water stress", "stress status", "openusd", "prim", "scene hierarchy", "alert", "alerts",
    ]
    asset_info = (twin_state or {}).get("asset_info") or (twin_state or {}).get("selected_asset_info") or {}
    selected_village = str(
        (twin_state or {}).get("selected_asset")
        or (twin_state or {}).get("selected_village")
        or asset_info.get("village")
        or asset_info.get("name")
        or ""
    )
    mentions_selected_village = (
        len(selected_village) >= 3
        and "all villages" not in selected_village.lower()
        and "all monitoring" not in selected_village.lower()
        and selected_village.lower() in q
    )

    if twin_state and (any(kw in q for kw in twin_keywords) or mentions_selected_village):
        t_season = twin_state.get("season") or detected_season or (seasons[0] if seasons else "Active Season")
        t_mode = twin_state.get("mode", "Observed")
        t_year = twin_state.get("year") or twin_state.get("selected_year", "Latest")
        t_preset = twin_state.get("scenario_preset", "Baseline (Zero Perturbation)")
        sim = twin_state.get("simulation_summary") or twin_state.get("simulation") or {}
        params = twin_state.get("scenario_params") or {}
        v_name = asset_info.get("name") or asset_info.get("village", "All Villages (Basin Aggregate)")

        if isinstance(sim, dict) and ("model_outputs" in sim or "coupled_dtwl_mbgl" in sim):
            m_out = sim.get("model_outputs") or {}
            deltas = sim.get("deltas") or {}
            base_dict = sim.get("baseline") or {}
            base_dtwl = float(base_dict.get("dtwl", sim.get("baseline_dtwl_mbgl", 0.0)) or 0.0)
            coupled_dtwl = float(m_out.get("coupled_dtwl", sim.get("coupled_dtwl_mbgl", 0.0)) or 0.0)
            delta_dtwl = float(deltas.get("dtwl", sim.get("delta_dtwl_mbgl", coupled_dtwl - base_dtwl)) or 0.0)
            if delta_dtwl > 0.05:
                plain_sim = (
                    f"**Plain-English Takeaway:** Under the **{t_preset}** scenario, underground water at **{v_name}** "
                    f"is projected to **drop {delta_dtwl:.2f} meters deeper below the ground** (from **{base_dtwl:.2f} m** down to **{coupled_dtwl:.2f} m** deep). "
                    f"*(In `mbgl` — meters below ground level — a larger number means water is farther down and harder to pump.)*"
                )
            elif delta_dtwl < -0.05:
                plain_sim = (
                    f"**Plain-English Takeaway:** Under the **{t_preset}** scenario, underground water at **{v_name}** "
                    f"is projected to **rise {abs(delta_dtwl):.2f} meters closer to the surface** (from **{base_dtwl:.2f} m** up to **{coupled_dtwl:.2f} m** deep), "
                    f"meaning **aquifer recovery and healthier water storage**."
                )
            else:
                plain_sim = (
                    f"**Plain-English Takeaway:** At **{v_name}**, underground water depth is **steady at {coupled_dtwl:.2f} meters below the ground** "
                    f"({_plain_depth_status(coupled_dtwl)})."
                )
            facts.append(plain_sim)

        facts.append(
            f"**Digital Twin State (`{t_season}` · `{t_mode}` · Year `{t_year}`)**: "
            f"Active scenario = **{t_preset}** "
            f"(Rainfall {float(params.get('rainfall_pct', 0.0)):+.0f}%, "
            f"ET {float(params.get('et_pct', 0.0)):+.0f}%, "
            f"Soil Moisture {float(params.get('sm_delta', params.get('sm_pct', 0.0))):+.1f}%, "
            f"ΔTemp {float(params.get('temp_delta_c', 0.0)):+.1f}°C, "
            f"Pumping {float(params.get('pumping_factor', 1.0)):.2f}x)."
        )

        if asset_info:
            usd_path = asset_info.get("usd_path", "/World/RajasthanBasin")
            d_name = asset_info.get("district", "N/A")
            b_name = asset_info.get("block", "N/A")
            mean_dtwl = float(asset_info.get("historical_mean_dtwl") or asset_info.get("mean_dtwl_mbgl") or 0.0)
            min_dtwl = float(asset_info.get("historical_min_dtwl") or asset_info.get("min_dtwl_mbgl") or 0.0)
            max_dtwl = float(asset_info.get("historical_max_dtwl") or asset_info.get("max_dtwl_mbgl") or 0.0)
            slope = float(asset_info.get("trend_slope_mbgl_yr") or asset_info.get("trend_slope_mbgl_per_yr") or 0.0)
            stress_dict = asset_info.get("stress_status") or {}
            stress = stress_dict.get("badge") or stress_dict.get("category") or asset_info.get("stress_label", "Unknown")
            coords_note = ""
            if asset_info.get("latitude") is not None and asset_info.get("longitude") is not None:
                coords_note = f" at ({float(asset_info['latitude']):.4f}°N, {float(asset_info['longitude']):.4f}°E)"
            facts.append(
                f"**[Verified Historical Observation] Asset `{v_name}`** (USD: `{usd_path}`, District: `{d_name}`, Block: `{b_name}`{coords_note}): "
                f"Historical Average Depth = **{mean_dtwl:.2f} mbgl** (Range: {min_dtwl:.2f}–{max_dtwl:.2f} m below ground), "
                f"Long-Term Trend = **{slope:+.3f} m/yr**, "
                f"Water Stress Status = **{stress}**."
            )

        if isinstance(sim, dict) and ("model_outputs" in sim or "coupled_dtwl_mbgl" in sim):
            m_out = sim.get("model_outputs") or {}
            deltas = sim.get("deltas") or {}
            base_dict = sim.get("baseline") or {}
            base_dtwl = float(base_dict.get("dtwl", sim.get("baseline_dtwl_mbgl", 0.0)) or 0.0)
            coupled_dtwl = float(m_out.get("coupled_dtwl", sim.get("coupled_dtwl_mbgl", 0.0)) or 0.0)
            delta_dtwl = float(deltas.get("dtwl", sim.get("delta_dtwl_mbgl", coupled_dtwl - base_dtwl)) or 0.0)
            ci_low = float(m_out.get("lower_95_ci", sim.get("ci_95_lower_mbgl", 0.0)) or 0.0)
            ci_high = float(m_out.get("upper_95_ci", sim.get("ci_95_upper_mbgl", 0.0)) or 0.0)
            ml_model = m_out.get("best_ml_model") or sim.get("best_ml_model", "ML")
            ml_sim = float(m_out.get("ml_simulated_dtwl", sim.get("ml_simulated_dtwl_mbgl", coupled_dtwl)) or 0.0)
            dl_model = m_out.get("best_deep_model") or sim.get("best_deep_model")
            dl_sim = m_out.get("deep_simulated_dtwl", sim.get("dl_simulated_dtwl_mbgl"))
            direction = (
                "water-table deepening / depletion"
                if delta_dtwl > 0.05
                else ("water-table rise / recharge recovery" if delta_dtwl < -0.05 else "near-equilibrium")
            )
            facts.append(
                f"**[Coupled Simulation Output]**: Baseline DTWL = **{base_dtwl:.2f} mbgl** → "
                f"Simulated DTWL = **{coupled_dtwl:.2f} mbgl** (Net ΔDTWL = **{delta_dtwl:+.2f} mbgl**, {direction}; "
                f"95% CI: **[{ci_low:.2f}, {ci_high:.2f}] mbgl**). "
                f"Component breakdown: ML (`{ml_model}`) = {ml_sim:.2f} mbgl"
                + (
                    f", Deep Learning (`{dl_model}`) = {float(dl_sim):.2f} mbgl"
                    if dl_sim is not None
                    else ""
                )
                + f", Vadose Mass-Balance Δ = {float(deltas.get('physics_dtwl_delta', 0.0)):+.2f} mbgl ($S_y=0.08$)."
            )

        alerts = asset_info.get("alerts") or []
        if alerts:
            alert_items = [
                f"[{a.get('severity')}] {a.get('title')}: {a.get('detail')}" if isinstance(a, dict) else str(a)
                for a in alerts[:3]
            ]
            facts.append(f"**Active Hydrological Alerts**: {'; '.join(alert_items)}")

        return facts[:6]

    if not results:
        return facts

    # Check if user asked about a specific village/district in the loaded dataset even without saying "twin"
    for season_key, res in results.items():
        clean_df = res.get("clean_data")
        if isinstance(clean_df, pd.DataFrame) and "VILLAGE" in clean_df.columns:
            villages = clean_df["VILLAGE"].dropna().astype(str).unique().tolist()
            matched_v = [
                v for v in villages
                if len(v) >= 3 and re.search(rf"\b{re.escape(v.lower())}\b", q)
            ]
            if matched_v:
                v_target = matched_v[0]
                v_rows = clean_df[clean_df["VILLAGE"].astype(str) == v_target]
                mean_val = float(v_rows["DTWL (mbgl)"].mean())
                min_val = float(v_rows["DTWL (mbgl)"].min())
                max_val = float(v_rows["DTWL (mbgl)"].max())
                dist_val = str(v_rows["DISTRICT"].iloc[0]) if "DISTRICT" in v_rows.columns else "N/A"
                block_val = str(v_rows["BLOCK"].iloc[0]) if "BLOCK" in v_rows.columns else "N/A"
                facts.append(
                    f"**[Verified Historical Observation] Village `{v_target}`** (`{season_key}`, District `{dist_val}`, Block `{block_val}`): "
                    f"Average underground water depth is **{mean_val:.2f} meters below ground (`mbgl`)** "
                    f"({_plain_depth_status(mean_val)}; shallowest recorded: **{min_val:.2f} m**, deepest recorded: **{max_val:.2f} m** across {len(v_rows)} seasonal records)."
                )
                if detected_season and season_key == detected_season:
                    break
    if facts:
        return facts[:4]

    # ---- Priority Case 0.5: LOFO Feature Importance / Hydrological Drivers ----
    driver_keywords = [
        "lofo", "feature importance", "top driver", "top drivers", "key driver", "key drivers",
        "most important feature", "which feature", "which predictor", "sensitivity",
    ]
    if any(kw in q for kw in driver_keywords):
        facts.append(
            "**Plain-English Meaning of Top Drivers (LOFO):** Leave-One-Feature-Out (LOFO) tests how much model accuracy drops when an environmental factor (like Rainfall, Soil Moisture, or Vegetation) is removed. **A larger drop means that factor is a critical real-world driver of your groundwater level.**"
        )
        seasons_to_check = [detected_season] if detected_season else list(results.keys())
        for season in seasons_to_check:
            lofo = results[season].get("lofo")
            if isinstance(lofo, pd.DataFrame) and not lofo.empty and "Feature" in lofo.columns:
                top_feats = []
                for _, r in lofo.head(4).iterrows():
                    drop = float(r.get("Correlation drop", r.get("R2 Drop", 0.0)) or 0.0)
                    top_feats.append(f"`{r['Feature']}` (impact Δr = {drop:+.4f})")
                facts.append(f"**{season} Top Hydrological Drivers (LOFO sensitivity)**: " + ", ".join(top_feats))
        if len(facts) > 1:
            return facts
        facts.clear()

    all_models: list[str] = []
    for res in results.values():
        for name in res["metrics"]["Model"].astype(str).tolist():
            if name not in all_models:
                all_models.append(name)
    detected_model = _detect_model(q, all_models)

    # ---- Priority Case 1: Forecast / Projection / Future Year queries ----
    forecast_keywords = [
        "forecast", "predict", "projection", "future", "scenario",
        "2023", "2024", "2025", "2026", "2027", "2028", "2029", "2030",
        "next year", "upcoming", "trend", "expected dtwl", "water level in",
    ]
    if any(kw in q for kw in forecast_keywords):
        facts.append(
            "**What We Are Forecasting (In Simple Words):**\n"
            "We are predicting **how deep underground the water table will be** over the coming years, measured in **`mbgl` (meters below ground level — how many meters you must dig or pump down from the surface to reach water)**:\n"
            "• **Smaller number (e.g., 3.7 m)** = Water is **closer to the ground surface** (plentiful water after rains; easier and cheaper to pump).\n"
            "• **Larger number (e.g., 6.6 m)** = Water has **dropped deeper underground** (drier season or heavier pumping)."
        )
        seasons_to_check = [detected_season] if detected_season else list(results.keys())
        for season in seasons_to_check:
            res = results[season]
            fc = res.get("forecast")
            if isinstance(fc, pd.DataFrame) and not fc.empty:
                year_col = "Year" if "Year" in fc.columns else ("YEAR" if "YEAR" in fc.columns else None)
                val_col = "Scenario forecast DTWL (mbgl)" if "Scenario forecast DTWL (mbgl)" in fc.columns else None
                if year_col and val_col:
                    facts.append(
                        _synthesize_forecast_story(
                            season=season,
                            model_name=str(res.get("best_model")),
                            fc_df=fc,
                            year_col=year_col,
                            val_col=val_col,
                            family_label="Model-Generated Forecast",
                        )
                    )
            if detected_season:
                deep_fc = res.get("deep_forecast")
                if isinstance(deep_fc, pd.DataFrame) and not deep_fc.empty:
                    year_col = "Year" if "Year" in deep_fc.columns else ("YEAR" if "YEAR" in deep_fc.columns else None)
                    val_col = "Scenario forecast DTWL (mbgl)" if "Scenario forecast DTWL (mbgl)" in deep_fc.columns else None
                    if year_col and val_col:
                        facts.append(
                            _synthesize_forecast_story(
                                season=f"{season} (Deep Learning)",
                                model_name=str(res.get("deep_best_model")),
                                fc_df=deep_fc,
                                year_col=year_col,
                                val_col=val_col,
                                family_label="Model-Generated Forecast",
                            )
                        )
        if len(facts) > 1:
            return facts
        facts.clear()

    # ---- Priority Case 2: Why high / low performance / seasonal variation drivers ----
    is_why_perf = (
        ("why" in q and any(w in q for w in ["performance", "monsoon", "low", "high", "difference", "variation", "better", "worse", "accuracy", "r2", "r²"]))
        or any(kw in q for kw in ["performance difference", "season performance", "seasonal variation", "seasonal difference", "physical reason", "hydrological reason", "accuracy difference", "performance variation"])
    )
    if is_why_perf:
        facts.append(
            "**Seasonal Performance Drivers & Physical Reasons**:\n"
            "• **Monsoon & Post-Monsoon (High R²)**: Heavy precipitation and soil moisture infiltration create strong, clear hydrological signals (high Signal-to-Noise Ratio). Tree ensembles (CatBoost, XGBoost) capture these dominant dynamics accurately.\n"
            "• **Non-Monsoon & Pre-Monsoon (Lower R²)**: In dry seasons, direct precipitation forcing is absent. Groundwater fluctuations are dominated by unobserved agricultural extraction (tube-well pumping) and subtle boundary fluxes, resulting in lower predictor signal relative to background noise."
        )
        return facts

    # ---- Priority Case 3: Comparison intent ("compare top two", "compare X and Y") ----
    compare_intent = any(w in q for w in ["compare", "versus", " vs ", "top two", "top 2", "difference between"])
    if compare_intent:
        season = detected_season or next(iter(results))
        metrics_table = results[season]["metrics"]
        named = [m for m in all_models if m.lower() in q]
        if len(named) >= 2:
            rows = metrics_table[metrics_table["Model"].isin(named)]
            rows = rows.sort_values("Bias-corrected test R2", ascending=False)
        else:
            rows = metrics_table.sort_values("Bias-corrected test R2", ascending=False).head(2)

        for _, row in rows.iterrows():
            try:
                r2 = float(row["Bias-corrected test R2"])
                rmse = float(row["Bias-corrected test RMSE"])
                mae = float(row["Bias-corrected test MAE"])
                facts.append(f"**{row['Model']}** on **{season}**: R² = {r2:.3f}, RMSE = {rmse:.3f}, MAE = {mae:.3f} mbgl")
            except (KeyError, TypeError, ValueError):
                facts.append(f"**{row['Model']}** on **{season}** — scored")

        if not rows.empty:
            facts.append(f"Winner on R² for **{season}**: **{rows.iloc[0]['Model']}**.")
        return facts[:8]

    # ---- Priority Case 4: Deep Learning / Physics-Informed family queries ----
    if _mentions_deep_family(q):
        detected_deep_model = _detect_deep_model(q)
        if detected_season:
            deep_metrics = results[detected_season].get("deep_metrics")
            if deep_metrics is None or deep_metrics.empty:
                facts.append(
                    f"The deep-learning tab has no results for **{detected_season}** — "
                    "either the sidebar toggle was off for this run, or every model in that family failed to fit."
                )
                return facts
            rows = deep_metrics
            if detected_deep_model:
                matched = rows[rows["Model"] == detected_deep_model]
                if not matched.empty:
                    rows = matched
            for _, row in rows.iterrows():
                try:
                    r2 = float(row["Bias-corrected test R2"])
                    rmse = float(row["Bias-corrected test RMSE"])
                    facts.append(f"**{row['Model']}** on **{detected_season}** (deep-learning tab): R² = {r2:.3f}, RMSE = {rmse:.3f} mbgl")
                except (KeyError, TypeError, ValueError):
                    facts.append(f"**{row['Model']}** on **{detected_season}** — scored")
            best_deep = results[detected_season].get("deep_best_model")
            if best_deep and not detected_deep_model:
                facts.append(f"Best in that tab for **{detected_season}**: **{best_deep}**.")
            return facts

        for season, res in results.items():
            deep_metrics = res.get("deep_metrics")
            if deep_metrics is None or deep_metrics.empty:
                continue
            if detected_deep_model:
                matched = deep_metrics[deep_metrics["Model"] == detected_deep_model]
                if matched.empty:
                    continue
                row = matched.iloc[0]
                try:
                    r2 = float(row["Bias-corrected test R2"])
                    facts.append(f"{season}: **{detected_deep_model}** scored R² = {r2:.3f}")
                except (KeyError, TypeError, ValueError):
                    facts.append(f"{season}: **{detected_deep_model}** scored")
            else:
                top_row = deep_metrics.iloc[0]
                try:
                    r2 = float(top_row["Bias-corrected test R2"])
                    facts.append(f"{season}: best in deep-learning tab is **{res.get('deep_best_model')}** (R² = {r2:.3f})")
                except (KeyError, TypeError, ValueError):
                    facts.append(f"{season}: best in deep-learning tab is **{res.get('deep_best_model')}**")
        if not facts:
            facts.append("No deep-learning results are available in this session — check sidebar toggle.")
        return facts[:8]

    # ---- Priority Case 5: Specific season named ----
    if detected_season:
        top = results[detected_season]["metrics"].iloc[0]
        winner = results[detected_season]["best_model"]
        deep_winner = results[detected_season].get("deep_best_model") or "N/A"
        season_desc = _SEASON_PLAIN_ROLE.get(detected_season, detected_season)
        if detected_metric:
            alias, column = detected_metric
            try:
                value = float(top.get(column))
                facts.append(
                    f"For **{detected_season}** (*{season_desc}*), the most accurate AI model is **{winner}** "
                    f"with **{alias.upper()} = {value:.3f}**. Best Deep Learning model: **{deep_winner}**."
                )
            except (TypeError, ValueError):
                facts.append(f"For **{detected_season}**, headline winner is **{winner}**.")
        else:
            try:
                r2 = float(top["Bias-corrected test R2"])
                rmse = float(top["Bias-corrected test RMSE"])
                facts.append(
                    f"For **{detected_season}** (*{season_desc}*), the best-performing AI model is **{winner}** "
                    f"with **R² = {r2:.3f}** (*{_plain_r2_phrase(r2)}*) and an average prediction error of **RMSE = {rmse:.3f} meters (`mbgl`)**. "
                    f"In the Deep Learning family, **{deep_winner}** performed best."
                )
            except (KeyError, TypeError, ValueError):
                facts.append(f"For **{detected_season}**, headline winner is **{winner}**.")
        return facts

    # ---- Priority Case 6: Specific model named ----
    if detected_model:
        model_rows = []
        for season, res in results.items():
            matches = res["metrics"][res["metrics"]["Model"].astype(str) == detected_model]
            if matches.empty:
                continue
            row = matches.iloc[0]
            try:
                r2 = float(row["Bias-corrected test R2"])
                rmse = float(row["Bias-corrected test RMSE"])
                model_rows.append(f"**{season}** — R² = {r2:.3f} (*{_plain_r2_phrase(r2)}*), average error RMSE = {rmse:.3f} m (`mbgl`)")
            except (KeyError, TypeError, ValueError):
                model_rows.append(f"**{season}** — scored")
        if model_rows:
            facts.append(f"**{detected_model}** performance across seasons (higher R² = better accuracy; lower RMSE = smaller error in meters):")
            facts.extend(f"  - {line}" for line in model_rows)
        return facts

    # ---- Priority Case 7: General Best / Winner / Top / Summary queries ----
    summary_keywords = [
        "best", "winner", "won", "top", "leads", "leading", "summary", "overview",
        "rankings", "which model", "result", "results", "overall", "performance",
    ]
    if any(w in q for w in summary_keywords):
        facts.append(
            "**Plain-English Summary of Best Models by Season** *(R² measures accuracy up to 1.0; RMSE is the average error in meters below ground)*:"
        )
        for season, res in results.items():
            top = res["metrics"].iloc[0]
            try:
                r2 = float(top["Bias-corrected test R2"])
                rmse = float(top["Bias-corrected test RMSE"])
                deep_winner = res.get("deep_best_model") or "N/A"
                facts.append(
                    f"• **{season}** (*{_SEASON_PLAIN_ROLE.get(season, season)}*): Best ML Model = **{res['best_model']}** "
                    f"(R² = {r2:.3f} — *{_plain_r2_phrase(r2)}*, average error RMSE = {rmse:.3f} m) | Best Deep Model = **{deep_winner}**"
                )
            except (KeyError, TypeError, ValueError):
                facts.append(f"• **{season}**: Best Model = **{res['best_model']}**")
        return facts[:7]

    return facts


# --------------------------------------------------------------------------- #
# Offline answer — composer
# --------------------------------------------------------------------------- #
_LIVE_LEAD_INS = [
    "Here's what this run shows:",
    "Pulling from your current results:",
    "From this session's numbers:",
    "Here's how that breaks down:",
]


def _offline_answer(
    question: str,
    hits: list[dict],
    job_context: str,
    payload: dict | None,
    twin_state: dict[str, Any] | None = None,
) -> str:
    """Compose a concise answer from live numbers and KB context."""
    live = _extract_live_numbers(question, payload, twin_state=twin_state)
    use_background = bool(hits)

    background = ""
    if use_background:
        raw = hits[0]["text"].strip()
        heading = hits[0].get("heading") or ""
        if heading and raw.startswith(f"{heading}\n\n"):
            raw = raw[len(heading) + 2:].strip()
        raw = re.sub(r"^Q:.*?\n", "", raw, flags=re.DOTALL).strip()
        raw = re.sub(r"^A:\s*", "", raw).strip()
        raw = re.sub(r"^\s*Conversation guide\s*\n+", "", raw).strip()
        if re.search(r"(?m)^\s*1\.\s", raw):
            background = raw
            if len(background) > 650:
                lines, kept, total = background.split("\n"), [], 0
                for line in lines:
                    if total + len(line) > 650 and kept:
                        break
                    kept.append(line)
                    total += len(line) + 1
                background = "\n".join(kept).rstrip()
        else:
            sentences = re.split(r"(?<=[.!?])\s+", raw)
            background = " ".join(sentences[:4]).strip()

    q_lower = question.lower()
    wants_explanation = any(
        token in q_lower
        for token in ["define", "explain", "meaning", "difference between", "how does", "how to read", "architecture", "openusd", "methodology"]
    )

    parts: list[str] = []
    if live:
        if len(live) == 1 and not live[0].startswith("  - "):
            fact = live[0]
            parts.append(fact[0].upper() + fact[1:] if fact else fact)
        else:
            parts.append(_pick(_LIVE_LEAD_INS, question + "::live"))
            for fact in live:
                parts.append(fact if fact.startswith("  - ") else f"- {fact}")

    if background and (not live or wants_explanation):
        if live:
            parts.append(f"**Methodology & Reference Context:**\n{background}")
        else:
            opener = _pick(_OPENERS, question)
            parts.append(f"{opener}\n\n{background}")

    if not parts:
        return _NO_ANSWER

    return "\n\n".join(parts)


# --------------------------------------------------------------------------- #
# Online answer — provider-agnostic (Gemini by default)
# --------------------------------------------------------------------------- #
def _online_answer(
    question: str,
    hits: list[dict],
    job_context: str,
    history: list[dict] | None,
    payload: dict | None,
    twin_state: dict[str, Any] | None = None,
) -> str:
    """Try the configured LLM. Fall back to offline composer on any issue."""
    if active_provider() == "none":
        return _offline_answer(question, hits, job_context, payload, twin_state=twin_state)

    knowledge = "\n\n---\n\n".join(
        f"[{h['title']} — {h.get('heading') or h['source']}]\n{h['text']}" for h in hits
    ) or "(no relevant knowledge-base chunks found)"

    transcript = _format_history(history)

    user_message = (
        f"CONTEXT (current analysis run & Digital Twin telemetry — read exact numbers from here):\n"
        f"{job_context}\n\n"
        f"KNOWLEDGE (methodology excerpts, cite concepts accurately):\n"
        f"{knowledge}\n\n"
        + (f"RECENT CONVERSATION:\n{transcript}\n\n" if transcript else "")
        + f"USER QUESTION:\n{question}"
    )

    result = complete(system=_SYSTEM_PROMPT, user=user_message, max_tokens=700)

    if result is None:
        return _offline_answer(question, hits, job_context, payload, twin_state=twin_state)

    if result.startswith("__ERROR__"):
        error_name = result.replace("__ERROR__", "", 1)
        fallback = _offline_answer(question, hits, job_context, payload, twin_state=twin_state)
        return (
            f"_(LLM call failed: {error_name}; answering offline.)_\n\n"
            f"{fallback}"
        )

    return result.strip()


def _infer_provenance(
    live_facts: list[str],
    sources: list[str],
    twin_state: dict[str, Any] | None,
    payload: dict[str, Any] | None,
) -> list[str]:
    """Return explicit epistemic provenance tags for the generated answer."""
    tags: list[str] = []
    joined = " ".join(live_facts)
    if "Verified Historical Observation" in joined or (payload and payload.get("results")):
        tags.append("Verified Historical Observation")
    if "Model-Generated Forecast" in joined or any("R²" in f or "Forecast" in f for f in live_facts):
        tags.append("Model-Generated Forecast")
    if "Coupled Simulation Output" in joined or (twin_state and (twin_state.get("simulation_summary") or twin_state.get("simulation"))):
        tags.append("Coupled Simulation Output")
    if sources:
        tags.append("Knowledge Base Reference")
    if not tags:
        tags.append("System Reference")
    return _dedupe_preserve_order(tags)


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def answer(
    question: str,
    payload: dict[str, Any] | None,
    history: list[dict] | None = None,
    prefer_llm: bool = True,
    twin_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Main entry point for the Naya Pani RAG & Digital Twin Assistant.

    Returns
    -------
    {
        'answer': str,
        'sources': [filenames],
        'section_citations': [filename#heading],
        'provenance': [epistemic tags],
        'provider': str
    }
    """
    question = (question or "").strip()
    if not question:
        return {
            "answer": "Please type a question.",
            "sources": [],
            "section_citations": [],
            "provenance": [],
            "provider": "offline",
        }

    sanitized_q, sec_notices = sanitize_rag_prompt(question)
    critical_notices = [n for n in sec_notices if getattr(n, "severity", "") == "CRITICAL"]
    if critical_notices and "[Filtered Instruction]" in sanitized_q:
        return {
            "answer": f"🛡️ Security Policy Guardrail: {critical_notices[0].message}",
            "sources": [],
            "section_citations": [],
            "provenance": ["Security Policy Guardrail"],
            "provider": "offline",
        }
    question = sanitized_q

    # Fast path: greetings, thanks, help, goodbyes.
    canned = smalltalk_reply(question)
    if canned is not None:
        return {
            "answer": canned,
            "sources": [],
            "section_citations": [],
            "provenance": ["Conversational Assistant"],
            "provider": "offline",
        }

    # Short confirmations ("yes", "ok") — avoid a generic, canned drift.
    if question.lower().strip(" .!?") in _SHORT_CONFIRMATIONS:
        return {
            "answer": (
                "I can explain a metric, compare seasonal ML/DL models, inspect the selected "
                "Digital Twin monitoring well, or summarize the active what-if simulation.\n\n"
                "Try asking for an exact metric, a season, a village asset, or a scenario perturbation."
            ),
            "sources": [],
            "section_citations": [],
            "provenance": ["Conversational Assistant"],
            "provider": "offline",
        }

    resolved_twin = _resolve_twin_state(twin_state)
    q_with_context = _with_followup_context(question, history)
    direct_live = _extract_live_numbers(q_with_context, payload, twin_state=resolved_twin)

    wants_concept = any(
        token in q_with_context.lower()
        for token in ["define", "explain", "meaning", "difference between", "how does", "how to read", "architecture", "openusd", "methodology"]
    )

    if direct_live and not wants_concept:
        clean_ans = sanitize_rag_response("\n\n".join(direct_live[:7]))
        return {
            "answer": clean_ans,
            "sources": [],
            "section_citations": [],
            "provenance": _infer_provenance(direct_live, [], resolved_twin, payload),
            "provider": "offline",
        }

    # Grounded retrieval path.
    hits = _kb().search(q_with_context, top_k=4)
    job_context = build_job_context(payload, twin_state=resolved_twin)

    if prefer_llm:
        text = _online_answer(q_with_context, hits, job_context, history, payload, twin_state=resolved_twin)
        provider = active_provider() if not text.startswith("_(") else "offline"
    else:
        text = _offline_answer(q_with_context, hits, job_context, payload, twin_state=resolved_twin)
        provider = "offline"

    text = sanitize_rag_response(text)
    sources = _dedupe_preserve_order([h["source"] for h in hits])
    section_citations = _dedupe_preserve_order([h.get("section_citation", h["source"]) for h in hits])
    provenance = _infer_provenance(direct_live, sources, resolved_twin, payload)

    return {
        "answer": text,
        "sources": sources,
        "section_citations": section_citations,
        "provenance": provenance,
        "provider": provider,
    }
