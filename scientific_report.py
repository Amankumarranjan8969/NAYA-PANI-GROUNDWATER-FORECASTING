from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
try:
    from docx import Document
    from docx.document import Document as DocumentType
    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor
    from docx.styles.style import ParagraphStyle
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    Document = None
    DocumentType = Any
    WD_CELL_VERTICAL_ALIGNMENT = None
    WD_ALIGN_PARAGRAPH = None


UNAVAILABLE = "Not available in the current analysis."
MAIN_METRICS = [
    "Test R2",
    "Bias-corrected test R2",
    "Test RMSE",
    "Test MAE",
    "Bias-corrected test RMSE",
    "Bias-corrected test MAE",
    "Bias-corrected test Pearson r",
    "Bias-corrected test KGE",
    "Bias-corrected test NSE",
    "Bias-corrected test Bias",
]
METRIC_EXPLANATIONS = [
    ("R²", "How much test-set variation the model explains; 1 is ideal, and a negative value can occur."),
    ("RMSE", "Typical prediction error in mbgl, with larger errors penalised more strongly."),
    ("MAE", "Average absolute prediction error in mbgl."),
    ("Pearson r", "Strength and direction of the linear relationship between predictions and observations."),
    ("KGE", "Combines correlation, variability, and mean agreement; values closer to 1 are better."),
    ("NSE", "Skill relative to predicting the observed mean; 1 is ideal and values below 0 indicate poor skill."),
    ("NRMSE", "RMSE scaled by the observed test range, for comparison across ranges."),
    ("WI", "Agreement index comparing model error with deviations from the observed mean."),
    ("LMI", "Absolute-error skill relative to deviations from the observed mean."),
    ("Bias", "Mean signed prediction error (prediction minus observation), in mbgl."),
]


def _text(value: Any) -> str:
    if value is None:
        return UNAVAILABLE
    try:
        if pd.isna(value):
            return UNAVAILABLE
    except (TypeError, ValueError):
        pass
    return str(value)


def _format_count(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError, OverflowError):
        return _text(value)


def _shade_cell(cell: Any, color: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    properties.append(shading)


def _add_table(
    document: DocumentType,
    frame: pd.DataFrame | None,
    *,
    title: str | None = None,
    max_rows: int | None = None,
    max_columns: int = 12,
) -> None:
    if title:
        document.add_heading(title, level=3)
    if not isinstance(frame, pd.DataFrame) or frame.empty or len(frame.columns) == 0:
        document.add_paragraph(UNAVAILABLE)
        return

    shown = frame.iloc[:, :max_columns].copy()
    truncated_columns = len(frame.columns) - len(shown.columns)
    if max_rows is not None:
        shown = shown.head(max_rows)
    table = document.add_table(rows=1, cols=len(shown.columns))
    table.style = "Light Shading Accent 1"
    table.autofit = True
    for index, column in enumerate(shown.columns):
        cell = table.rows[0].cells[index]
        cell.text = str(column)
        _shade_cell(cell, "DCEAF7")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for run in cell.paragraphs[0].runs:
            run.bold = True
            run.font.size = Pt(8)

    for row_values in shown.itertuples(index=False, name=None):
        cells = table.add_row().cells
        for index, value in enumerate(row_values):
            cells[index].text = _text(value)
            cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for paragraph in cells[index].paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(8)

    notes: list[str] = []
    if max_rows is not None and len(frame) > len(shown):
        notes.append(
            f"Showing {len(shown):,} of {len(frame):,} rows; the complete tabular output remains available in the Excel export."
        )
    if truncated_columns:
        notes.append(
            f"{truncated_columns} additional columns were omitted from this Word table to preserve page readability."
        )
    if notes:
        note = document.add_paragraph(" ".join(notes))
        note.style = "Caption"


def _add_bullet(document: DocumentType, text: str) -> None:
    document.add_paragraph(text, style="List Bullet")


def _add_toc_field(paragraph: Any) -> None:
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = ' TOC \\o "1-2" \\h \\z \\u '
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Open in Word and update the table to populate page numbers."
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    paragraph.add_run()._r.append(begin)
    paragraph.add_run()._r.append(instruction)
    paragraph.add_run()._r.append(separate)
    paragraph.add_run()._r.append(placeholder)
    paragraph.add_run()._r.append(end)


def _add_page_number(paragraph: Any) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    start = OxmlElement("w:fldChar")
    start.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    number = OxmlElement("w:t")
    number.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (start, instruction, separate, number, end):
        paragraph.add_run()._r.append(element)


def _configure_document(document: DocumentType) -> None:
    section = document.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)
    styles = document.styles
    normal_style = styles["Normal"]
    if isinstance(normal_style, ParagraphStyle):
        normal_style.font.name = "Aptos"
        normal_style.font.size = Pt(9)
        normal_style.font.color.rgb = RGBColor(38, 50, 56)
    title_style = styles["Title"]
    if isinstance(title_style, ParagraphStyle):
        title_style.font.name = "Aptos Display"
        title_style.font.size = Pt(28)
        title_style.font.color.rgb = RGBColor(17, 82, 110)
    for style_name, size in (("Heading 1", 17), ("Heading 2", 13), ("Heading 3", 10)):
        heading_style = styles[style_name]
        if isinstance(heading_style, ParagraphStyle):
            heading_style.font.name = "Aptos Display"
            heading_style.font.size = Pt(size)
            heading_style.font.color.rgb = RGBColor(17, 82, 110)
    header = section.header.paragraphs[0]
    header.text = "NAYA-PANI /  |  SCIENTIFIC ANALYSIS"
    header.style = "Caption"
    footer = section.footer.paragraphs[0]
    footer.add_run("Generated from current dashboard analysis  •  Page ")
    _add_page_number(footer)
    update_fields = OxmlElement("w:updateFields")
    update_fields.set(qn("w:val"), "true")
    document.settings.element.append(update_fields)


