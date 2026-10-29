import json
import os
import re

static_dir = r"D:\NIH_roorkee\FULL WORK FINAL_DIGITAL_NAYA_PANI\NAYA_PAANI\static"
with open(os.path.join(static_dir, "elevation_luni_50km.json"), "r") as fp:
    dem = json.load(fp)

elev_compact = [[round(y, 1) for y in row] for row in dem["elevations"]]
dem_json_str = json.dumps({
    "grid_size": dem["grid_size"],
    "min_elev": dem["min_elev"],
    "max_elev": dem["max_elev"],
    "elevations": elev_compact
})

template_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Naya Pani - Photorealistic 50 km Regional Digital Twin</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body, html {{ width: 100%; height: 100%; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #070b14; color: #f8fafc; }}
    #desert-canvas-wrap {{ position: relative; width: 100%; height: 760px; overflow: hidden; background: #070b14; user-select: none; }}
    #three-canvas {{ width: 100%; height: 100%; display: block; }}

    /* Top Camera Toolbar */
    .top-toolbar {{ position: absolute; top: 10px; left: 12px; right: 12px; display: flex; align-items: center; justify-content: space-between; gap: 8px; z-index: 20; pointer-events: none; }}
    .preset-bar {{ display: flex; align-items: center; gap: 4px; background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(12px); padding: 5px 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.18); pointer-events: auto; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }}
    .preset-btn {{ background: transparent; border: 1px solid transparent; color: #cbd5e1; padding: 5px 9px; border-radius: 6px; font-size: 11px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 4px; transition: all 0.2s; }}
    .preset-btn:hover {{ background: rgba(255,255,255,0.1); color: #fff; }}
    .preset-btn.active {{ background: #d97706; color: #fff; border-color: #f59e0b; font-weight: 600; box-shadow: 0 2px 10px rgba(217,119,6,0.4); }}

    .top-actions {{ display: flex; align-items: center; gap: 5px; pointer-events: auto; }}
    .action-btn {{ background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.18); color: #cbd5e1; padding: 5px 9px; border-radius: 6px; font-size: 11px; font-weight: 500; cursor: pointer; transition: all 0.2s; }}
    .action-btn:hover {{ background: #334155; color: #fff; }}
    .action-btn.active {{ background: #d97706; color: #fff; border-color: #f59e0b; }}
    .action-btn.rain-active {{ background: #0284c7; color: #fff; border-color: #38bdf8; box-shadow: 0 0 12px rgba(2,132,199,0.6); }}

    /* Layer Drawer */
    .layer-drawer-btn {{ position: absolute; top: 54px; left: 12px; z-index: 15; background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.18); color: #f8fafc; padding: 6px 11px; border-radius: 6px; font-size: 11.5px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }}
    .layer-panel {{ position: absolute; top: 88px; left: 12px; width: 240px; background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(14px); border: 1px solid rgba(255,255,255,0.18); border-radius: 10px; padding: 10px 12px; z-index: 15; display: none; box-shadow: 0 10px 28px rgba(0,0,0,0.6); }}
    .layer-panel.open {{ display: block; }}
    .layer-panel-title {{ font-size: 11px; font-weight: 700; color: #f59e0b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }}
    .layer-item {{ display: flex; align-items: center; justify-content: space-between; font-size: 11.5px; color: #cbd5e1; margin-bottom: 6px; cursor: pointer; }}
    .layer-item input {{ cursor: pointer; accent-color: #d97706; }}

    /* Bottom-Left Scientific Sliders */
    .controls-panel {{ position: absolute; bottom: 12px; left: 12px; background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.18); border-radius: 10px; padding: 10px 14px; z-index: 15; min-width: 250px; box-shadow: 0 6px 20px rgba(0,0,0,0.5); }}
    .control-row {{ display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 6px; font-size: 11.5px; color: #cbd5e1; }}
    .control-row:last-child {{ margin-bottom: 0; }}
    .control-row label {{ font-weight: 500; display: flex; align-items: center; gap: 5px; }}
    .control-row input[type=range] {{ width: 110px; accent-color: #d97706; cursor: pointer; }}
    .val-badge {{ font-size: 10.5px; font-weight: 600; color: #f59e0b; min-width: 32px; text-align: right; }}

    /* Floating Scientific Inspection Card */
    .well-card {{ position: absolute; top: 54px; right: 12px; width: 330px; background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(14px); border: 1px solid rgba(255,255,255,0.22); border-radius: 12px; padding: 12px 14px; z-index: 25; display: block; box-shadow: 0 12px 32px rgba(0,0,0,0.6); animation: cardIn 0.25s ease-out; }}
    @keyframes cardIn {{ from {{ opacity: 0; transform: translateY(-8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .well-card-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }}
    .well-card-cat {{ font-size: 10px; font-weight: 700; color: #f59e0b; text-transform: uppercase; letter-spacing: 0.05em; }}
    .well-card-status {{ font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px; text-transform: uppercase; }}
    .status-safe {{ background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }}
    .status-semi {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }}
    .status-critical {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; }}
    .well-card-name {{ font-size: 14.5px; font-weight: 700; color: #ffffff; margin-bottom: 8px; }}
    .well-card-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 11px; margin-bottom: 8px; }}
    .card-metric {{ background: rgba(30, 41, 59, 0.6); padding: 5px 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.06); }}
    .card-lbl {{ color: #94a3b8; font-size: 10px; margin-bottom: 2px; }}
    .card-val {{ color: #f8fafc; font-weight: 600; }}
    .well-card-close {{ position: absolute; top: 10px; right: 10px; background: transparent; border: none; color: #94a3b8; font-size: 16px; cursor: pointer; padding: 2px 6px; border-radius: 4px; }}
    .well-card-close:hover {{ color: #fff; background: rgba(255,255,255,0.1); }}

    /* Rain Simulation Banner */
    .rain-banner {{ position: absolute; bottom: 12px; right: 12px; background: rgba(2, 132, 199, 0.90); backdrop-filter: blur(12px); border: 1px solid #38bdf8; border-radius: 8px; padding: 8px 12px; font-size: 11.5px; color: #fff; display: none; align-items: center; gap: 8px; z-index: 15; box-shadow: 0 4px 16px rgba(2,132,199,0.4); }}
    .rain-pulse {{ width: 8px; height: 8px; border-radius: 50%; background: #38bdf8; animation: pulse 1s infinite alternate; }}
    @keyframes pulse {{ from {{ opacity: 0.4; transform: scale(0.8); }} to {{ opacity: 1; transform: scale(1.2); }} }}
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/MTLLoader.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/OBJLoader.js"></script>
</head>
<body>
<div id="desert-canvas-wrap">
  <canvas id="three-canvas"></canvas>

  <!-- Top Camera Toolbar -->
  <div class="top-toolbar">
    <div class="preset-bar">
      <button class="preset-btn active" id="btn-iso" onclick="applyCameraPreset('iso')">📐 Elevated Panoramic</button>
      <button class="preset-btn" id="btn-basin" onclick="applyCameraPreset('basin')">🌐 50 km Basin</button>
      <button class="preset-btn" id="btn-top" onclick="applyCameraPreset('top')">🛰️ Top-Down GIS</button>
      <button class="preset-btn" id="btn-oblique" onclick="applyCameraPreset('oblique')">🌄 Low Oblique</button>
      <button class="preset-btn" id="btn-cutaway" onclick="applyCameraPreset('cutaway')">⛏️ Subsurface</button>
      <button class="preset-btn" id="btn-settle" onclick="applyCameraPreset('settle')">🏘️ Settlements</button>
      <button class="preset-btn" id="btn-river" onclick="applyCameraPreset('river')">🌊 Luni River</button>
    </div>
    <div class="top-actions">
      <button class="action-btn" id="btn-rain" onclick="toggleRainSimulation()">🌧️ Rain Simulation</button>
      <button class="action-btn active" id="btn-day" onclick="applyLightingPreset('day')">☀️ Day</button>
      <button class="action-btn" id="btn-sunset" onclick="applyLightingPreset('sunset')">🌅 Sunset</button>
      <button class="action-btn" id="btn-night" onclick="applyLightingPreset('night')">🌌 Night</button>
    </div>
  </div>

  <!-- Layer Drawer Button & Panel -->
  <button class="layer-drawer-btn" onclick="toggleLayerPanel()">⚙️ Scene Layers</button>
  <div class="layer-panel" id="layer-panel">
    <div class="layer-panel-title">Geospatial Layers</div>
    <label class="layer-item"><input type="checkbox" id="layer-terrain" checked onchange="toggleLayer('terrain')"> <span>Realistic 3D Terrain</span></label>
    <label class="layer-item"><input type="checkbox" id="layer-satellite" checked onchange="toggleLayer('satellite')"> <span>Satellite Orthophoto</span></label>
    <label class="layer-item"><input type="checkbox" id="layer-river" checked onchange="toggleLayer('river')"> <span>Living Luni River</span></label>
    <label class="layer-item"><input type="checkbox" id="layer-settlements" checked onchange="toggleLayer('settlements')"> <span>Rajasthani Settlements</span></label>
    <label class="layer-item"><input type="checkbox" id="layer-trees" checked onchange="toggleLayer('trees')"> <span>3D Realistic Trees</span></label>
    <label class="layer-item"><input type="checkbox" id="layer-grass" checked onchange="toggleLayer('grass')"> <span>3D Grass Cover</span></label>
    <label class="layer-item"><input type="checkbox" id="layer-activity" checked onchange="toggleLayer('activity')"> <span>Vehicles, Camels & Life</span></label>
    <label class="layer-item"><input type="checkbox" id="layer-wells" checked onchange="toggleLayer('wells')"> <span>CGWB Monitoring Wells</span></label>
    <label class="layer-item"><input type="checkbox" id="layer-flow" checked onchange="toggleLayer('flow')"> <span>Groundwater Flow Lines</span></label>
    <label class="layer-item"><input type="checkbox" id="layer-strata" checked onchange="toggleLayer('strata')"> <span>Subsurface Stratigraphy</span></label>
  </div>

  <!-- Bottom-Left Scientific Sliders -->
  <div class="controls-panel">
    <div class="control-row">
      <label>⛏️ Subsurface Cutaway:</label>
      <input type="range" id="slice-slider" min="0" max="100" value="0" oninput="updateSlice(this.value)">
      <span class="val-badge" id="slice-val">0%</span>
    </div>
    <div class="control-row">
      <label>🏔️ Vert. Exaggeration:</label>
      <input type="range" id="exaggeration-slider" min="0.5" max="3.0" step="0.1" value="__EXAGGERATION__" oninput="updateExaggeration(this.value)">
      <span class="val-badge" id="exag-val">__EXAGGERATION__x</span>
    </div>
    <div class="control-row">
      <label>💧 Water Table Level:</label>
      <input type="range" id="water-slider" min="-5.0" max="3.0" step="0.2" value="0.0" oninput="updateWaterTable(this.value)">
      <span class="val-badge" id="water-val">0.0m</span>
    </div>
  </div>

  <!-- Rain Banner -->
  <div class="rain-banner" id="rain-banner">
    <div class="rain-pulse"></div>
    <span>Monsoon Active: 48 mm/hr | Aquifer Recharge: +1.12 mm/day</span>
  </div>

  <!-- Floating Scientific Well Inspection Card -->
  <div class="well-card" id="well-card">
    <button class="well-card-close" onclick="closeWellCard()">✕</button>
    <div class="well-card-header">
      <span class="well-card-cat" id="wc-cat">CGWB Telemetry Piezometer</span>
      <span class="well-card-status status-safe" id="wc-badge">__STRESS_CAT__</span>
    </div>
    <div class="well-card-name" id="wc-name">__WELL_NAME__</div>
    <div class="well-card-grid">
      <div class="card-metric"><div class="card-lbl">District / Block</div><div class="card-val" id="wc-block">__DISTRICT__ (__BLOCK__)</div></div>
      <div class="card-metric"><div class="card-lbl">WGS84 Coordinates</div><div class="card-val" id="wc-coords">__WELL_LAT__°N, __WELL_LON__°E</div></div>
      <div class="card-metric"><div class="card-lbl">Surface Elevation</div><div class="card-val" id="wc-elev">__WELL_ELEV__ m ASL</div></div>
      <div class="card-metric"><div class="card-lbl">Active DTWL</div><div class="card-val" style="color:#38bdf8;" id="wc-dtwl">__DTWL_VAL__ mbgl</div></div>
      <div class="card-metric"><div class="card-lbl">Water Table Elev.</div><div class="card-val" id="wc-wtelev">__WT_ELEV__ m ASL</div></div>
      <div class="card-metric"><div class="card-lbl">Regional Aquifer</div><div class="card-val" id="wc-aquifer">Luni Alluvial Semi-Confined</div></div>
    </div>
    <div style="font-size: 10px; color: #94a3b8; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 5px;">
      Verified Historical CGWB Observation · SimReady OpenUSD Asset
    </div>
  </div>
</div>

<script>
    // Embedded Real Geospatial DEM Data (NASA/SRTM 50 km coverage)
    const REAL_DEM_DATA = {dem_json_str};

    // Global Scene Declarations
    let scene, camera, renderer, controls;
    let terrainMesh, terrainGeom, baseHeights = [];
    let waterMesh, vadoseMesh, fracturedMesh, aquitardMesh, bedrockMesh;
    let clipPlaneX;
    let flowParticles, cloudGroup, rainParticles;
    let wellGroup, settlementGroup, treeGroup, grassGroup, riverWaterMesh, lakeGroup, activityGroup;
    let riverFoamParticles, riverCurve;
    let movingVehicles = [];
    let isRaining = false;
    let currentExag = parseFloat('__EXAGGERATION__') || 1.15;
    let baseWaterY = -2.5;

    // Sinuous Luni River Path: flows through flat valley from Pushkar down to SW plains
    function getRiverZ(x) {{
      return 5.5 * Math.sin(x * 0.038) - 0.20 * x + 4.0;
    }}

    // Accurate Bilinear Interpolation from Real DEM Data
    function getRegionalElevation(x, z) {{
      const grid = REAL_DEM_DATA.elevations;
      const n = REAL_DEM_DATA.grid_size;
      const minE = REAL_DEM_DATA.min_elev;
      const maxE = REAL_DEM_DATA.max_elev;

      const fj = Math.max(0, Math.min(n - 1, ((x + 80.0) / 160.0) * (n - 1)));
      const fi = Math.max(0, Math.min(n - 1, ((z + 80.0) / 160.0) * (n - 1)));

      const j0 = Math.floor(fj), j1 = Math.min(n - 1, j0 + 1);
      const i0 = Math.floor(fi), i1 = Math.min(n - 1, i0 + 1);
      const dj = fj - j0;
      const di = fi - i0;

      const e00 = grid[i0][j0], e01 = grid[i0][j1];
      const e10 = grid[i1][j0], e11 = grid[i1][j1];

      const elevM = (e00 * (1 - dj) + e01 * dj) * (1 - di) + (e10 * (1 - dj) + e11 * dj) * di;
      const relH = (elevM - minE) / (maxE - minE);

      const yWorld = (relH * 7.5 - 1.2) * currentExag;
      return yWorld;
    }}

    // Procedural Fallback Texture
    function createProceduralFallbackTexture() {{
      const size = 1024;
      const canvas = document.createElement('canvas');
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext('2d');

      ctx.fillStyle = '#caa373';
      ctx.fillRect(0, 0, size, size);

      for (let y = 0; y < size; y += 16) {{
        for (let x = 0; x < size; x += 16) {{
          const wx = (x / size) * 160 - 80;
          const wz = (y / size) * 160 - 80;
          if (wx > 10) {{
            ctx.fillStyle = (Math.random() > 0.5) ? '#846e58' : '#967d64';
          }} else if (Math.abs(wz - getRiverZ(wx)) < 4.5) {{
            ctx.fillStyle = '#e4d0b0';
          }} else if (wx < -15) {{
            ctx.fillStyle = '#dca864';
          }} else {{
            const pType = Math.floor(Math.sin(wx * 2.1 + wz * 1.8) * 100) % 4;
            ctx.fillStyle = (pType === 0) ? '#386638' : (pType === 1) ? '#5a823c' : (pType === 2) ? '#b08a46' : '#9c7343';
          }}
          ctx.fillRect(x, y, 16, 16);
        }}
      }}
      return new THREE.CanvasTexture(canvas);
    }}

    // Dynamic Procedural Water Wave Ripple Texture
    function createWaterWaveTexture() {{
      const size = 512;
      const canvas = document.createElement('canvas');
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext('2d');

      ctx.fillStyle = '#8080ff';
      ctx.fillRect(0, 0, size, size);

      const img = ctx.getImageData(0, 0, size, size);
      const data = img.data;

      for (let y = 0; y < size; y++) {{
        for (let x = 0; x < size; x++) {{
          const wave1 = Math.sin(x * 0.08 + y * 0.04);
          const wave2 = Math.cos(x * 0.05 - y * 0.09);
          const wave3 = Math.sin((x + y) * 0.12);
          const total = (wave1 + wave2 + wave3) / 3.0;

          const nx = Math.floor((total * 0.4 + 0.5) * 255);
          const ny = Math.floor((Math.cos(x * 0.08) * 0.4 + 0.5) * 255);
          const idx = (y * size + x) * 4;
          data[idx] = nx;
          data[idx + 1] = ny;
          data[idx + 2] = 240;
          data[idx + 3] = 255;
        }}
      }}
      ctx.putImageData(img, 0, 0);
      const tex = new THREE.CanvasTexture(canvas);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;
      tex.repeat.set(4, 16);
      return tex;
    }}

    // Initialize Photorealistic Digital Twin
    function initEngine() {{
      const wrap = document.getElementById('desert-canvas-wrap');
      const canvas = document.getElementById('three-canvas');
      const w = wrap.clientWidth || 800;
      const h = wrap.clientHeight || 760;

      // 1. Scene & Atmosphere
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0xbbe5f8);
      scene.fog = new THREE.FogExp2(0xfef3c7, 0.0022);

      // Realistic Sky Dome
      const skyGeom = new THREE.SphereGeometry(320, 32, 16);
      const skyMat = new THREE.MeshBasicMaterial({{ color: 0x60a5fa, side: THREE.BackSide }});
      const sky = new THREE.Mesh(skyGeom, skyMat);
      scene.add(sky);

      // 2. Camera: Elevated Panoramic View
      camera = new THREE.PerspectiveCamera(38, w / h, 0.5, 800);
      camera.position.set(15, 62, 82);

      // 3. Renderer with ACES Tone Mapping & Soft Shadows
      renderer = new THREE.WebGLRenderer({{ canvas: canvas, antialias: true, powerPreference: 'high-performance' }});
      renderer.setSize(w, h);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.05;
      renderer.localClippingEnabled = true;

      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.maxPolarAngle = Math.PI / 2 - 0.02;
      controls.minDistance = 8;
      controls.maxDistance = 300;
      controls.target.set(-10, 0, -5);

      // 4. Directional Sunlight & Warm Desert Sky Fill
      const hemiLight = new THREE.HemisphereLight(0xffedd5, 0x78350f, 0.75);
      scene.add(hemiLight);

      const dirLight = new THREE.DirectionalLight(0xfff7ed, 1.45);
      dirLight.position.set(65, 85, 45);
      dirLight.castShadow = true;
      dirLight.shadow.mapSize.width = 2048;
      dirLight.shadow.mapSize.height = 2048;
      dirLight.shadow.camera.near = 10;
      dirLight.shadow.camera.far = 320;
      dirLight.shadow.camera.left = -95;
      dirLight.shadow.camera.right = 95;
      dirLight.shadow.camera.top = 95;
      dirLight.shadow.camera.bottom = -95;
      dirLight.shadow.bias = -0.0002;
      scene.add(dirLight);

      const sunGeom = new THREE.SphereGeometry(4.5, 16, 16);
      const sunMat = new THREE.MeshBasicMaterial({{ color: 0xfffbeb }});
      const sun = new THREE.Mesh(sunGeom, sunMat);
      sun.position.copy(dirLight.position);
      scene.add(sun);

      // 5. Geological Cutaway Clipping Plane
      clipPlaneX = new THREE.Plane(new THREE.Vector3(-1, 0, 0), 95.0);

      // 6. Terrain Mesh with Real DEM Vertices & Satellite Orthophoto
      const segs = 127;
      terrainGeom = new THREE.PlaneGeometry(160, 160, segs, segs);
      terrainGeom.rotateX(-Math.PI / 2);

      const pos = terrainGeom.attributes.position;
      baseHeights = new Float32Array(pos.count);
      for (let i = 0; i < pos.count; i++) {{
        const x = pos.getX(i);
        const z = pos.getZ(i);
        const y = getRegionalElevation(x, z);
        baseHeights[i] = y;
        pos.setY(i, y);
      }}
      terrainGeom.computeVertexNormals();

      // Load Real Satellite Orthophoto & Normal Map
      const texLoader = new THREE.TextureLoader();
      texLoader.setCrossOrigin('anonymous');
      const satUrl = (window.location.protocol === 'file:') ? '../static/satellite_luni_50km.jpg' : '/app/static/satellite_luni_50km.jpg';
      const normUrl = (window.location.protocol === 'file:') ? '../static/normal_luni_50km.jpg' : '/app/static/normal_luni_50km.jpg';

      const satTexture = texLoader.load(satUrl, (tex) => {{
        console.log('Satellite orthophoto loaded!');
        terrainMesh.material.map = tex;
        terrainMesh.material.needsUpdate = true;
      }}, undefined, (err) => {{
        console.warn('Fallback procedural satellite texture...', err);
        terrainMesh.material.map = createProceduralFallbackTexture();
        terrainMesh.material.needsUpdate = true;
      }});
      satTexture.anisotropy = 8;

      const normTexture = texLoader.load(normUrl, (tex) => {{
        console.log('Normal map loaded!');
        terrainMesh.material.normalMap = tex;
        terrainMesh.material.needsUpdate = true;
      }});
      normTexture.anisotropy = 8;

      const terrainMat = new THREE.MeshStandardMaterial({{
        map: satTexture,
        normalMap: normTexture,
        normalScale: new THREE.Vector2(1.5, 1.5),
        roughness: 0.86,
        metalness: 0.02,
        side: THREE.DoubleSide,
        clippingPlanes: [clipPlaneX],
        clipShadows: true,
      }});

      terrainMesh = new THREE.Mesh(terrainGeom, terrainMat);
      terrainMesh.receiveShadow = true;
      terrainMesh.castShadow = true;
      scene.add(terrainMesh);

      // 7. Surface Hydrology: Lakes & Living Flowing Luni River
      lakeGroup = new THREE.Group();
      scene.add(lakeGroup);

      const waterRippleTex = createWaterWaveTexture();

      const livingWaterMat = new THREE.MeshStandardMaterial({{
        color: 0x0284c7,
        roughness: 0.08,
        metalness: 0.75,
        normalMap: waterRippleTex,
        normalScale: new THREE.Vector2(1.2, 1.2),
        transparent: true,
        opacity: 0.85,
        side: THREE.DoubleSide,
      }});

      // Ana Sagar Lake (Ajmer)
      const anaGeom = new THREE.CylinderGeometry(5.2, 4.6, 0.35, 24);
      const anaLake = new THREE.Mesh(anaGeom, livingWaterMat);
      const anaY = getRegionalElevation(1.5, -0.5);
      anaLake.position.set(1.5, anaY + 0.10, -0.5);
      anaLake.scale.set(1.3, 1, 0.8);
      lakeGroup.add(anaLake);

      // Pushkar Sacred Lake
      const pushGeom = new THREE.CylinderGeometry(3.6, 3.2, 0.35, 20);
      const pushLake = new THREE.Mesh(pushGeom, livingWaterMat);
      const pushY = getRegionalElevation(6.0, 12.0);
      pushLake.position.set(6.0, pushY + 0.10, 12.0);
      pushLake.scale.set(1.1, 1, 0.7);
      lakeGroup.add(pushLake);

      // Sinuous Luni River Ribbon through Natural Valley
      const riverPts = [];
      for (let rx = -75; rx <= 10; rx += 2.5) {{
        const rz = getRiverZ(rx);
        const ry = getRegionalElevation(rx, rz) + 0.06;
        riverPts.push(new THREE.Vector3(rx, ry, rz));
      }}
      riverCurve = new THREE.CatmullRomCurve3(riverPts);

      const numPts = 90;
      const ribbonPts = riverCurve.getPoints(numPts);
      const riverGeom = new THREE.BufferGeometry();
      const rVertices = [];
      const rUvs = [];
      const riverWidth = 3.0;

      for (let i = 0; i < ribbonPts.length; i++) {{
        const pt = ribbonPts[i];
        const nextPt = (i < ribbonPts.length - 1) ? ribbonPts[i + 1] : pt;
        const prevPt = (i > 0) ? ribbonPts[i - 1] : pt;
        const dir = new THREE.Vector3().subVectors(nextPt, prevPt).normalize();
        const normal = new THREE.Vector3(-dir.z, 0, dir.x).normalize();

        const p1 = new THREE.Vector3().copy(pt).addScaledVector(normal, riverWidth * 0.5);
        const p2 = new THREE.Vector3().copy(pt).addScaledVector(normal, -riverWidth * 0.5);

        rVertices.push(p1.x, p1.y, p1.z);
        rVertices.push(p2.x, p2.y, p2.z);

        const v = i / (ribbonPts.length - 1);
        rUvs.push(0, v * 12.0);
        rUvs.push(1, v * 12.0);
      }}

      const rIndices = [];
      for (let i = 0; i < ribbonPts.length - 1; i++) {{
        const a = i * 2;
        const b = i * 2 + 1;
        const c = (i + 1) * 2;
        const d = (i + 1) * 2 + 1;
        rIndices.push(a, b, c);
        rIndices.push(b, d, c);
      }}

      riverGeom.setAttribute('position', new THREE.Float32BufferAttribute(rVertices, 3));
      riverGeom.setAttribute('uv', new THREE.Float32BufferAttribute(rUvs, 2));
      riverGeom.setIndex(rIndices);
      riverGeom.computeVertexNormals();

      riverWaterMesh = new THREE.Mesh(riverGeom, livingWaterMat);
      scene.add(riverWaterMesh);

      // Living River Drift / Foam Particles (flowing downstream)
      const foamCount = 65;
      const foamGeom = new THREE.BufferGeometry();
      const foamPos = new Float32Array(foamCount * 3);
      const foamProgress = new Float32Array(foamCount);
      for (let f = 0; f < foamCount; f++) {{
        foamProgress[f] = Math.random();
        const pt = riverCurve.getPoint(foamProgress[f]);
        foamPos[f * 3 + 0] = pt.x + (Math.random() - 0.5) * 1.8;
        foamPos[f * 3 + 1] = pt.y + 0.08;
        foamPos[f * 3 + 2] = pt.z + (Math.random() - 0.5) * 1.8;
      }}
      foamGeom.setAttribute('position', new THREE.BufferAttribute(foamPos, 3));
      const foamMat = new THREE.PointsMaterial({{ color: 0xe0f2fe, size: 0.35, transparent: true, opacity: 0.85 }});
      riverFoamParticles = new THREE.Points(foamGeom, foamMat);
      riverFoamParticles.userData = {{ progress: foamProgress }};
      scene.add(riverFoamParticles);

      // Highway Bridge over the Luni River at Govindgarh
      const bridgeX = -18, bridgeZ = getRiverZ(bridgeX);
      const bridgeY = getRegionalElevation(bridgeX, bridgeZ) + 1.2;
      const bridgeDeckGeom = new THREE.BoxGeometry(3.8, 0.40, 11.0);
      const concreteMat = new THREE.MeshStandardMaterial({{ color: 0x94a3b8, roughness: 0.85 }});
      const bridgeDeck = new THREE.Mesh(bridgeDeckGeom, concreteMat);
      bridgeDeck.position.set(bridgeX, bridgeY, bridgeZ);
      bridgeDeck.castShadow = true;
      scene.add(bridgeDeck);

      for (let pierZ of [bridgeZ - 3.2, bridgeZ + 3.2]) {{
        const pierGeom = new THREE.CylinderGeometry(0.32, 0.32, 2.5, 8);
        const pier = new THREE.Mesh(pierGeom, concreteMat);
        pier.position.set(bridgeX, bridgeY - 1.25, pierZ);
        scene.add(pier);
      }}

      // Paved State Highway through Valley Floor
      const roadPts = [
        new THREE.Vector3(42, 0, -18),
        new THREE.Vector3(20, 0, -8),
        new THREE.Vector3(6, 0, 12),
        new THREE.Vector3(-6, 0, 10),
        new THREE.Vector3(-18, 0, bridgeZ),
        new THREE.Vector3(-35, 0, 0),
        new THREE.Vector3(-55, 0, -8),
        new THREE.Vector3(-75, 0, -16)
      ];
      roadPts.forEach(pt => {{
        pt.y = getRegionalElevation(pt.x, pt.z) + 0.12;
      }});
      const roadCurve = new THREE.CatmullRomCurve3(roadPts);
      const roadGeom = new THREE.TubeGeometry(roadCurve, 70, 0.65, 6, false);
      const roadMat = new THREE.MeshStandardMaterial({{ color: 0x1e293b, roughness: 0.92 }});
      const roadMesh = new THREE.Mesh(roadGeom, roadMat);
      scene.add(roadMesh);

      // 8. Populated Rajasthani Rural Settlements on Flat Valley Grounds
      settlementGroup = new THREE.Group();
      scene.add(settlementGroup);

      const villages = [
        {{ name: "Govindgarh", x: -18, z: 6, count: 28 }},
        {{ name: "Pushkar Rural", x: 6, z: 12, count: 24 }},
        {{ name: "Pisangan Plains", x: -42, z: -5, count: 26 }},
        {{ name: "Srinagar East", x: 42, z: -18, count: 20 }},
        {{ name: "Saradhna South", x: -12, z: -35, count: 18 }},
      ];

      villages.forEach(v => {{
        for (let b = 0; b < v.count; b++) {{
          const bx = v.x + (Math.random() - 0.5) * 10;
          const bz = v.z + (Math.random() - 0.5) * 10;
          const by = getRegionalElevation(bx, bz);

          const w = 1.2 + Math.random() * 1.0;
          const h = 0.9 + Math.random() * 0.7;
          const d = 1.2 + Math.random() * 1.0;

          const isWhite = Math.random() > 0.45;
          const houseGeom = new THREE.BoxGeometry(w, h, d);
          const houseMat = new THREE.MeshStandardMaterial({{
            color: isWhite ? 0xf8fafc : 0xd4a373,
            roughness: 0.88,
            clippingPlanes: [clipPlaneX],
          }});
          const house = new THREE.Mesh(houseGeom, houseMat);
          house.position.set(bx, by + h / 2, bz);
          house.castShadow = true;
          settlementGroup.add(house);

          if (Math.random() > 0.35) {{
            const tankGeom = new THREE.CylinderGeometry(0.18, 0.18, 0.35, 8);
            const tankMat = new THREE.MeshStandardMaterial({{ color: 0x0284c7 }});
            const tank = new THREE.Mesh(tankGeom, tankMat);
            tank.position.set(bx + 0.2, by + h + 0.18, bz + 0.2);
            settlementGroup.add(tank);
          }}
        }}

        // Traditional Stepwell (Baori)
        const baoriY = getRegionalElevation(v.x + 3.0, v.z + 3.0);
        const baoriGeom = new THREE.CylinderGeometry(1.5, 1.1, 1.2, 8);
        const baoriMat = new THREE.MeshStandardMaterial({{ color: 0x64748b, roughness: 0.92 }});
        const baori = new THREE.Mesh(baoriGeom, baoriMat);
        baori.position.set(v.x + 3.0, baoriY + 0.15, v.z + 3.0);
        settlementGroup.add(baori);

        // Stone Shade Pavilion (Chhatri)
        const chhatriY = getRegionalElevation(v.x - 2.8, v.z - 2.5);
        const chhatriDomeGeom = new THREE.SphereGeometry(0.8, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2);
        const chhatriMat = new THREE.MeshStandardMaterial({{ color: 0xe2a868, roughness: 0.85 }});
        const chhatriDome = new THREE.Mesh(chhatriDomeGeom, chhatriMat);
        chhatriDome.position.set(v.x - 2.8, chhatriY + 1.5, v.z - 2.5);
        settlementGroup.add(chhatriDome);
        for (let cp = 0; cp < 4; cp++) {{
          const cx = v.x - 2.8 + (cp % 2 === 0 ? 0.5 : -0.5);
          const cz = v.z - 2.5 + (cp < 2 ? 0.5 : -0.5);
          const pillarGeom = new THREE.CylinderGeometry(0.06, 0.06, 1.5, 6);
          const pillar = new THREE.Mesh(pillarGeom, chhatriMat);
          pillar.position.set(cx, chhatriY + 0.75, cz);
          settlementGroup.add(pillar);
        }}
      }});

      // 9. Living Activity: Vehicles, Camels & Life
      activityGroup = new THREE.Group();
      scene.add(activityGroup);

      const vehicleColors = [0xd97706, 0x0284c7, 0xef4444, 0x475569];
      for (let i = 0; i < 4; i++) {{
        const vGroup = new THREE.Group();
        const bodyGeom = new THREE.BoxGeometry(1.5, 0.7, 0.75);
        const bodyMat = new THREE.MeshStandardMaterial({{ color: vehicleColors[i % 4], roughness: 0.5 }});
        const body = new THREE.Mesh(bodyGeom, bodyMat);
        body.position.y = 0.40;
        body.castShadow = true;
        vGroup.add(body);

        const cabGeom = new THREE.BoxGeometry(0.65, 0.5, 0.7);
        const cabMat = new THREE.MeshStandardMaterial({{ color: 0x0f172a, roughness: 0.3 }});
        const cab = new THREE.Mesh(cabGeom, cabMat);
        cab.position.set(0.25, 0.9, 0);
        vGroup.add(cab);

        activityGroup.add(vGroup);
        movingVehicles.push({{ group: vGroup, progress: i * 0.25, speed: 0.0006 + Math.random() * 0.0004, curve: roadCurve }});
      }}

      // Desert Camels on Dunes & Valley
      const camelLocs = [
        {{ x: -28, z: 12 }}, {{ x: -30, z: 13.5 }}, {{ x: -32, z: 15 }},
        {{ x: -48, z: 2 }}, {{ x: -50, z: 3.5 }},
        {{ x: -22, z: -20 }}, {{ x: -24, z: -18 }}
      ];
      camelLocs.forEach(c => {{
        const cy = getRegionalElevation(c.x, c.z);
        const camel = new THREE.Group();
        const cMat = new THREE.MeshStandardMaterial({{ color: 0xb45309, roughness: 0.9 }});

        const body = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.65, 0.55), cMat);
        body.position.y = 1.0;
        camel.add(body);

        const hump = new THREE.Mesh(new THREE.ConeGeometry(0.38, 0.55, 8), cMat);
        hump.position.set(-0.1, 1.5, 0);
        camel.add(hump);

        const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.14, 0.75, 6), cMat);
        neck.position.set(0.5, 1.4, 0);
        neck.rotation.z = -0.35;
        camel.add(neck);

        for (let l = 0; l < 4; l++) {{
          const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.8, 6), cMat);
          leg.position.set((l < 2 ? 0.35 : -0.35), 0.4, (l % 2 === 0 ? 0.18 : -0.18));
          camel.add(leg);
        }}

        camel.position.set(c.x, cy, c.z);
        activityGroup.add(camel);
      }});

      // 10. Monitoring Wellheads & Sensor Network
      wellGroup = new THREE.Group();
      scene.add(wellGroup);

      const wellLocs = [
        {{ id: "govindgarh", name: "Govindgarh Wellhead", x: -18, z: 6, status: "Safe", badgeClass: "status-safe", color: 0x10b981, dtwl: "7.94 mbgl", block: "Ajmer (Pisangan)", coords: "26.4600°N, 74.5200°E", elev: "462.0 m ASL", wtelev: "454.1 m ASL", aquifer: "Luni Alluvial Semi-Confined" }},
        {{ id: "pisangan", name: "Pisangan Central Station", x: -42, z: -5, status: "Critical", badgeClass: "status-critical", color: 0xef4444, dtwl: "28.42 mbgl", block: "Ajmer (Pisangan Central)", coords: "26.3800°N, 74.3900°E", elev: "448.0 m ASL", wtelev: "419.6 m ASL", aquifer: "Over-Exploited Deep Alluvium" }},
        {{ id: "pushkar", name: "Pushkar Hydrowell", x: 6, z: 12, status: "Safe", badgeClass: "status-safe", color: 0x10b981, dtwl: "6.12 mbgl", block: "Ajmer (Pushkar Valley)", coords: "26.4900°N, 74.5500°E", elev: "488.0 m ASL", wtelev: "481.9 m ASL", aquifer: "Aeolian Inter-Dunal Unconfined" }},
        {{ id: "srinagar", name: "Srinagar Station", x: 42, z: -18, status: "Semi-Critical", badgeClass: "status-semi", color: 0xf59e0b, dtwl: "16.80 mbgl", block: "Ajmer (Srinagar Piedmont)", coords: "26.4300°N, 74.7600°E", elev: "475.0 m ASL", wtelev: "458.2 m ASL", aquifer: "Fractured Weathered Gneiss" }},
        {{ id: "saradhna", name: "Saradhna Piezometer", x: -12, z: -35, status: "Safe", badgeClass: "status-safe", color: 0x10b981, dtwl: "9.35 mbgl", block: "Ajmer (Saradhna Agri)", coords: "26.3400°N, 74.5100°E", elev: "455.0 m ASL", wtelev: "445.6 m ASL", aquifer: "Semi-Confined Sandy Loam" }},
      ];

      wellLocs.forEach(w => {{
        const wy = getRegionalElevation(w.x, w.z);

        const tubeH = Math.max(3.0, wy - baseWaterY + 3.0);
        const tubeGeom = new THREE.CylinderGeometry(0.18, 0.18, tubeH, 8);
        const tubeMat = new THREE.MeshStandardMaterial({{ color: 0x94a3b8, metalness: 0.8 }});
        const tube = new THREE.Mesh(tubeGeom, tubeMat);
        tube.position.set(w.x, wy - tubeH / 2, w.z);
        tube.castShadow = true;
        wellGroup.add(tube);

        const apronGeom = new THREE.CylinderGeometry(1.2, 1.4, 0.30, 8);
        const apronMat = new THREE.MeshStandardMaterial({{ color: 0x64748b }});
        const apron = new THREE.Mesh(apronGeom, apronMat);
        apron.position.set(w.x, wy + 0.15, w.z);
        wellGroup.add(apron);

        const mastGeom = new THREE.CylinderGeometry(0.07, 0.07, 2.0, 6);
        const mastMat = new THREE.MeshStandardMaterial({{ color: 0x1e293b }});
        const mast = new THREE.Mesh(mastGeom, mastMat);
        mast.position.set(w.x, wy + 1.15, w.z);
        wellGroup.add(mast);

        const panelGeom = new THREE.BoxGeometry(1.0, 0.05, 0.8);
        const panelMat = new THREE.MeshStandardMaterial({{ color: 0x1e3a8a, metalness: 0.7 }});
        const panel = new THREE.Mesh(panelGeom, panelMat);
        panel.position.set(w.x, wy + 1.9, w.z);
        panel.rotation.x = 0.45;
        wellGroup.add(panel);

        const ledGeom = new THREE.SphereGeometry(0.30, 12, 12);
        const ledMat = new THREE.MeshBasicMaterial({{ color: w.color }});
        const led = new THREE.Mesh(ledGeom, ledMat);
        led.position.set(w.x, wy + 2.3, w.z);
        led.userData = w;
        wellGroup.add(led);
      }});

      // Raycaster for Wellhead Interaction
      const raycaster = new THREE.Raycaster();
      const mouse = new THREE.Vector2();
      canvas.addEventListener('click', (e) => {{
        const rect = canvas.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(wellGroup.children, true);
        if (intersects.length > 0) {{
          let obj = intersects[0].object;
          while (obj && !obj.userData.name && obj.parent) obj = obj.parent;
          if (obj && obj.userData.name) {{
            inspectWell(obj.userData);
          }}
        }}
      }});

      // 11. Photorealistic 3D Trees from User Assets (22-trees_9_obj)
      treeGroup = new THREE.Group();
      scene.add(treeGroup);

      const mtlPath = (window.location.protocol === 'file:') ? '../static/tree_sonnerat.mtl' : '/app/static/tree_sonnerat.mtl';
      const objPath = (window.location.protocol === 'file:') ? '../static/tree_sonnerat.obj' : '/app/static/tree_sonnerat.obj';

      const treePositions = [];
      for (let t = 0; t < 110; t++) {{
        const tx = (Math.random() - 0.5) * 130;
        const tz = (Math.random() - 0.5) * 130;
        const ty = getRegionalElevation(tx, tz);
        if (ty < 2.5 && ty > -1.0) {{
          treePositions.push({{ x: tx, y: ty, z: tz, scale: 0.18 + Math.random() * 0.14, rot: Math.random() * Math.PI * 2 }});
        }}
      }}

      // Fallback Procedural Khejri Generator
      function spawnProceduralTrees() {{
        const tCount = treePositions.length;
        const trunkGeom = new THREE.CylinderGeometry(0.12, 0.22, 1.4, 6);
        const trunkMat = new THREE.MeshStandardMaterial({{ color: 0x3f2d1c, roughness: 0.95, clippingPlanes: [clipPlaneX] }});
        const canopyGeom1 = new THREE.CylinderGeometry(0.95, 0.65, 0.40, 8);
        const canopyGeom2 = new THREE.CylinderGeometry(0.70, 0.40, 0.32, 8);
        const canopyMat = new THREE.MeshStandardMaterial({{ color: 0x365314, roughness: 0.92, clippingPlanes: [clipPlaneX] }});
        const canopyMatTop = new THREE.MeshStandardMaterial({{ color: 0x3f6212, roughness: 0.90, clippingPlanes: [clipPlaneX] }});

        const trunkInst = new THREE.InstancedMesh(trunkGeom, trunkMat, tCount);
        const c1Inst = new THREE.InstancedMesh(canopyGeom1, canopyMat, tCount);
        const c2Inst = new THREE.InstancedMesh(canopyGeom2, canopyMatTop, tCount);
        const mat = new THREE.Matrix4();
        const posV = new THREE.Vector3();
        const quat = new THREE.Quaternion();
        const scV = new THREE.Vector3(1, 1, 1);

        for (let i = 0; i < tCount; i++) {{
          const tp = treePositions[i];
          const s = tp.scale * 3.5;
          scV.set(s, s, s);

          posV.set(tp.x, tp.y + 0.7 * s, tp.z);
          mat.compose(posV, quat, scV);
          trunkInst.setMatrixAt(i, mat);

          posV.set(tp.x, tp.y + 1.4 * s, tp.z);
          mat.compose(posV, quat, scV);
          c1Inst.setMatrixAt(i, mat);

          posV.set(tp.x + 0.1 * s, tp.y + 1.75 * s, tp.z + 0.1 * s);
          mat.compose(posV, quat, scV);
          c2Inst.setMatrixAt(i, mat);
        }}
        trunkInst.castShadow = true;
        treeGroup.add(trunkInst);
        treeGroup.add(c1Inst);
        treeGroup.add(c2Inst);
      }}

      // Load User 3D OBJ Tree Model
      if (THREE.OBJLoader && THREE.MTLLoader) {{
        const mtlLoader = new THREE.MTLLoader();
        mtlLoader.setCrossOrigin('anonymous');
        mtlLoader.load(mtlPath, (materials) => {{
          materials.preload();
          const objLoader = new THREE.OBJLoader();
          objLoader.setMaterials(materials);
          objLoader.load(objPath, (objModel) => {{
            console.log('User 3D Tree OBJ model successfully loaded!');
            objModel.traverse((child) => {{
              if (child.isMesh) {{
                child.castShadow = true;
                child.receiveShadow = true;
                if (child.material) {{
                  child.material.clippingPlanes = [clipPlaneX];
                  child.material.side = THREE.DoubleSide;
                  child.material.roughness = 0.88;
                  child.material.metalness = 0.05;
                  if (child.material.color) {{
                    child.material.color.setRGB(0.50, 0.68, 0.38);
                  }}
                }}
              }}
            }});
            treePositions.forEach(tp => {{
              const clone = objModel.clone();
              clone.position.set(tp.x, tp.y, tp.z);
              clone.scale.set(tp.scale, tp.scale, tp.scale);
              clone.rotation.y = tp.rot;
              treeGroup.add(clone);
            }});
          }}, undefined, (err) => {{
            console.warn('OBJLoader failed, using procedural trees:', err);
            spawnProceduralTrees();
          }});
        }}, undefined, (err) => {{
          console.warn('MTLLoader failed, using procedural trees:', err);
          spawnProceduralTrees();
        }});
      }} else {{
        spawnProceduralTrees();
      }}

      // 12. 3D Grass Cover from User Assets (24-grass / grass_tuft.png)
      grassGroup = new THREE.Group();
      scene.add(grassGroup);

      const grassTexUrl = (window.location.protocol === 'file:') ? '../static/grass_tuft.png' : '/app/static/grass_tuft.png';
      const grassTex = texLoader.load(grassTexUrl);
      grassTex.anisotropy = 4;

      const grassPlane1 = new THREE.PlaneGeometry(0.85, 1.3);
      grassPlane1.translate(0, 0.65, 0);
      const grassPlane2 = grassPlane1.clone().rotateY(Math.PI / 2);
      const grassPlane3 = grassPlane1.clone().rotateY(Math.PI / 4);

      const tuftGeom = new THREE.BufferGeometry();
      const p1Arr = grassPlane1.attributes.position.array;
      const p2Arr = grassPlane2.attributes.position.array;
      const p3Arr = grassPlane3.attributes.position.array;
      const combinedPos = new Float32Array([...p1Arr, ...p2Arr, ...p3Arr]);
      const uv1Arr = grassPlane1.attributes.uv.array;
      const combinedUv = new Float32Array([...uv1Arr, ...uv1Arr, ...uv1Arr]);
      
      const idx1 = Array.from(grassPlane1.index.array);
      const idx2 = idx1.map(i => i + 4);
      const idx3 = idx1.map(i => i + 8);
      const combinedIdx = new Uint16Array([...idx1, ...idx2, ...idx3]);

      tuftGeom.setAttribute('position', new THREE.BufferAttribute(combinedPos, 3));
      tuftGeom.setAttribute('uv', new THREE.BufferAttribute(combinedUv, 2));
      tuftGeom.setIndex(new THREE.BufferAttribute(combinedIdx, 1));
      tuftGeom.computeVertexNormals();

      const grassMat = new THREE.MeshStandardMaterial({{
        map: grassTex,
        alphaTest: 0.35,
        transparent: true,
        side: THREE.DoubleSide,
        roughness: 0.75,
        clippingPlanes: [clipPlaneX],
      }});

      const grassCount = 420;
      const grassInst = new THREE.InstancedMesh(tuftGeom, grassMat, grassCount);
      const gMat = new THREE.Matrix4();
      const gPos = new THREE.Vector3();
      const gQuat = new THREE.Quaternion();
      const gSc = new THREE.Vector3(1, 1, 1);

      let gPlaced = 0;
      for (let g = 0; g < grassCount; g++) {{
        const gx = (Math.random() - 0.5) * 115;
        const gz = (Math.random() - 0.5) * 115;
        const gy = getRegionalElevation(gx, gz);
        if (gy < 2.0 && gy > -1.0) {{
          const s = 0.7 + Math.random() * 0.8;
          gSc.set(s, s, s);
          gPos.set(gx, gy, gz);
          gQuat.setFromAxisAngle(new THREE.Vector3(0, 1, 0), Math.random() * Math.PI);
          gMat.compose(gPos, gQuat, gSc);
          grassInst.setMatrixAt(gPlaced, gMat);
          gPlaced++;
        }}
      }}
      grassInst.count = gPlaced;
      grassInst.castShadow = true;
      grassGroup.add(grassInst);

      // 13. Subsurface Stratigraphy Blocks & Hydrogeological Cutaway
      const waterY = baseWaterY;

      const waterGeom = new THREE.PlaneGeometry(158, 158, 32, 32);
      waterGeom.rotateX(-Math.PI / 2);
      const subWaterMat = new THREE.MeshStandardMaterial({{
        color: 0x00b4d8,
        roughness: 0.15,
        metalness: 0.60,
        transparent: true,
        opacity: 0.85,
        side: THREE.DoubleSide,
      }});
      waterMesh = new THREE.Mesh(waterGeom, subWaterMat);
      waterMesh.position.y = waterY;
      scene.add(waterMesh);

      const vadoseGeom = new THREE.BoxGeometry(158, 3.5, 158);
      const vadoseMat = new THREE.MeshStandardMaterial({{ color: 0x854d0e, roughness: 0.92, side: THREE.DoubleSide, clippingPlanes: [clipPlaneX] }});
      vadoseMesh = new THREE.Mesh(vadoseGeom, vadoseMat);
      vadoseMesh.position.y = waterY - 1.75;
      scene.add(vadoseMesh);

      const fracGeom = new THREE.BoxGeometry(158, 3.2, 158);
      const fracMat = new THREE.MeshStandardMaterial({{ color: 0xb45309, roughness: 0.88, side: THREE.DoubleSide, clippingPlanes: [clipPlaneX] }});
      fracturedMesh = new THREE.Mesh(fracGeom, fracMat);
      fracturedMesh.position.y = waterY - 5.1;
      scene.add(fracturedMesh);

      const aquitardGeom = new THREE.BoxGeometry(158, 2.2, 158);
      const aquitardMat = new THREE.MeshStandardMaterial({{ color: 0x475569, roughness: 0.92, side: THREE.DoubleSide, clippingPlanes: [clipPlaneX] }});
      aquitardMesh = new THREE.Mesh(aquitardGeom, aquitardMat);
      aquitardMesh.position.y = waterY - 7.8;
      scene.add(aquitardMesh);

      const bedrockGeom = new THREE.BoxGeometry(158, 4.5, 158);
      const bedrockMat = new THREE.MeshStandardMaterial({{ color: 0x0f172a, roughness: 0.96, side: THREE.DoubleSide, clippingPlanes: [clipPlaneX] }});
      bedrockMesh = new THREE.Mesh(bedrockGeom, bedrockMat);
      bedrockMesh.position.y = waterY - 11.15;
      scene.add(bedrockMesh);

      // 14. Dynamic Darcy Groundwater Flow Streamlines
      const pCount = 450;
      const pGeom = new THREE.BufferGeometry();
      const pPos = new Float32Array(pCount * 3);
      for (let p = 0; p < pCount; p++) {{
        pPos[p * 3 + 0] = (Math.random() - 0.5) * 140;
        pPos[p * 3 + 1] = waterY + 0.05;
        pPos[p * 3 + 2] = (Math.random() - 0.5) * 140;
      }}
      pGeom.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
      const pMat = new THREE.PointsMaterial({{ color: 0x00f5ff, size: 0.42, transparent: true, opacity: 0.85 }});
      flowParticles = new THREE.Points(pGeom, pMat);
      scene.add(flowParticles);

      // 15. Monsoon Rain Simulation Particle System
      const rainCount = 2800;
      const rainGeom = new THREE.BufferGeometry();
      const rainPos = new Float32Array(rainCount * 3);
      for (let r = 0; r < rainCount; r++) {{
        rainPos[r * 3 + 0] = (Math.random() - 0.5) * 160;
        rainPos[r * 3 + 1] = Math.random() * 80 + 10;
        rainPos[r * 3 + 2] = (Math.random() - 0.5) * 160;
      }}
      rainGeom.setAttribute('position', new THREE.BufferAttribute(rainPos, 3));
      const rainMat = new THREE.PointsMaterial({{ color: 0x93c5fd, size: 0.28, transparent: true, opacity: 0.65 }});
      rainParticles = new THREE.Points(rainGeom, rainMat);
      rainParticles.visible = false;
      scene.add(rainParticles);

      // 16. High-Altitude Atmospheric Clouds (y = 95 - 110)
      cloudGroup = new THREE.Group();
      scene.add(cloudGroup);
      const cloudPuffGeom = new THREE.DodecahedronGeometry(8.5, 1);
      const cloudMat = new THREE.MeshStandardMaterial({{ color: 0xffffff, roughness: 0.95, transparent: true, opacity: 0.65 }});
      for (let c = 0; c < 12; c++) {{
        const puff = new THREE.Mesh(cloudPuffGeom, cloudMat);
        puff.position.set((Math.random() - 0.5) * 160, 95 + Math.random() * 15, (Math.random() - 0.5) * 160);
        puff.scale.set(2.4 + Math.random() * 1.5, 0.6 + Math.random() * 0.4, 1.5 + Math.random() * 1.0);
        cloudGroup.add(puff);
      }}

      // 17. Render Loop
      let clock = new THREE.Clock();
      function animate() {{
        requestAnimationFrame(animate);
        const delta = clock.getDelta();
        const elapsed = clock.getElapsedTime();

        if (riverWaterMesh && riverWaterMesh.material.normalMap) {{
          riverWaterMesh.material.normalMap.offset.y -= delta * 0.18;
          riverWaterMesh.material.normalMap.offset.x += delta * 0.04;
        }}

        if (riverFoamParticles && riverCurve) {{
          const fPos = riverFoamParticles.geometry.attributes.position.array;
          const fProg = riverFoamParticles.userData.progress;
          for (let f = 0; f < foamCount; f++) {{
            fProg[f] -= delta * 0.045;
            if (fProg[f] < 0) fProg[f] = 1.0;
            const pt = riverCurve.getPoint(fProg[f]);
            fPos[f * 3 + 0] = pt.x + Math.sin(elapsed * 2.0 + f) * 0.6;
            fPos[f * 3 + 1] = pt.y + 0.08;
            fPos[f * 3 + 2] = pt.z + Math.cos(elapsed * 2.0 + f) * 0.6;
          }}
          riverFoamParticles.geometry.attributes.position.needsUpdate = true;
        }}

        if (flowParticles) {{
          const arr = flowParticles.geometry.attributes.position.array;
          for (let i = 0; i < pCount; i++) {{
            arr[i * 3 + 0] -= 0.06;
            arr[i * 3 + 2] -= 0.04;
            if (arr[i * 3 + 0] < -70) arr[i * 3 + 0] = 70;
            if (arr[i * 3 + 2] < -70) arr[i * 3 + 2] = 70;
          }}
          flowParticles.geometry.attributes.position.needsUpdate = true;
        }}

        if (isRaining && rainParticles) {{
          const rArr = rainParticles.geometry.attributes.position.array;
          for (let i = 0; i < rainCount; i++) {{
            rArr[i * 3 + 1] -= delta * 65.0;
            if (rArr[i * 3 + 1] < 0) rArr[i * 3 + 1] = 85.0;
          }}
          rainParticles.geometry.attributes.position.needsUpdate = true;
        }}

        movingVehicles.forEach(v => {{
          v.progress += v.speed;
          if (v.progress > 1.0) v.progress = 0.0;
          const pt = v.curve.getPoint(v.progress);
          const nextPt = v.curve.getPoint(Math.min(1.0, v.progress + 0.01));
          v.group.position.copy(pt);
          v.group.lookAt(nextPt);
        }});

        if (cloudGroup) {{
          cloudGroup.children.forEach(c => {{
            c.position.x += delta * 1.2;
            if (c.position.x > 95) c.position.x = -95;
          }});
        }}

        controls.update();
        renderer.render(scene, camera);
      }}
      animate();
    }}

    // Camera Navigation Presets
    function applyCameraPreset(preset) {{
      document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
      const btn = document.getElementById('btn-' + preset);
      if (btn) btn.classList.add('active');

      if (preset === 'iso') {{
        camera.position.set(15, 62, 82);
        controls.target.set(-10, 0, -5);
      }} else if (preset === 'basin') {{
        camera.position.set(0, 115, 105);
        controls.target.set(0, 0, 0);
      }} else if (preset === 'top') {{
        camera.position.set(0, 135, 0.001);
        controls.target.set(0, 0, 0);
      }} else if (preset === 'oblique') {{
        camera.position.set(45, 18, 55);
        controls.target.set(-10, 2, -5);
      }} else if (preset === 'cutaway') {{
        camera.position.set(45, 24, -45);
        controls.target.set(0, -3, 0);
        updateSlice(50);
      }} else if (preset === 'settle') {{
        camera.position.set(-18 + 14, 11, 6 + 14);
        controls.target.set(-18, 2, 6);
      }} else if (preset === 'river') {{
        camera.position.set(8, 16, 12);
        controls.target.set(-18, 1.2, 6);
      }}
    }}

    // Lighting Presets
    function applyLightingPreset(mode) {{
      document.querySelectorAll('.top-actions .action-btn').forEach(b => {{
        if (b.id !== 'btn-rain') b.classList.remove('active');
      }});
      const btn = document.getElementById('btn-' + mode);
      if (btn) btn.classList.add('active');

      if (mode === 'day') {{
        scene.background.setHex(0xbbe5f8);
        scene.fog.color.setHex(0xfef3c7);
        renderer.toneMappingExposure = 1.05;
      }} else if (mode === 'sunset') {{
        scene.background.setHex(0xfdba74);
        scene.fog.color.setHex(0x7c2d12);
        renderer.toneMappingExposure = 1.20;
      }} else if (mode === 'night') {{
        scene.background.setHex(0x020617);
        scene.fog.color.setHex(0x090d16);
        renderer.toneMappingExposure = 0.65;
      }}
    }}

    // Monsoon Rain Simulator Toggle
    function toggleRainSimulation() {{
      isRaining = !isRaining;
      const btn = document.getElementById('btn-rain');
      const banner = document.getElementById('rain-banner');

      if (isRaining) {{
        btn.classList.add('rain-active');
        banner.style.display = 'flex';
        rainParticles.visible = true;
        scene.background.setHex(0x334155);
        scene.fog.color.setHex(0x1e293b);
        terrainMesh.material.roughness = 0.22;
        terrainMesh.material.needsUpdate = true;
      }} else {{
        btn.classList.remove('rain-active');
        banner.style.display = 'none';
        rainParticles.visible = false;
        applyLightingPreset('day');
        terrainMesh.material.roughness = 0.86;
        terrainMesh.material.needsUpdate = true;
      }}
    }}

    // Slice Cutaway Update
    function updateSlice(pct) {{
      const val = parseFloat(pct);
      document.getElementById('slice-slider').value = val;
      document.getElementById('slice-val').innerText = val.toFixed(0) + '%';
      const planeConstant = 95.0 - (val / 100.0) * 190.0;
      clipPlaneX.constant = planeConstant;
    }}

    // Vertical Exaggeration Update
    function updateExaggeration(val) {{
      currentExag = parseFloat(val);
      document.getElementById('exag-val').innerText = currentExag.toFixed(2) + 'x';

      const pos = terrainGeom.attributes.position;
      for (let i = 0; i < pos.count; i++) {{
        const x = pos.getX(i);
        const z = pos.getZ(i);
        pos.setY(i, getRegionalElevation(x, z));
      }}
      terrainGeom.computeVertexNormals();
      terrainGeom.attributes.position.needsUpdate = true;
    }}

    // Water Table Offset Update
    function updateWaterTable(val) {{
      const offset = parseFloat(val);
      document.getElementById('water-val').innerText = (offset >= 0 ? '+' : '') + offset.toFixed(1) + 'm';
      const newY = baseWaterY + offset;
      waterMesh.position.y = newY;
      vadoseMesh.position.y = newY - 1.75;
      fracturedMesh.position.y = newY - 5.1;
      aquitardMesh.position.y = newY - 7.8;
      bedrockMesh.position.y = newY - 11.15;
    }}

    // Layer Drawer Panel
    function toggleLayerPanel() {{
      const panel = document.getElementById('layer-panel');
      panel.classList.toggle('open');
    }}

    function toggleLayer(layer) {{
      const chk = document.getElementById('layer-' + layer);
      const v = chk.checked;
      if (layer === 'terrain') terrainMesh.visible = v;
      else if (layer === 'satellite') {{
        terrainMesh.material.map = v ? satTexture : null;
        terrainMesh.material.needsUpdate = true;
      }}
      else if (layer === 'river') {{ riverWaterMesh.visible = v; lakeGroup.visible = v; if (riverFoamParticles) riverFoamParticles.visible = v; }}
      else if (layer === 'settlements') settlementGroup.visible = v;
      else if (layer === 'trees') treeGroup.visible = v;
      else if (layer === 'grass') grassGroup.visible = v;
      else if (layer === 'activity') activityGroup.visible = v;
      else if (layer === 'wells') wellGroup.visible = v;
      else if (layer === 'flow') flowParticles.visible = v;
      else if (layer === 'strata') {{
        waterMesh.visible = v; vadoseMesh.visible = v; fracturedMesh.visible = v;
        aquitardMesh.visible = v; bedrockMesh.visible = v;
      }}
    }}

    // Inspect Wellhead & Fly-To
    function inspectWell(w) {{
      const card = document.getElementById('well-card');
      document.getElementById('wc-name').innerText = w.name;
      document.getElementById('wc-block').innerText = w.block;
      document.getElementById('wc-coords').innerText = w.coords;
      document.getElementById('wc-elev').innerText = w.elev;
      document.getElementById('wc-dtwl').innerText = w.dtwl;
      document.getElementById('wc-wtelev').innerText = w.wtelev;
      document.getElementById('wc-aquifer').innerText = w.aquifer;

      const badge = document.getElementById('wc-badge');
      badge.innerText = w.status.toUpperCase();
      badge.className = 'well-card-status ' + w.badgeClass;

      card.style.display = 'block';

      controls.target.set(w.x, getRegionalElevation(w.x, w.z) + 1.0, w.z);
      camera.position.set(w.x + 10, getRegionalElevation(w.x, w.z) + 8, w.z + 10);
    }}

    function closeWellCard() {{
      document.getElementById('well-card').style.display = 'none';
    }}

    // Safe Startup Execution
    window.addEventListener('DOMContentLoaded', () => {{
      setTimeout(initEngine, 50);
    }});
    if (document.readyState === 'complete' || document.readyState === 'interactive') {{
      setTimeout(initEngine, 50);
    }}
</script>
</body>
</html>
"""

# Now replace _get_threejs_regional_template in digital_twin.py
target_py = r"D:\NIH_roorkee\FULL WORK FINAL_DIGITAL_NAYA_PANI\NAYA_PAANI\digital_twin.py"
with open(target_py, "r", encoding="utf-8") as fp:
    py_text = fp.read()

func_header = "def _get_threejs_regional_template() -> str:"
start_idx = py_text.find(func_header)
if start_idx == -1:
    print("Could not find function header!")
    exit(1)

next_func = "\ndef _render_threejs_desert_twin"
end_idx = py_text.find(next_func, start_idx)
if end_idx == -1:
    print("Could not find next function header!")
    exit(1)

# Escape backslashes for python raw triple-quoted string
new_func = f'''def _get_threejs_regional_template() -> str:
    """Return the photorealistic Three.js 50 km Regional Environmental & Hydrological Digital Twin HTML/JS template."""
    return r"""{template_html}"""
'''

updated_py = py_text[:start_idx] + new_func + py_text[end_idx:]

with open(target_py, "w", encoding="utf-8") as fp:
    fp.write(updated_py)

print("Successfully updated digital_twin.py! New file length:", len(updated_py))
