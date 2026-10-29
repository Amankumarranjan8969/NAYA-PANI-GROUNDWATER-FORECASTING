"""Apply the complete photorealistic transformation to digital_twin.py."""
import shutil
import py_compile
from pathlib import Path

ROOT = Path(r"D:\NIH_roorkee\FULL WORK FINAL_DIGITAL_NAYA_PANI\NAYA_PAANI")
TWIN_PY = ROOT / "digital_twin.py"
BACKUP_PY = ROOT / "digital_twin.py.bak_clean"

shutil.copy2(TWIN_PY, BACKUP_PY)

with open(TWIN_PY, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update Plotly _scene layout and dark styling
text = text.replace('paper_bg = "rgba(254, 243, 224, 0.98)"', 'paper_bg = "#070b14"')
text = text.replace('paper_bg = "rgba(255, 251, 245, 0.98)"', 'paper_bg = "#070b14"')
text = text.replace('paper_bg = "#090d16"', 'paper_bg = "#070b14"')

old_layout = '''    fig.update_layout(
        meta={"digital_twin": True},
        paper_bgcolor=paper_bg,
        plot_bgcolor=paper_bg,
        height=620,
        margin=dict(l=0, r=0, t=28, b=0),
        font=dict(color="#1E293B", family="Inter, sans-serif", size=12.5),
        legend=dict(
            bgcolor="rgba(255,255,255,0.85)",
            orientation="h",
            y=1.03,
            font=dict(color="#1E293B", size=11.5),
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#0F172A",
            font=dict(color="#0F172A", family="Inter, sans-serif", size=12.5),
        ),
        scene=dict(
            bgcolor=paper_bg,
            aspectmode="cube",
            camera=cam_cfg,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
        ),
    )'''

new_layout = '''    fig.update_layout(
        meta={"digital_twin": True},
        paper_bgcolor="#070b14",
        plot_bgcolor="#070b14",
        height=640,
        margin=dict(l=0, r=0, t=10, b=10),
        font=dict(color="#f8fafc", family="Inter, sans-serif", size=11.5),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.88)",
            orientation="h",
            y=-0.04,
            font=dict(color="#cbd5e1", size=10),
            bordercolor="rgba(255,255,255,0.15)",
            borderwidth=1,
        ),
        hoverlabel=dict(
            bgcolor="#0f172a",
            bordercolor="#38bdf8",
            font=dict(color="#f8fafc", family="Inter, sans-serif", size=11.5),
        ),
        scene=dict(
            bgcolor="#070b14",
            aspectmode="cube",
            camera=cam_cfg,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
        ),
    )'''

if old_layout in text:
    text = text.replace(old_layout, new_layout)
    print("Replaced Plotly layout!")
else:
    print("Warning: old_layout not found exactly, checking CRLF...")
    old_layout_crlf = old_layout.replace("\n", "\r\n")
    if old_layout_crlf in text:
        text = text.replace(old_layout_crlf, new_layout.replace("\n", "\r\n"))
        print("Replaced Plotly layout (CRLF)!")

# Refine lollipop trees in Plotly
text = text.replace('marker=dict(size=7.5, color="#3f6212", symbol="circle", opacity=0.92)', 'marker=dict(size=3.5, color="#4d7c0f", symbol="circle", opacity=0.85)')
text = text.replace('marker=dict(size=3.5, color="#78350f", symbol="square", opacity=0.85)', 'marker=dict(size=2.0, color="#78350f", symbol="square", opacity=0.6), showlegend=False')
text = text.replace('name="☀️ Desert Solar Forcing",', 'name="☀️ Desert Solar Forcing",\n                showlegend=False,')

# 2. Update Three.js template with v4 photoreal engine
with open(ROOT / "scratch" / "prototype_v4.html", "r", encoding="utf-8") as f:
    v4_html = f.read()

v4_html = v4_html.replace("Govindgarh Wellhead", "__WELL_NAME__")
v4_html = v4_html.replace("Ajmer (Pisangan)", "__DISTRICT__ (__BLOCK__)")
v4_html = v4_html.replace("26.4600°N, 74.5200°E", "__WELL_LAT__°N, __WELL_LON__°E")
v4_html = v4_html.replace("462.0 m ASL", "__WELL_ELEV__ m ASL")
v4_html = v4_html.replace("7.94 mbgl", "__DTWL_VAL__ mbgl")
v4_html = v4_html.replace("454.1 m ASL", "__WT_ELEV__ m ASL")

new_threejs_block = '''def _get_threejs_regional_template() -> str:
    """Return the photorealistic Three.js 50 km Regional Environmental & Hydrological Digital Twin HTML/JS template."""
    return r"""''' + v4_html + '''"""'''

start_marker = "def _get_threejs_regional_template()"
end_marker = 'return r"""'
idx_start = text.find(start_marker)
assert idx_start != -1, "Could not find _get_threejs_regional_template"
idx_func_end = text.find("def _render_threejs_desert_twin(", idx_start)
assert idx_func_end != -1, "Could not find _render_threejs_desert_twin"

text = text[:idx_start] + new_threejs_block + "\n\n\n" + text[idx_func_end:]

with open(TWIN_PY, "w", encoding="utf-8") as f:
    f.write(text)

print("Saved updated digital_twin.py!")
py_compile.compile(str(TWIN_PY), doraise=True)
print("Syntax compilation passed successfully!")