def _metric_columns(metrics: pd.DataFrame) -> list[str]:
    preferred = ["Model"] + [column for column in MAIN_METRICS if column in metrics.columns]
    if len(preferred) > 1:
        return preferred
    return list(metrics.columns[:10])


def _metric_short_definitions(document: DocumentType) -> None:
    _add_table(
        document,
        pd.DataFrame(METRIC_EXPLANATIONS, columns=["Metric", "Plain-language meaning"]),
        title="How to read the metrics",
    )


def _prediction_figure(predictions: pd.DataFrame, model_name: str) -> bytes | None:
    actual_column = "Actual DTWL (mbgl)"
    predicted_column = f"{model_name} bias-corrected prediction"
    if predictions.empty or actual_column not in predictions or predicted_column not in predictions:
        return None
    actual = pd.to_numeric(predictions[actual_column], errors="coerce")
    predicted = pd.to_numeric(predictions[predicted_column], errors="coerce")
    valid = actual.notna() & predicted.notna()
    if not valid.any():
        return None
    actual_values = actual.loc[valid].to_numpy(dtype=float)
    predicted_values = predicted.loc[valid].to_numpy(dtype=float)
    lower = float(min(actual_values.min(), predicted_values.min()))
    upper = float(max(actual_values.max(), predicted_values.max()))
    if lower == upper:
        margin = max(abs(lower) * 0.05, 0.5)
        lower -= margin
        upper += margin

    figure, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    axes[0].scatter(actual_values, predicted_values, alpha=0.65, s=20, color="#147D92")
    axes[0].plot([lower, upper], [lower, upper], "--", color="#64748B", linewidth=1)
    axes[0].set(xlabel="Observed DTWL (mbgl)", ylabel="Predicted DTWL (mbgl)",
                title="Held-out observations")
    axes[0].grid(alpha=0.2)

    chart_data = predictions.loc[valid, ["Year", actual_column, predicted_column]].copy()
    chart_data["Year"] = pd.to_numeric(chart_data["Year"], errors="coerce")
    annual = chart_data.groupby("Year", as_index=False)[[actual_column, predicted_column]].median()
    axes[1].plot(annual["Year"], annual[actual_column], "o-", label="Observed", color="#147D92")
    axes[1].plot(annual["Year"], annual[predicted_column], "s--", label="Predicted", color="#E07A5F")
    axes[1].set(xlabel="Year", ylabel="Median DTWL (mbgl)", title="Median by test year")
    axes[1].grid(alpha=0.2)
    axes[1].legend(frameon=False, fontsize=8)
    figure.tight_layout()
    output = BytesIO()
    figure.savefig(output, format="png", dpi=160, bbox_inches="tight")
    plt.close(figure)
    return output.getvalue()


