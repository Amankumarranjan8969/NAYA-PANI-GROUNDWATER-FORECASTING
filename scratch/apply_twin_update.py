"""Safely apply the 50 km Regional Three.js Digital Twin upgrade to digital_twin.py."""
import os
import shutil
import py_compile
import subprocess
from pathlib import Path
from scratch.generate_twin import build_threejs_template

ROOT = Path(r"D:\NIH_roorkee\FULL WORK FINAL_DIGITAL_NAYA_PANI\NAYA_PAANI")
TWIN_PY = ROOT / "digital_twin.py"
BACKUP_PY = ROOT / "digital_twin.py.bak"

def apply_update():
    print(f"Backing up {TWIN_PY} -> {BACKUP_PY}...")
    shutil.copy2(TWIN_PY, BACKUP_PY)

    with open(TWIN_PY, "r", encoding="utf-8") as f:
        content = f.read()

    template_code = build_threejs_template()

    # New implementation of _get_threejs_regional_template and _render_threejs_desert_twin
    new_code = '''def _get_threejs_regional_template() -> str:
    """Return the raw Three.js 50 km Regional Environmental & Hydrological Digital Twin HTML/JS template."""
    return r"""''' + template_code + '''"""


def _render_threejs_desert_twin(
    season: str,
    year: int,
    district: str,
    block: str,
    selected_village: str,
    mode: str,
    state: dict[str, float | None],
    asset_info: dict[str, Any],
    asset_catalog: pd.DataFrame | None = None,
    initial_preset: str = "📐 Elevated Isometric View (Default)",
    initial_cutaway: str = "Complete Surface Landscape",
    initial_exaggeration: float = 1.5,
    initial_ambiance: str = "☀️ High Noon Thar Sun",
) -> None:
    """Render a photorealistic, real-time interactive 3D WebGL 50 km Regional Hydrological Digital Twin via Three.js.

    Architectural Systems:
    - 50 km Radius Regional Multi-Scale Georeferenced Landscape (150-unit world radius, ~7,854 km² circular coverage)
    - Realistic regional geomorphology: Aravalli metamorphic strike ridges, central alluvial pediments, Thar aeolian dunefields
    - Dynamic flowing Luni river network (Saraswati/Sagarmati confluence to SW) with animated normal ripples and concrete girder bridge
    - Populated Rajasthani rural settlements (Govindgarh, Pushkar, Pisangan, Srinagar, Saradhna) with stepwells (Baori), Chhatris, and Kunds
    - Agricultural cadastral field mosaic with solar tube-well pump houses and South-facing solar PV pumping arrays
    - Natural xerophytic flora: Instanced Khejri trees (Prosopis cineraria), Rohida (Tecomella undulata), and Sewan grass (Lasiurus scindicus)
    - 6-Layer Subsurface 3D Geological Stratigraphy Block (Topsoil, Vadose Murrum, Fractured Quartzite, Luni Aquifer, Aquitard, Malani Granite Basement)
    - 400 Animated 3D Darcy Flow Particles tracking regional groundwater hydraulic gradient from NE to SW
    - Real WGS84 Monitoring Wells with borehole casings, telemetry masts, status-coded beacons, and click-to-inspect raycaster
    - Elevated Isometric Camera default (~35° downward pitch) + 10 smooth camera presets, rotating compass rose, scale bar, and GPS inspector
    - Dynamic atmosphere: PCF soft shadows, 4 ambiance modes (Day, Sunset, Night, Monsoon Storm), drifting cloud shadows, and rain simulation
    """
    dtwl_val = float(state.get("dtwl") or 15.0)
    rain_val = float(state.get("rainfall") or 0.0)
    et_val = float(state.get("et") or 0.0)
    soil_val = float(state.get("soil") or 14.0)
    stress_cat = (asset_info.get("stress_status") or {}).get("category", "Safe")
    stress_color = (asset_info.get("stress_status") or {}).get("color", "#10b981")
    well_name = str(asset_info.get("name", "Basin Wellhead"))
    well_lat = float(asset_info.get("latitude") or 26.45)
    well_lon = float(asset_info.get("longitude") or 74.63)
    well_elev = float(asset_info.get("elevation_m") or 480.0)

    # Format all well records from asset_catalog for the Three.js scene
    well_records: list[dict[str, Any]] = []
    if asset_catalog is not None and not asset_catalog.empty:
        for _, r in asset_catalog.iterrows():
            v_name = str(r.get("Village", "Well"))
            well_records.append({
                "village": v_name,
                "district": str(r.get("District", district)),
                "block": str(r.get("Block", block)),
                "lat": float(r.get("Latitude") or well_lat),
                "lon": float(r.get("Longitude") or well_lon),
                "elev": float(r.get("Elevation_m") or well_elev),
                "dtwl": float(r.get("DTWL_mbgl") or dtwl_val),
                "stress": str(r.get("Stress_Category", "Safe")),
                "color": str(r.get("Stress_Color", "#10b981")),
                "trend": float(r.get("Trend_Slope_mbgl_yr") or 0.0),
                "obsCount": int(r.get("Observation_Count") or 12),
                "minDtwl": float(r.get("Min_DTWL_mbgl") or (dtwl_val - 4.0)),
                "maxDtwl": float(r.get("Max_DTWL_mbgl") or (dtwl_val + 6.0)),
                "meanDtwl": float(r.get("Mean_DTWL_mbgl") or dtwl_val),
                "isSelected": (v_name == selected_village),
            })

    config_json = json.dumps({
        "season": season,
        "year": year,
        "district": district,
        "block": block,
        "selectedVillage": well_name,
        "mode": mode,
        "dtwl": round(dtwl_val, 2),
        "rainfall": round(rain_val, 1),
        "et": round(et_val, 1),
        "soil": round(soil_val, 1),
        "stressCat": stress_cat,
        "stressColor": stress_color,
        "lat": round(well_lat, 4),
        "lon": round(well_lon, 4),
        "elev": round(well_elev, 1),
        "wells": well_records,
        "initialPreset": initial_preset,
        "initialCutaway": initial_cutaway,
        "initialExaggeration": float(initial_exaggeration),
        "initialAmbiance": initial_ambiance,
    })

    raw_template = _get_threejs_regional_template()
    replacements = {
        "__CONFIG_JSON__": config_json,
        "__STRESS_COLOR__": stress_color,
        "__STRESS_CAT__": stress_cat,
        "__WELL_NAME__": well_name,
        "__DISTRICT__": district,
        "__BLOCK__": block,
        "__WELL_LAT__": f"{well_lat:.4f}",
        "__WELL_LON__": f"{well_lon:.4f}",
        "__WELL_ELEV__": f"{well_elev:.1f}",
        "__MODE__": mode,
        "__DTWL_VAL__": f"{dtwl_val:.2f}",
        "__WT_ELEV__": f"{(well_elev - dtwl_val):.1f}",
        "__EXAGGERATION__": f"{float(initial_exaggeration):.1f}",
    }
    rendered_html = raw_template
    for k, v in replacements.items():
        rendered_html = rendered_html.replace(k, str(v))

    components.html(rendered_html, height=760)'''

    # Find start and end markers
    if "def _get_threejs_regional_template()" in content:
        start_idx = content.find("def _get_threejs_regional_template()")
    else:
        start_idx = content.find("def _render_threejs_desert_twin(")
    assert start_idx != -1, "Could not find start marker in digital_twin.py"

    if "components.html(rendered_html, height=760)" in content:
        end_marker = "components.html(rendered_html, height=760)"
    else:
        end_marker = "components.html(threejs_html, height=720)"
    end_idx = content.find(end_marker)
    assert end_idx != -1, f"Could not find end marker {end_marker} in digital_twin.py"
    end_idx += len(end_marker)

    updated_content = content[:start_idx] + new_code + content[end_idx:]

    with open(TWIN_PY, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("Updated digital_twin.py successfully!")

    # Verify python syntax
    try:
        py_compile.compile(str(TWIN_PY), doraise=True)
        print("[SUCCESS] Python syntax compilation passed for updated digital_twin.py!")
    except Exception as e:
        print("[ERROR] Syntax error in updated file! Restoring backup...")
        shutil.copy2(BACKUP_PY, TWIN_PY)
        raise e

if __name__ == "__main__":
    apply_update()
