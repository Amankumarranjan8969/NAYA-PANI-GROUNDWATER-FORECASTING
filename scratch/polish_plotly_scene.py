"""Polish Plotly _scene in digital_twin.py with dark theme, clean legend, and no clumsy lollipops."""
from pathlib import Path
import py_compile

TWIN_PY = Path(r"D:\NIH_roorkee\FULL WORK FINAL_DIGITAL_NAYA_PANI\NAYA_PAANI\digital_twin.py")

with open(TWIN_PY, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'paper_bg = "rgba(254, 243, 224, 0.98)"' in line or 'paper_bg = "rgba(255, 251, 245, 0.98)"' in line:
        new_lines.append('        paper_bg = "#070b14"\n')
    elif 'paper_bg = "#090d16"' in line:
        new_lines.append('        paper_bg = "#070b14"\n')
    elif 'fig.update_layout(' in line and 'digital_twin' in lines[i+1]:
        # Replace the entire update_layout block
        layout_block = """    fig.update_layout(
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
            font=dict(color="#cbd5e1", size=10.5),
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
    )
"""
        new_lines.append(layout_block)
        # Advance until `return fig`
        while i < len(lines) and 'return fig' not in lines[i]:
            i += 1
        new_lines.append(lines[i]) # return fig
    elif '# Khejri Desert Trunks' in line:
        # Skip the trunk trace that caused the 2D square lollipop
        while i < len(lines) and ')' not in lines[i]:
            i += 1
        if i < len(lines) and lines[i].strip() == ')':
            i += 1
        if i < len(lines) and lines[i].strip() == ')':
            i += 1
    elif 'size=7.5, color="#3f6212"' in line:
        # Refine tree marker size to a clean point
        new_lines.append(line.replace('size=7.5', 'size=3.8'))
    elif 'name="☀️ Desert Solar Forcing"' in line:
        # Make the sun marker subtle
        new_lines.append('                showlegend=False,\n')
    else:
        new_lines.append(line)
    i += 1

with open(TWIN_PY, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Updated _scene in digital_twin.py successfully!")
py_compile.compile(str(TWIN_PY), doraise=True)
print("Syntax compilation passed!")