def _add_figure(document: DocumentType, image_data: bytes | None, caption: str) -> None:
    if image_data is None:
        document.add_paragraph(UNAVAILABLE)
        return
    document.add_picture(BytesIO(image_data), width=Inches(6.4))
    paragraph = document.add_paragraph(caption, style="Caption")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def _append_season_results(
    document: DocumentType,
    season: str,
    result: dict[str, Any],
) -> None:
    metrics = result.get("metrics")
    if not isinstance(metrics, pd.DataFrame) or metrics.empty:
        document.add_heading(f"Results for {season}", level=2)
        document.add_paragraph(UNAVAILABLE)
        return

    model_name = str(result.get("best_model", UNAVAILABLE))
    ranked = metrics.loc[metrics["Model"].astype(str).eq(model_name)]
    if ranked.empty:
        ranked = metrics.head(1)
    best = ranked.iloc[0]
    corrected_r2 = best.get("Bias-corrected test R2", np.nan)
    corrected_rmse = best.get("Bias-corrected test RMSE", np.nan)
    document.add_heading(f"Results for {season}", level=2)
    document.add_paragraph(
        f"Simple interpretation: {model_name} ranked first for this season under the "
        "pipeline's bias-corrected test R² ranking. This indicates the strongest relative "
        "test-set fit among models that completed; it does not establish causation."
    )
    document.add_paragraph(
        f"Technical result: bias-corrected test R² = {_text(corrected_r2)}; "
        f"bias-corrected test RMSE = {_text(corrected_rmse)} mbgl. "
        f"Input observations = {_format_count(result.get('raw_rows'))}; "
        f"rows used after feature creation = {_format_count(result.get('lagged_rows'))}; "
        f"rows removed during strict lag-feature creation = {_format_count(result.get('rows_removed'))}."
    )

    split_counts = result.get("split_counts")
    if isinstance(split_counts, pd.Series):
        document.add_paragraph(
            "Partitioning: "
            + str(result.get("split_mode", UNAVAILABLE))
            + "."
        )
        split_frame = split_counts.rename_axis("Partition").rename("Rows").reset_index()
        _add_table(document, split_frame, title="Train, validation, and test row counts")
    else:
        document.add_paragraph(f"Split counts: {UNAVAILABLE}")

    available_metrics = metrics[_metric_columns(metrics)]
    _add_table(document, available_metrics, title="Headline model comparison")
    _add_table(document, result.get("deep_metrics"), title="Deep-learning and physics-informed model comparison")

    selected_features = result.get("selected_features")
    if isinstance(selected_features, (list, tuple)) and selected_features:
        document.add_paragraph(
            "Selected predictors for this season: " + ", ".join(map(str, selected_features)) + "."
        )
    else:
        document.add_paragraph(f"Selected predictors: {UNAVAILABLE}")

    ranking = result.get("feature_ranking")
    if isinstance(ranking, pd.DataFrame) and not ranking.empty:
        _add_table(document, ranking, title="Feature ranking (training data)", max_rows=10)
        document.add_paragraph(
            "Simple interpretation: higher ranking values indicate stronger statistical "
            "association used for predictor selection. They are not proof that a factor causes "
            "groundwater change."
        )
        document.add_paragraph(
            "Technical method: feature selection is performed on training data only, using "
            "mRMR when available; otherwise mutual information is used for ranking and the "
            "requested number of features is selected."
        )
    else:
        document.add_paragraph(f"Feature ranking: {UNAVAILABLE}")

    sensitivity = result.get("lofo")
    if isinstance(sensitivity, pd.DataFrame) and not sensitivity.empty:
        _add_table(document, sensitivity, title="Leave-one-feature-out sensitivity", max_rows=10)
        document.add_paragraph(
            "Simple interpretation: a larger positive correlation drop means held-out "
            "prediction correlation declined more when that predictor was removed."
        )
        document.add_paragraph(
            "Technical method: the selected best model is refitted after removing one feature "
            "at a time; the table compares Pearson correlation with the baseline."
        )
    else:
        document.add_paragraph(
            "Feature sensitivity: Not available in the current analysis (the sensitivity "
            "calculation may have been disabled or produced no results)."
        )

    predictions = result.get("predictions")
    if isinstance(predictions, pd.DataFrame) and not predictions.empty:
        pred_col = f"{model_name} bias-corrected prediction"
        chosen = ["Year", "Village", "Actual DTWL (mbgl)", pred_col]
        available = [column for column in chosen if column in predictions.columns]
        if available:
            _add_table(
                document,
                predictions[available].sort_values(
                    [column for column in ["Year", "Village"] if column in available]
                ),
                title="Observed and predicted held-out values (sample)",
                max_rows=12,
            )
            figure = _prediction_figure(predictions, model_name)
            _add_figure(
                document,
                figure,
                f"Figure: Held-out observed DTWL compared with {model_name}'s "
                "bias-corrected predictions. The left panel compares values against "
                "the 1:1 agreement line; the right panel shows annual medians.",
            )
        else:
            document.add_paragraph(f"Observed-versus-predicted values: {UNAVAILABLE}")
    else:
        document.add_paragraph(f"Observed-versus-predicted values: {UNAVAILABLE}")

