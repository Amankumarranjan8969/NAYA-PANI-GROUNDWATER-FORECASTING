import pathlib
import shutil
import streamlit

root = pathlib.Path(__file__).resolve().parent.parent
st_static = pathlib.Path(streamlit.__file__).parent / "static"
idx = st_static / "index.html"
bak = st_static / "index.html.bak"

if not bak.exists():
    shutil.copy2(idx, bak)

shutil.copy2(root / "static" / "manifest.json", st_static / "nayapani_manifest.json")
shutil.copy2(root / "static" / "service_worker.js", st_static / "service_worker.js")
shutil.copy2(root / "static" / "nayapani-icon-192.png", st_static / "nayapani-icon-192.png")
shutil.copy2(root / "static" / "nayapani-icon-512.png", st_static / "nayapani-icon-512.png")
shutil.copy2(root / "static" / "nayapani-icon-192.png", st_static / "icon-192.png")
shutil.copy2(root / "static" / "nayapani-icon-512.png", st_static / "icon-512.png")
shutil.copy2(root / "static" / "favicon.ico", st_static / "favicon.ico")

html = bak.read_text(encoding="utf-8")
old_fav = '<link rel="shortcut icon" href="./favicon.png" />'
new_tags = (
    '<link rel="shortcut icon" href="./nayapani-icon-192.png?v=4" />\n'
    '    <link rel="icon" type="image/png" href="./nayapani-icon-192.png?v=4" />\n'
    '    <link rel="apple-touch-icon" href="./nayapani-icon-192.png?v=4" />\n'
    '    <link rel="manifest" href="./nayapani_manifest.json?v=4" />'
)
html = html.replace(old_fav, new_tags)
html = html.replace("<title>Streamlit</title>", "<title>NAYA-PANI — Groundwater Intelligence</title>")
idx.write_text(html, encoding="utf-8")
print("SUCCESS: Synced all Naya Pani icons and manifest to Streamlit static distribution!")