def _add_written_forecast_narrative(document: DocumentType, forecast: pd.DataFrame, label: str) -> None:
    if not isinstance(forecast, pd.DataFrame) or forecast.empty:
        return
    narrative_parts = []
    year_col = "Year" if "Year" in forecast.columns else ("YEAR" if "YEAR" in forecast.columns else None)
    val_col = "Scenario forecast DTWL (mbgl)" if "Scenario forecast DTWL (mbgl)" in forecast.columns else None
    if not val_col:
        for c in forecast.columns:
            if "DTWL" in c or "forecast" in c.lower():
                val_col = c
                break
    if year_col and val_col:
        for _, row in forecast.iterrows():
            yr = row[year_col]
            v = row[val_col]
            try:
                narrative_parts.append(f"in {int(yr)}, the predicted Depth to Water Level (DTWL) is {float(v):.2f} mbgl")
            except (ValueError, TypeError):
                narrative_parts.append(f"in {yr}, the predicted DTWL is {v} mbgl")
    if narrative_parts:
        text = f"Written Forecast Projection Narrative ({label}): " + "; ".join(narrative_parts) + "."
        document.add_paragraph(text)


def _append_season_results(document: DocumentType, season: str, result: dict[str, Any]) -> None:
    metrics = result.get("metrics")
    if not isinstance(metrics, pd.DataFrame) or metrics.empty:
        document.add_paragraph(f"Headline metrics: {UNAVAILABLE}")
        return

    best = metrics.iloc[0]
    model_name = str(best.get("Model", "Best Model"))

    document.add_heading(f"{season}: Performance Summary", level=2)
    document.add_paragraph(
        f"Headline winner: {model_name} achieved the highest bias-corrected test R² "
        f"({_text(best.get('Bias-corrected test R2'))}) and test RMSE "
        f"({_text(best.get('Bias-corrected test RMSE'))} mbgl). "
        f"Rows used after feature creation = {_format_count(result.get('lagged_rows'))}; "
        f"rows removed during strict lag-feature creation = {_format_count(result.get('rows_removed'))}."
    )

    split_counts = result.get("split_counts")
    if isinstance(split_counts, pd.Series):
        document.add_paragraph(
            "Partitioning: "
            + str(result.get("split_mode", UNAVAILABLE))
            + "."
        )
        split_frame = split_counts.rename_axis("Partition").rename("Rows").reset_index()
        _add_table(document, split_frame, title="Train, validation, and test row counts")
    else:
        document.add_paragraph(f"Split counts: {UNAVAILABLE}")

    available_metrics = metrics[_metric_columns(metrics)]
    _add_table(document, available_metrics, title="Headline model comparison")
    _add_table(document, result.get("deep_metrics"), title="Deep-learning and physics-informed model comparison")

    selected_features = result.get("selected_features")
    if isinstance(selected_features, (list, tuple)) and selected_features:
        document.add_paragraph(
            "Selected predictors for this season: " + ", ".join(map(str, selected_features)) + "."
        )
    else:
        document.add_paragraph(f"Selected predictors: {UNAVAILABLE}")

    ranking = result.get("feature_ranking")
    if isinstance(ranking, pd.DataFrame) and not ranking.empty:
        _add_table(document, ranking, title="Feature ranking (training data)", max_rows=10)
        document.add_paragraph(
            "Simple interpretation: higher ranking values indicate stronger statistical "
            "association used for predictor selection. They are not proof that a factor causes "
            "groundwater change."
        )
    else:
        document.add_paragraph(f"Feature ranking: {UNAVAILABLE}")

    sensitivity = result.get("lofo")
    if isinstance(sensitivity, pd.DataFrame) and not sensitivity.empty:
        _add_table(document, sensitivity, title="Leave-one-feature-out sensitivity", max_rows=10)
    else:
        document.add_paragraph("Feature sensitivity: Not available in the current analysis.")

    predictions = result.get("predictions")
    if isinstance(predictions, pd.DataFrame) and not predictions.empty:
        pred_col = f"{model_name} bias-corrected prediction"
        chosen = ["Year", "Village", "Actual DTWL (mbgl)", pred_col]
        available = [column for column in chosen if column in predictions.columns]
        if available:
            _add_table(
                document,
                predictions[available].sort_values(
                    [column for column in ["Year", "Village"] if column in available]
                ),
                title="Observed and predicted held-out values (sample)",
                max_rows=12,
            )
            figure = _prediction_figure(predictions, model_name)
            _add_figure(
                document,
                figure,
                f"Figure: Held-out observed DTWL compared with {model_name}'s "
                "bias-corrected predictions. The left panel compares values against "
                "the 1:1 agreement line; the right panel shows annual medians.",
            )

    forecast = result.get("forecast")
    if isinstance(forecast, pd.DataFrame) and not forecast.empty:
        document.add_paragraph(
            "SIMULATION / SCENARIO FORECAST: recursive multi-year scenario predictions "
            "updating target lags forward."
        )
        _add_table(document, forecast, title="Headline model scenario forecast outputs")
        _add_written_forecast_narrative(document, forecast, f"{model_name} ({season})")
    else:
        document.add_paragraph(f"Scenario forecast: {UNAVAILABLE}")

    deep_forecast = result.get("deep_forecast")
    if isinstance(deep_forecast, pd.DataFrame) and not deep_forecast.empty:
        deep_model_name = result.get("deep_best_model") or "Deep Model"
        _add_table(document, deep_forecast, title=f"Deep learning scenario forecast outputs ({deep_model_name})")
        _add_written_forecast_narrative(document, deep_forecast, f"{deep_model_name} Deep Model ({season})")

    deep_predictions = result.get("deep_predictions")
    if isinstance(deep_predictions, pd.DataFrame) and not deep_predictions.empty:
        deep_model = result.get("deep_best_model")
        document.add_paragraph(
            f"Separate model family: the best reported deep-learning / physics-informed "
            f"model for this season was {_text(deep_model)}. Its outputs remain separate "
            "from the six-model headline family."
        )
        if deep_model:
            deep_figure = _prediction_figure(deep_predictions, str(deep_model))
            _add_figure(
                document,
                deep_figure,
                f"Figure: Held-out observed and bias-corrected predictions for {_text(deep_model)}.",
            )
    else:
        document.add_paragraph(
            "Deep-learning / physics-informed predictions: Not available in the current analysis."
        )


def _add_provenance(document: DocumentType, payload: dict[str, Any], source_name: str) -> None:
    identity = payload.get("upload_identity")
    document.add_paragraph(f"Uploaded document: {source_name or UNAVAILABLE}")
    if isinstance(identity, (tuple, list)) and len(identity) >= 3:
        document.add_paragraph(
            f"Uploaded file size: {_format_count(identity[1])} bytes; "
            f"SHA-256: {_text(identity[2])}."
        )
    document.add_paragraph(
        "Report provenance: generated directly from this session's uploaded workbook, "
        "data-quality report, and stored model outputs. This report does not rerun training."
    )


def build_scientific_report(payload: dict[str, Any], source_name: str = "") -> bytes:
    """Generate a Word report from the current uploaded data and model results."""
    if not HAS_DOCX:
        raise RuntimeError("The 'python-docx' package is not installed. Please install python-docx to generate Word reports.")
    results = payload.get("results")
    if not isinstance(results, dict) or not results:
        raise ValueError("No completed seasonal model results are available for reporting.")

    document = Document()
    _configure_document(document)
    title = document.add_paragraph(style="Title")
    title.add_run("NAYA-PANI\nGroundwater Scientific Report")
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    document.add_paragraph(
        "Analysis date and time: " + datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    )
    _add_provenance(document, payload, source_name)

    document.add_heading("Abstract & Executive Summary", level=1)
    overview = payload.get("clean_data")
    total_rows = len(overview) if isinstance(overview, pd.DataFrame) else None
    seasons = list(results)
    document.add_paragraph(
        "Abstract: This scientific report delivers a comprehensive evaluation of machine-learning "
        "and physics-informed deep learning models applied to seasonal Depth to Water Level (DTWL) "
        "forecasting across multiple seasons and monitoring villages. By combining historical target lags, "
        "meteorological forcing (precipitation, temperature, humidity), soil moisture profiles, "
        "and hydro-meteorological indices, the system provides multi-year scenario forecasts, "
        "feature sensitivity rankings, and interactive Digital Twin decision support."
    )
    document.add_paragraph(
        f"Technical Summary: {len(seasons)} season(s) were analysed "
        f"({', '.join(map(str, seasons))}) with {(_format_count(total_rows) if total_rows is not None else UNAVAILABLE)} "
        "validated observations. Model performance highlights for each season include:"
    )
    for season, result in results.items():
        metrics = result.get("metrics")
        if isinstance(metrics, pd.DataFrame) and not metrics.empty:
            best = metrics.iloc[0]
            _add_bullet(
                document,
                f"{season}: Best-ranked model **{best.get('Model', UNAVAILABLE)}** with "
                f"bias-corrected test R² = {_text(best.get('Bias-corrected test R2'))}, "
                f"RMSE = {_text(best.get('Bias-corrected test RMSE'))} mbgl, "
                f"MAE = {_text(best.get('Bias-corrected test MAE'))} mbgl.",
            )
        else:
            _add_bullet(document, f"{season}: Model results unavailable.")

    document.add_heading("Seasonal Performance Variation & Physical Drivers", level=2)
    document.add_paragraph(
        "Why Model Skill Varies Across Seasons:\n"
        "• High Skill in Monsoon & Post-Monsoon Seasons: Heavy precipitation and rapid soil moisture "
        "recharge introduce a dominant hydrometeorological signal with strong variance. Tree-based ensembles "
        "(CatBoost, XGBoost, Random Forest) effectively capture these strong non-linear relationships, yielding high test R² values.\n"
        "• Lower Skill in Non-Monsoon & Pre-Monsoon Seasons: In dry seasons, direct rainfall drivers are minimal. "
        "Groundwater variations are primarily driven by unobserved anthropogenic extractions (tube-well pumping, "
        "irrigation draft) and subtle boundary fluxes, which reduces the signal-to-noise ratio in weather-based predictors."
    )

    document.add_heading("Table of Contents", level=1)
    _add_toc_field(document.add_paragraph())
    document.add_paragraph(
        "If page numbers are not shown, select the table in Microsoft Word and choose Update Field."
    )

    document.add_heading("1. Project Overview", level=1)
    document.add_paragraph(
        "Simple explanation: NAYA-PANI analyses seasonal environmental and "
        "historical groundwater observations to estimate groundwater depth and explore "
        "future conditions."
    )
    document.add_paragraph(
        "Technical context: the application validates recognised seasonal workbook sheets, "
        "engineers predictors, uses temporal model comparisons, and provides forecasts, "
        "diagnostics, explainability outputs, and a data-bound Digital Twin view."
    )

    document.add_heading("2. Data Used", level=1)
    clean_data = payload.get("clean_data")
    if isinstance(clean_data, pd.DataFrame) and not clean_data.empty:
        document.add_paragraph(
            f"Observations after workbook loading and validation: {_format_count(len(clean_data))}. "
            f"Fields carried into the analysis: {', '.join(map(str, clean_data.columns))}."
        )
        if "YEAR" in clean_data:
            years = pd.to_numeric(clean_data["YEAR"], errors="coerce").dropna()
            period = f"{years.min():.0f}–{years.max():.0f}" if not years.empty else UNAVAILABLE
            document.add_paragraph(f"Observed year range: {period}.")
        if "Season" in clean_data:
            document.add_paragraph(
                "Seasons present in loaded data: "
                + ", ".join(map(str, clean_data["Season"].dropna().unique()))
                + "."
            )
    else:
        document.add_paragraph(f"Loaded data summary: {UNAVAILABLE}")
    document.add_paragraph(
        "Dataset name/source: the uploaded workbook shown in the provenance block; "
        "an external source or collection method is not inferred if it was not recorded."
    )
    target = "DTWL (mbgl)"
    document.add_paragraph(
        "Prediction target — simple: groundwater depth below ground level. Technical: "
        f"{target}, measured in metres below ground level (mbgl); a larger value represents "
        "a deeper water level."
    )
    _add_table(document, payload.get("workbook_report"), title="Workbook sheets and loading checks")
    _add_table(document, payload.get("validation_report"), title="Data-quality checks and actions")
    notices = payload.get("notices")
    if isinstance(notices, (list, tuple)) and notices:
        document.add_paragraph("Workbook notices:")
        for notice in notices:
            _add_bullet(document, str(notice))
    elif not notices:
        document.add_paragraph("Workbook notices: none recorded.")

    document.add_heading("3. What the System Predicts", level=1)
    document.add_paragraph(
        "Simple explanation: it estimates how far groundwater is below the ground surface "
        "for the selected season and village-year observations."
    )
    document.add_paragraph(
        "Technical definition: the supervised-learning target is DTWL (mbgl). Predictions "
        "are compared with measured DTWL on the temporal test partition. Raw and "
        "training-mean bias-corrected predictions are retained separately."
    )

    document.add_heading("4. How the Prediction Works", level=1)
    document.add_paragraph(
        "Environmental + Historical Groundwater Data → Pattern Learning → "
        "Groundwater Prediction → Comparison with Observed Groundwater"
    )
    config = payload.get("config")
    if config is not None:
        train_end = getattr(config, "train_end", None)
        validation_end = getattr(config, "validation_end", None)
        document.add_paragraph(
            f"Technical method: temporal split configuration uses training years through "
            f"{_text(train_end)}, validation through {_text(validation_end)}, and later "
            "years for test where a holdout split is possible. Feature selection is fitted "
            "on training data only; a StandardScaler is fitted on training predictors and "
            "applied to validation and test data."
        )
        document.add_paragraph(
            f"Configured feature count: {_text(getattr(config, 'selected_feature_count', None))}; "
            f"tree estimator count: {_text(getattr(config, 'tree_count', None))}; "
            f"optional model family enabled: {_text(getattr(config, 'include_optional_models', None))}; "
            f"deep family enabled: {_text(getattr(config, 'include_deep_models', None))}."
        )
    else:
        document.add_paragraph(f"Run configuration: {UNAVAILABLE}")

    document.add_heading("5. Model Results", level=1)
    document.add_paragraph(
        "Simple interpretation: models are compared on data held out by year when the "
        "uploaded data supports the configured split. The highest pipeline-ranked "
        "bias-corrected test R² is identified per season."
    )
    document.add_paragraph(
        "Technical note: bias correction adds the difference between the training target "
        "mean and the model's training prediction mean to predictions; raw test metrics "
        "are also retained in the tables."
    )
    _metric_short_definitions(document)

    document.add_heading("6. Factors Associated with Predictions", level=1)
    document.add_paragraph(
        "Simple interpretation: the following tables report which measured, engineered, "
        "and historical variables were selected or most sensitive in this run."
    )
    document.add_paragraph(
        "Technical caution: these are predictive associations and sensitivity analyses, "
        "not causal estimates of groundwater response."
    )

    document.add_heading("7. Observed Versus Predicted Results", level=1)
    document.add_paragraph(
        "Figures and sample tables use held-out observations and predictions from the "
        "current run. The diagonal in each scatter plot indicates perfect agreement."
    )
    document.add_heading("8. Digital Twin Architecture & Operational Significance", level=1)
    document.add_paragraph(
        "Definition & Significance: The NAYA-PANI Digital Twin is an interactive, data-bound 3D representation "
        "of the regional groundwater system. It serves as a visual bridge connecting empirical hydrogeological data, "
        "machine learning forecasts, and real-time decision-making for water resource managers."
    )
    document.add_paragraph(
        "Operational Value & Capabilities:\n"
        "1. Multi-Layer Spatial Integration: Integrates 3D terrain topography, monitoring well networks, "
        "aquifer layers, river channels, precipitation grids, evapotranspiration flux, and soil moisture profiles into a unified visual environment.\n"
        "2. Interactive Stress Testing: Enables managers to simulate extraction stress, drought shocks, "
        "and artificial recharge scenarios by adjusting regional recharge/pumping multipliers in real time.\n"
        "3. Scenario Visualization: Displays projected groundwater table levels across historical years and future scenario horizon years (2023–2027), allowing early identification of depleting groundwater zones."
    )
    document.add_paragraph(
        "Technical Architecture: The Digital Twin derives its baseline data directly from the selected season's "
        "validated observations and model forecast outputs. Filtering options allow district-, year-, and season-specific "
        "queries. Toggleable conceptual layers render subsurface flows and well depths. Interactive simulation sliders "
        "provide immediate visual feedback for local policy exploration."
    )

    document.add_heading("9. Deep Learning & Physics-Informed Modeling", level=1)
    document.add_paragraph(
        "Methodology & Model Architectures: In addition to the six headline gradient-boosted and tree ensemble models, "
        "NAYA-PANI evaluates a specialized deep learning and physics-informed model family:\n"
        "1. PINN (Physics-Informed Neural Network): Integrates a physical hydrostatic loss regularization penalty "
        "into the neural network loss function, penalizing unphysical groundwater jumps between consecutive temporal steps.\n"
        "2. Reservoir Computing (ESN - Echo State Network): Uses a fixed, randomly connected recurrent reservoir of nonlinear "
        "nodes with fast linear output training, capturing complex temporal memory dynamics without gradient vanishing.\n"
        "3. SARIMA (Seasonal AutoRegressive Integrated Moving Average): Classical statistical seasonal model establishing baseline linear autoregressive memory.\n"
        "4. LSTM (Long Short-Term Memory Network): Recurrent deep neural network with gated memory cells specialized for sequential time-series patterns."
    )
    document.add_paragraph(
        "Comparative Evaluation: Deep models are evaluated on the exact same temporal holdout test splits, "
        "with bias-correction and standard metric sets (R², RMSE, MAE, KGE, NSE). Multi-year recursive scenario forecasts "
        "generated by the deep models for each season are illustrated in the 2x2 multi-season forecast figure below."
    )
    try:
        from pipeline import build_2x2_forecast_figure
        deep_2x2_fig = build_2x2_forecast_figure(results, n_steps=5, is_deep=True)
        if deep_2x2_fig is not None:
            deep_img_bytes = _figure_to_bytes(deep_2x2_fig)
            _add_figure(
                document,
                deep_img_bytes,
                "Figure: Multi-season (2x2) continuous groundwater forecasts across all four seasons for the Deep Learning & Physics-Informed model family (PINN, ESN, SARIMA, LSTM).",
            )
    except Exception:
        pass

    document.add_heading("10. Key Scientific Findings", level=1)
    document.add_paragraph(
        "Findings below are limited to results directly stored by this analysis; they "
        "describe model fit and predictor association, not causal groundwater processes."
    )
    for season, result in results.items():
        metrics = result.get("metrics")
        if isinstance(metrics, pd.DataFrame) and not metrics.empty:
            best = metrics.iloc[0]
            observed = result.get("predictions")
            observed_summary = ""
            if isinstance(observed, pd.DataFrame) and "Actual DTWL (mbgl)" in observed:
                observed_values = pd.to_numeric(
                    observed["Actual DTWL (mbgl)"], errors="coerce"
                ).dropna()
                if not observed_values.empty:
                    observed_summary = (
                        f" Observed held-out DTWL ranged from {observed_values.min()} to "
                        f"{observed_values.max()} mbgl (n={len(observed_values)})."
                    )
            _add_bullet(
                document,
                f"{season}: {best.get('Model', UNAVAILABLE)} ranked first by "
                f"bias-corrected test R² ({_text(best.get('Bias-corrected test R2'))}); "
                f"its test RMSE was {_text(best.get('Bias-corrected test RMSE'))} mbgl."
                f"{observed_summary}",
            )
            ranking = result.get("feature_ranking")
            if isinstance(ranking, pd.DataFrame) and "Feature" in ranking.columns:
                selected = ranking.loc[
                    ranking.get("Selected", pd.Series(False, index=ranking.index)).astype(bool),
                    "Feature",
                ].head(3).astype(str).tolist()
                if selected:
                    _add_bullet(
                        document,
                        f"{season}: selected predictor examples were {', '.join(selected)}; "
                        "their statistical selection does not show causation.",
                    )
        else:
            _add_bullet(document, f"{season}: model metrics {UNAVAILABLE}")
        if result.get("low_data_rescue_used"):
            _add_bullet(
                document,
                f"{season}: the low-data rescue was used; missing engineered lag/rolling/trend "
                "values were imputed within village after the strict split was insufficient.",
            )
        elif result.get("low_data_rescue_used") is False:
            _add_bullet(document, f"{season}: the low-data rescue was not used.")
        else:
            _add_bullet(document, f"{season}: low-data rescue status {UNAVAILABLE}")

    document.add_heading("11. Limitations", level=1)
    for limitation in (
        "Model skill depends on the uploaded workbook's completeness, spatial coverage, and time span.",
        "A temporal holdout is needed for an independent estimate of future-period performance; a small-data fallback may not provide one.",
        "Feature ranking and leave-one-feature-out sensitivity do not establish causation.",
        "Recursive forecasts hold non-target predictors at the latest reference state while updating DTWL history, so they are conditional scenarios rather than complete hydrological simulations.",
        "The Digital Twin's terrain is conceptual and its slider-based simulation is visual only.",
        "Unavailable optional models or diagnostics are not replaced with estimated or fabricated results.",
    ):
        _add_bullet(document, limitation)

    document.add_heading("12. Technical Details and Season Outputs", level=1)
    document.add_paragraph(
        "The following retains the technical model outputs and settings available in the "
        "current analysis. Full tabular result sets are also included in the existing Excel export."
    )
    for season, result in results.items():
        _append_season_results(document, str(season), result)
        document.add_heading(f"{season}: Technical configuration", level=3)
        document.add_paragraph(
            "Derived features: "
            + (
                ", ".join(map(str, result.get("derived_features", [])))
                if result.get("derived_features")
                else UNAVAILABLE
            )
        )
        feature_groups = result.get("feature_groups")
        if isinstance(feature_groups, dict):
            for group_name in ("lag", "rolling", "trend"):
                values = feature_groups.get(group_name, [])
                document.add_paragraph(
                    f"{group_name.title()} features: "
                    + (", ".join(map(str, values)) if values else UNAVAILABLE)
                )
        else:
            document.add_paragraph(f"Engineered feature groups: {UNAVAILABLE}")
        _add_table(document, result.get("parameters"), title="Recorded model parameters")
        _add_table(document, result.get("availability"), title="Headline model availability")
        _add_table(document, result.get("deep_availability"), title="Deep model availability")
        errors = result.get("model_errors")
        deep_errors = result.get("deep_model_errors")
        for label, error_values in (("Headline model errors", errors), ("Deep model errors", deep_errors)):
            if isinstance(error_values, (list, tuple)) and error_values:
                document.add_paragraph(f"{label}:")
                for error in error_values:
                    _add_bullet(document, str(error))
            elif error_values is None:
                document.add_paragraph(f"{label}: {UNAVAILABLE}")
            else:
                document.add_paragraph(f"{label}: none recorded.")

    output = BytesIO()
    document.save(output)
    return output.getvalue()
