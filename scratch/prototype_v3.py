"""Prototype v3: Photorealistic environmental digital twin with micro-textured terrain, organic trees, architectural details, and animated water."""
import os

html_content = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Naya Pani - Photorealistic 50 km Regional Digital Twin v3</title>
  <style>
    * { box-sizing: border-box; }
    body, html { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #070b14; color: #f8fafc; }
    #desert-canvas-wrap { position: relative; width: 100%; height: 760px; overflow: hidden; background: #070b14; user-select: none; }
    #three-canvas { width: 100%; height: 100%; display: block; }

    /* Top Camera Toolbar */
    .top-toolbar { position: absolute; top: 10px; left: 12px; right: 12px; display: flex; align-items: center; justify-content: space-between; gap: 8px; z-index: 20; pointer-events: none; }
    .preset-bar { display: flex; align-items: center; gap: 4px; background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(12px); padding: 5px 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.18); pointer-events: auto; }
    .preset-btn { background: transparent; border: 1px solid transparent; color: #cbd5e1; padding: 5px 9px; border-radius: 6px; font-size: 11px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 4px; transition: all 0.2s; }
    .preset-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }
    .preset-btn.active { background: #d97706; color: #fff; border-color: #f59e0b; font-weight: 600; box-shadow: 0 2px 10px rgba(217,119,6,0.4); }

    .top-actions { display: flex; align-items: center; gap: 5px; pointer-events: auto; }
    .action-btn { background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.18); color: #cbd5e1; padding: 5px 9px; border-radius: 6px; font-size: 11px; font-weight: 500; cursor: pointer; transition: all 0.2s; }
    .action-btn:hover { background: #334155; color: #fff; }
    .action-btn.active { background: #d97706; color: #fff; border-color: #f59e0b; }

    /* Layer Drawer */
    .layer-drawer-btn { position: absolute; top: 54px; left: 12px; z-index: 15; background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.18); color: #f8fafc; padding: 6px 11px; border-radius: 6px; font-size: 11.5px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
    .layer-panel { position: absolute; top: 88px; left: 12px; width: 240px; background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(14px); border: 1px solid rgba(255,255,255,0.18); border-radius: 10px; padding: 10px 12px; z-index: 15; display: none; box-shadow: 0 10px 28px rgba(0,0,0,0.6); }
    .layer-panel.open { display: block; }
    .layer-panel-title { font-size: 11px; font-weight: 700; color: #f59e0b; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.12); padding-bottom: 4px; }
    .layer-item { display: flex; align-items: center; justify-content: space-between; font-size: 11px; color: #e2e8f0; margin-bottom: 5px; cursor: pointer; }
    .layer-item input { accent-color: #f59e0b; cursor: pointer; }

    /* Inspector Panel */
    .inspector-panel { position: absolute; top: 54px; right: 12px; width: 285px; background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(14px); border: 1px solid rgba(255,255,255,0.18); border-radius: 10px; padding: 12px 14px; z-index: 15; box-shadow: 0 10px 28px rgba(0,0,0,0.6); }
    .ins-header { font-size: 10.5px; font-weight: 700; color: #f59e0b; text-transform: uppercase; letter-spacing: 0.6px; display: flex; align-items: center; justify-content: space-between; }
    .ins-village { font-size: 14px; font-weight: 700; color: #fff; margin-top: 3px; }
    .ins-row { display: flex; justify-content: space-between; font-size: 11px; color: #94a3b8; margin-top: 4px; }
    .ins-val { color: #f1f5f9; font-weight: 600; }
    .ins-badge { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 10.5px; font-weight: 600; color: #fff; background: #10b981; }

    /* Bottom Dock */
    .bottom-dock { position: absolute; bottom: 10px; left: 12px; right: 12px; display: flex; align-items: center; justify-content: space-between; gap: 8px; z-index: 20; pointer-events: none; }
    .dock-left { display: flex; align-items: center; gap: 10px; pointer-events: auto; background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(12px); padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.18); }
    .dock-center { display: flex; align-items: center; gap: 12px; pointer-events: auto; background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(14px); padding: 6px 16px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.22); box-shadow: 0 6px 24px rgba(0,0,0,0.45); }
    .dock-right { display: flex; align-items: center; gap: 8px; pointer-events: auto; background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(12px); padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.18); font-size: 11px; color: #cbd5e1; }
    .dock-ctrl { display: flex; align-items: center; gap: 6px; font-size: 11px; color: #e2e8f0; }
    .dock-ctrl label { font-weight: 600; color: #fde047; white-space: nowrap; }
    .dock-ctrl select { background: #1e293b; border: 1px solid #475569; color: #f8fafc; font-size: 11px; border-radius: 4px; padding: 2px 5px; outline: none; }
    .dock-ctrl input[type=range] { width: 95px; accent-color: #f59e0b; cursor: pointer; }
    .dock-val { font-weight: 700; color: #38bdf8; min-width: 26px; text-align: right; }

    #well-tooltip { position: absolute; display: none; background: rgba(15,23,42,0.94); border: 1px solid #f59e0b; color: #fff; font-size: 11px; padding: 5px 9px; border-radius: 5px; pointer-events: none; z-index: 30; }
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
  <div id="desert-canvas-wrap">
    <canvas id="three-canvas"></canvas>
    <div id="well-tooltip"></div>

    <!-- Top Camera Toolbar -->
    <div class="top-toolbar">
      <div class="preset-bar">
        <button class="preset-btn active" id="btn-iso" onclick="applyCameraPreset('iso')">📐 Elevated Isometric</button>
        <button class="preset-btn" id="btn-basin" onclick="applyCameraPreset('basin')">🌐 50 km Basin</button>
        <button class="preset-btn" id="btn-top" onclick="applyCameraPreset('top')">🛰️ Top-Down GIS</button>
        <button class="preset-btn" id="btn-oblique" onclick="applyCameraPreset('oblique')">🌄 Low Oblique</button>
        <button class="preset-btn" id="btn-cutaway" onclick="applyCameraPreset('cutaway')">🪓 Subsurface</button>
        <button class="preset-btn" id="btn-settle" onclick="applyCameraPreset('settle')">🏘️ Settlements</button>
        <button class="preset-btn" id="btn-river" onclick="applyCameraPreset('river')">🌊 Luni River</button>
      </div>

      <div class="top-actions">
        <button class="action-btn active" id="amb-day" onclick="setAmbiance('day')">☀️ Day</button>
        <button class="action-btn" id="amb-sunset" onclick="setAmbiance('sunset')">🌅 Sunset</button>
        <button class="action-btn" id="amb-night" onclick="setAmbiance('night')">🌌 Night</button>
      </div>
    </div>

    <!-- Layer Drawer Button -->
    <button class="layer-drawer-btn" onclick="toggleLayerDrawer()">⚙️ Scene Layers</button>
    <div class="layer-panel" id="layer-panel">
      <div class="layer-panel-title"><span>50 km Regional Layers</span></div>
      <label class="layer-item"><span>Surface Terrain</span><input type="checkbox" id="chk-terrain" checked onchange="updateLayers()"></label>
      <label class="layer-item"><span>Subsurface Stratigraphy</span><input type="checkbox" id="chk-strata" checked onchange="updateLayers()"></label>
      <label class="layer-item"><span>Luni Water Table</span><input type="checkbox" id="chk-water" checked onchange="updateLayers()"></label>
      <label class="layer-item"><span>Luni River & Bridge</span><input type="checkbox" id="chk-river" checked onchange="updateLayers()"></label>
      <label class="layer-item"><span>WGS84 Monitoring Wells</span><input type="checkbox" id="chk-wells" checked onchange="updateLayers()"></label>
      <label class="layer-item"><span>Settlements & Roads</span><input type="checkbox" id="chk-settle" checked onchange="updateLayers()"></label>
      <label class="layer-item"><span>Khejri Flora & Trees</span><input type="checkbox" id="chk-trees" checked onchange="updateLayers()"></label>
      <label class="layer-item"><span>Groundwater Darcy Flow</span><input type="checkbox" id="chk-flow" checked onchange="updateLayers()"></label>
    </div>

    <!-- Inspector Panel -->
    <div class="inspector-panel" id="inspector-panel">
      <div class="ins-header">
        <span>Hydrogeological Asset</span>
        <span class="ins-badge" id="ins-badge">SAFE</span>
      </div>
      <div class="ins-village" id="ins-village">Govindgarh Wellhead</div>
      <div class="ins-row"><span>District / Block:</span><span class="ins-val">Ajmer (Pisangan)</span></div>
      <div class="ins-row"><span>WGS84 Coordinates:</span><span class="ins-val">26.4600°N, 74.5200°E</span></div>
      <div class="ins-row"><span>Surface Elevation:</span><span class="ins-val">462.0 m ASL</span></div>
      <div class="ins-row"><span>Active DTWL:</span><span class="ins-val" style="color:#38bdf8;">7.94 mbgl</span></div>
      <div class="ins-row"><span>Water Table Elevation:</span><span class="ins-val">454.1 m ASL</span></div>
      <div class="ins-row"><span>Regional Aquifer:</span><span class="ins-val">Luni Alluvial Semi-Confined</span></div>
    </div>

    <!-- Bottom Dock -->
    <div class="bottom-dock">
      <div class="dock-left">
        <div style="font-family:monospace; font-size:10.5px; color:#cbd5e1;">📍 26.4500°N, 74.6300°E | 50 km Radius Coverage (~7,854 km²)</div>
      </div>
      <div class="dock-center">
        <div class="dock-ctrl">
          <label>🪓 Cutaway:</label>
          <select id="cutaway-select" onchange="applyCutawayMode(this.value)">
            <option value="complete">Complete Landscape</option>
            <option value="partial">Partial Cutaway</option>
            <option value="full">Full Geological Cutaway</option>
            <option value="cross">Cross-Section</option>
            <option value="groundwater">Groundwater-Only</option>
          </select>
        </div>
        <div class="dock-ctrl">
          <label>Slicer:</label>
          <input type="range" id="slice-slider" min="0" max="100" value="0" oninput="onSliceInput(this.value)">
          <span class="dock-val" id="slice-val">0%</span>
        </div>
        <div class="dock-ctrl">
          <label>⛰️ Relief Exaggeration:</label>
          <input type="range" id="exaggeration-slider" min="1.0" max="3.0" step="0.2" value="1.2" oninput="onExaggerationInput(this.value)">
          <span class="dock-val" id="exaggeration-val">1.2x</span>
        </div>
      </div>
      <div class="dock-right">
        <span>Upper Luni Basin Digital Twin · <b>NVIDIA Omniverse Architecture</b></span>
      </div>
    </div>
  </div>

  <script>
    // Global Scene Declarations
    let scene, camera, renderer, controls;
    let terrainMesh, terrainGeom, baseHeights = [];
    let waterMesh, vadoseMesh, fracturedMesh, aquitardMesh, bedrockMesh;
    let clipPlaneX;
    let flowParticles, cloudGroup;
    let wellGroup, settlementGroup, treeGroup, riverWaterMesh;

    // Fast 2D Simplex Noise Implementation (Deterministic seed)
    const Simplex = (function() {
      const F2 = 0.5 * (Math.sqrt(3.0) - 1.0);
      const G2 = (3.0 - Math.sqrt(3.0)) / 6.0;
      const p = new Uint8Array([
        151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,30,69,142,8,99,37,240,21,10,23,
        190,6,148,247,120,234,75,0,26,197,62,94,252,219,203,117,35,11,32,57,177,33,88,237,149,56,87,174,20,
        125,136,171,168,68,175,74,165,71,134,139,48,27,166,77,146,158,231,83,111,229,122,60,211,133,230,220,
        105,92,41,55,46,245,40,244,102,143,54,65,25,63,161,1,216,80,73,209,76,132,187,208,89,18,169,200,196,
        135,130,116,188,159,86,164,100,109,198,173,186,3,64,52,217,226,250,124,123,5,202,38,147,118,126,255,
        82,85,212,207,206,59,227,47,16,58,17,182,189,28,42,223,183,170,213,119,248,152,2,44,154,163,70,221,
        153,101,155,167,43,172,9,129,22,39,253,19,98,108,110,79,113,224,232,178,185,112,104,218,246,97,228,
        251,34,242,193,238,210,144,12,191,179,162,241,81,51,145,235,249,14,239,107,49,192,214,31,181,199,106,
        157,184,84,204,176,115,121,50,45,127,4,150,254,138,236,205,93,222,114,67,29,24,72,243,141,128,195,
        78,66,215,61,156,180
      ]);
      const perm = new Uint8Array(512);
      const permMod12 = new Uint8Array(512);
      for (let i = 0; i < 512; i++) {
        perm[i] = p[i & 255];
        permMod12[i] = (perm[i] % 12);
      }
      const grad3 = [
        1,1,0, -1,1,0, 1,-1,0, -1,-1,0,
        1,0,1, -1,0,1, 1,0,-1, -1,0,-1,
        0,1,1, 0,-1,1, 0,1,-1, 0,-1,-1
      ];

      return {
        noise2D: function(xin, yin) {
          let n0, n1, n2;
          const s = (xin + yin) * F2;
          const i = Math.floor(xin + s);
          const j = Math.floor(yin + s);
          const t = (i + j) * G2;
          const X0 = i - t;
          const Y0 = j - t;
          const x0 = xin - X0;
          const y0 = yin - Y0;

          let i1, j1;
          if (x0 > y0) { i1 = 1; j1 = 0; } else { i1 = 0; j1 = 1; }

          const x1 = x0 - i1 + G2;
          const y1 = y0 - j1 + G2;
          const x2 = x0 - 1.0 + 2.0 * G2;
          const y2 = y0 - 1.0 + 2.0 * G2;

          const ii = i & 255;
          const jj = j & 255;
          const gi0 = permMod12[ii + perm[jj]] * 3;
          const gi1 = permMod12[ii + i1 + perm[jj + j1]] * 3;
          const gi2 = permMod12[ii + 1 + perm[jj + 1]] * 3;

          let t0 = 0.5 - x0 * x0 - y0 * y0;
          if (t0 < 0) n0 = 0.0;
          else { t0 *= t0; n0 = t0 * t0 * (grad3[gi0] * x0 + grad3[gi0 + 1] * y0); }

          let t1 = 0.5 - x1 * x1 - y1 * y1;
          if (t1 < 0) n1 = 0.0;
          else { t1 *= t1; n1 = t1 * t1 * (grad3[gi1] * x1 + grad3[gi1 + 1] * y1); }

          let t2 = 0.5 - x2 * x2 - y2 * y2;
          if (t2 < 0) n2 = 0.0;
          else { t2 *= t2; n2 = t2 * t2 * (grad3[gi2] * x2 + grad3[gi2 + 1] * y2); }

          return 70.0 * (n0 + n1 + n2);
        },
        fbm2D: function(x, y, octaves = 4, lacunarity = 2.0, gain = 0.5) {
          let sum = 0, amp = 1.0, freq = 1.0, maxAmp = 0;
          for (let i = 0; i < octaves; i++) {
            sum += this.noise2D(x * freq, y * freq) * amp;
            maxAmp += amp;
            amp *= gain;
            freq *= lacunarity;
          }
          return sum / maxAmp;
        }
      };
    })();

    // Sinuous Luni river centerline: flows from NE (Ajmer/Pushkar) to SW (Pisangan/Barmer)
    function getRiverZ(x) {
      return 12.0 * Math.sin(x * 0.035) + 3.5 * Math.cos(x * 0.075) - 0.22 * x - 2.0;
    }

    // Realistic Regional Elevation Function for the Upper Luni 50 km Basin
    function getRegionalElevation(x, z) {
      // 1. Regional topographic slope (tilts NE to SW towards Luni outlet)
      const baseSlope = (-x * 0.035 + z * 0.025);

      // 2. Eastern Aravalli Mountain Range (runs along strike NE-SW, x > 15)
      let aravalli = 0;
      if (x > 10) {
        // Main quartzite ridge spine
        const ridgeAxis = x - 42 - Math.sin(z * 0.05) * 10.0;
        const dRidge = Math.abs(ridgeAxis);
        const rProfile = Math.max(0, 1.0 - dRidge / 16.0);
        const rH = Math.pow(rProfile, 2.0) * 16.0;

        // Parallel subsidiary ridge
        const r2Axis = x - 64 - Math.cos(z * 0.04) * 8.0;
        const dR2 = Math.abs(r2Axis);
        const r2Profile = Math.max(0, 1.0 - dR2 / 14.0);
        const r2H = Math.pow(r2Profile, 2.0) * 18.0;

        // Rocky crags & gullies
        const crags = Simplex.fbm2D(x * 0.06, z * 0.06, 3) * 2.2;
        aravalli = rH + r2H + (rProfile > 0.05 || r2Profile > 0.05 ? crags : 0);
      }

      // 3. Central Basin Alluvial Plain (gentle rolling pediments, < 2 deg slope)
      const pediments = Simplex.fbm2D(x * 0.02, z * 0.02, 3) * 1.6 + 1.2;

      // 4. Luni River Valley Incision (smoothly carved 1.8m flat alluvial channel)
      const rz = getRiverZ(x);
      const dRiver = Math.abs(z - rz);
      let riverIncision = 0;
      if (dRiver < 6.5 && x < 42) {
        const t = dRiver / 6.5;
        // Flat riverbed bottom with sloping river bluffs
        riverIncision = -(1.0 - Math.pow(t, 2.2)) * 1.8;
      }

      // 5. Western Thar Desert Aeolian Sand Dunes (x < -10)
      let dunes = 0;
      if (x < -5) {
        const u = (x + z) * 0.05;
        const v = (-x + z) * 0.07;
        const seif = Math.sin(v * 3.2 + Simplex.noise2D(u * 1.2, v * 1.2) * 0.6) * 1.4;
        const weight = Math.max(0, Math.min(1.0, (-5 - x) / 45.0));
        dunes = seif * weight;
      }

      const rawH = baseSlope + aravalli + pediments + riverIncision + dunes;
      const exag = parseFloat(document.getElementById('exaggeration-slider') ? document.getElementById('exaggeration-slider').value : 1.2);
      return rawH * exag;
    }

    // -------------------------------------------------------------
    // HIGH-RESOLUTION PROCEDURAL SATELLITE ORTHOPHOTO TEXTURE (1024x1024)
    // -------------------------------------------------------------
    function createSatelliteOrthophotoTexture() {
      const size = 1024;
      const canvasTex = document.createElement('canvas');
      canvasTex.width = size;
      canvasTex.height = size;
      const ctx = canvasTex.getContext('2d');

      // Base Alluvial Pediment Soil (warm golden buff)
      ctx.fillStyle = '#caa373';
      ctx.fillRect(0, 0, size, size);

      const imgData = ctx.getImageData(0, 0, size, size);
      const data = imgData.data;

      for (let py = 0; py < size; py++) {
        for (let px = 0; px < size; px++) {
          const wx = (px / size) * 160.0 - 80.0;
          const wz = (py / size) * 160.0 - 80.0;

          const rz = getRiverZ(wx);
          const dRiver = Math.abs(wz - rz);

          let r, g, b;

          // 1. Aravalli Mountain Ranges (East, wx > 12)
          if (wx > 12) {
            const rockNoise = Simplex.fbm2D(wx * 0.06, wz * 0.06, 3);
            if (wx > 26) {
              // Deep quartzite rock & slate schist with shadow crevices
              r = 88 + rockNoise * 25;
              g = 78 + rockNoise * 20;
              b = 68 + rockNoise * 18;
            } else {
              // Weathered scree & talus fan
              r = 138 + rockNoise * 22;
              g = 112 + rockNoise * 18;
              b = 85 + rockNoise * 15;
            }
          }
          // 2. Luni River Channel & Sandbars
          else if (dRiver < 5.2 && wx < 42) {
            if (dRiver < 2.2) {
              // Pale dry river sand & gravel terraces
              r = 228; g = 208; b = 172;
            } else {
              // Moist riparian silt & acacia vegetation buffer
              r = 95; g = 115; b = 58;
            }
          }
          // 3. Western Thar Sand Dunefield (wx < -12)
          else if (wx < -12) {
            const duneNoise = Simplex.fbm2D(wx * 0.08, wz * 0.08, 2);
            // Fine aeolian ripple texture
            const ripple = Math.sin(wx * 18.0 + wz * 14.0) * 8.0;
            r = 218 + duneNoise * 20 + ripple;
            g = 162 + duneNoise * 16 + ripple * 0.8;
            b = 88 + duneNoise * 12;
          }
          // 4. Central Agricultural Cadastral Mosaic
          else {
            const gridX = Math.floor((wx + 80) / 4.2);
            const gridZ = Math.floor((wz + 80) / 4.2);
            const fieldHash = Math.abs(Math.sin(gridX * 12.9898 + gridZ * 78.233)) * 43758.5453;
            const fieldType = Math.floor(fieldHash) % 6;

            // Crop furrow directional lines
            const furrow = Math.sin(wx * 22.0) * 6.0;

            if (fieldType === 0) { // Emerald green irrigated winter crops (wheat, mustard)
              r = 34 + furrow; g = 112 + furrow * 1.2; b = 48;
            } else if (fieldType === 1) { // Fresh irrigated Rabi crop
              r = 52 + furrow; g = 132 + furrow * 1.2; b = 58;
            } else if (fieldType === 2) { // Golden harvest parcel
              r = 208 + furrow; g = 168 + furrow * 0.8; b = 58;
            } else if (fieldType === 3) { // Dark moist plowed loam
              r = 92 + furrow; g = 64 + furrow * 0.8; b = 38;
            } else { // Fallow arid pediment
              r = 172; g = 134; b = 92;
            }

            // Dark cadastral boundary hedgerows
            const borderX = Math.abs((wx + 80) % 4.2);
            const borderZ = Math.abs((wz + 80) % 4.2);
            if (borderX < 0.28 || borderZ < 0.28) {
              r *= 0.62; g *= 0.62; b *= 0.62;
            }
          }

          const idx = (py * size + px) * 4;
          data[idx] = Math.min(255, Math.max(0, r));
          data[idx + 1] = Math.min(255, Math.max(0, g));
          data[idx + 2] = Math.min(255, Math.max(0, b));
          data[idx + 3] = 255;
        }
      }

      ctx.putImageData(imgData, 0, 0);

      const texture = new THREE.CanvasTexture(canvasTex);
      texture.wrapS = THREE.ClampToEdgeWrapping;
      texture.wrapT = THREE.ClampToEdgeWrapping;
      texture.anisotropy = 4;
      return texture;
    }

    // -------------------------------------------------------------
    // INITIALIZE PHOTOREALISTIC THREE.JS WORLD
    // -------------------------------------------------------------
    function initEngine() {
      const wrap = document.getElementById('desert-canvas-wrap');
      const canvas = document.getElementById('three-canvas');
      const w = wrap.clientWidth || 800;
      const h = wrap.clientHeight || 760;

      // 1. Scene & Realistic Atmosphere Skybox
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0xbae6fd); // Natural blue sky
      scene.fog = new THREE.FogExp2(0xfef3c7, 0.0035);

      // Sky Dome with Atmospheric Gradient
      const skyGeom = new THREE.SphereGeometry(280, 32, 16);
      const skyMat = new THREE.MeshBasicMaterial({ color: 0x7dd3fc, side: THREE.BackSide });
      const sky = new THREE.Mesh(skyGeom, skyMat);
      scene.add(sky);

      // 2. Camera: Elevated Panoramic Isometric View (~35 deg pitch downward, framing whole 50 km basin cleanly)
      camera = new THREE.PerspectiveCamera(38, w / h, 0.5, 700);
      camera.position.set(15, 62, 82);

      // 3. Renderer with Soft Shadows & Local Clipping
      renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, powerPreference: 'high-performance' });
      renderer.setSize(w, h);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      renderer.localClippingEnabled = true;

      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.maxPolarAngle = Math.PI / 2 - 0.03;
      controls.minDistance = 8;
      controls.maxDistance = 280;
      controls.target.set(-8, 0, -8);

      // 4. Natural Directional Sunlight & Ambient Illumination
      const hemiLight = new THREE.HemisphereLight(0xfffbeb, 0x78350f, 0.70);
      scene.add(hemiLight);

      const dirLight = new THREE.DirectionalLight(0xfff7ed, 1.40);
      dirLight.position.set(65, 85, 45);
      dirLight.castShadow = true;
      dirLight.shadow.mapSize.width = 2048;
      dirLight.shadow.mapSize.height = 2048;
      dirLight.shadow.camera.near = 10;
      dirLight.shadow.camera.far = 300;
      dirLight.shadow.camera.left = -90;
      dirLight.shadow.camera.right = 90;
      dirLight.shadow.camera.top = 90;
      dirLight.shadow.camera.bottom = -90;
      dirLight.shadow.bias = -0.0003;
      scene.add(dirLight);

      // Sun Disc
      const sunGeom = new THREE.SphereGeometry(4.0, 16, 16);
      const sunMat = new THREE.MeshBasicMaterial({ color: 0xfffbeb });
      const sun = new THREE.Mesh(sunGeom, sunMat);
      sun.position.copy(dirLight.position);
      scene.add(sun);

      // 5. Geological Cutaway Slicer Plane
      clipPlaneX = new THREE.Plane(new THREE.Vector3(1, 0, 0), 95.0);

      // 6. Terrain Mesh with Smooth Normals & Satellite Orthophoto Texture
      const segs = 150;
      terrainGeom = new THREE.PlaneGeometry(160, 160, segs, segs);
      terrainGeom.rotateX(-Math.PI / 2);

      const pos = terrainGeom.attributes.position;
      baseHeights = new Float32Array(pos.count);
      for (let i = 0; i < pos.count; i++) {
        const x = pos.getX(i);
        const z = pos.getZ(i);
        const y = getRegionalElevation(x, z);
        baseHeights[i] = y;
        pos.setY(i, y);
      }
      terrainGeom.computeVertexNormals();

      const satTexture = createSatelliteOrthophotoTexture();
      const terrainMat = new THREE.MeshStandardMaterial({
        map: satTexture,
        roughness: 0.94,
        metalness: 0.01,
        side: THREE.DoubleSide,
        clippingPlanes: [clipPlaneX],
        clipShadows: true,
      });

      terrainMesh = new THREE.Mesh(terrainGeom, terrainMat);
      terrainMesh.receiveShadow = true;
      terrainMesh.castShadow = true;
      scene.add(terrainMesh);

      // 7. Subsurface 3D Geological Stratigraphy Blocks
      const waterY = -2.5;

      // Saturated Luni Principal Aquifer Table (glowing cyan water table)
      const waterGeom = new THREE.PlaneGeometry(158, 158, 32, 32);
      waterGeom.rotateX(-Math.PI / 2);
      const waterMat = new THREE.MeshStandardMaterial({
        color: 0x00b4d8,
        roughness: 0.15,
        metalness: 0.60,
        transparent: true,
        opacity: 0.85,
        side: THREE.DoubleSide,
      });
      waterMesh = new THREE.Mesh(waterGeom, waterMat);
      waterMesh.position.y = waterY;
      scene.add(waterMesh);

      // Vadose Zone Murrum Block
      const vadoseGeom = new THREE.BoxGeometry(158, 3.5, 158);
      const vadoseMat = new THREE.MeshStandardMaterial({
        color: 0x854d0e,
        roughness: 0.92,
        side: THREE.DoubleSide,
        clippingPlanes: [clipPlaneX],
      });
      vadoseMesh = new THREE.Mesh(vadoseGeom, vadoseMat);
      vadoseMesh.position.y = waterY - 1.75;
      scene.add(vadoseMesh);

      // Fractured Sandstone & Quartzite Block
      const fracGeom = new THREE.BoxGeometry(158, 3.2, 158);
      const fracMat = new THREE.MeshStandardMaterial({
        color: 0xb45309,
        roughness: 0.88,
        side: THREE.DoubleSide,
        clippingPlanes: [clipPlaneX],
      });
      fracturedMesh = new THREE.Mesh(fracGeom, fracMat);
      fracturedMesh.position.y = waterY - 5.1;
      scene.add(fracturedMesh);

      // Confining Clayey Aquitard Block
      const aquitardGeom = new THREE.BoxGeometry(158, 2.2, 158);
      const aquitardMat = new THREE.MeshStandardMaterial({
        color: 0x475569,
        roughness: 0.92,
        side: THREE.DoubleSide,
        clippingPlanes: [clipPlaneX],
      });
      aquitardMesh = new THREE.Mesh(aquitardGeom, aquitardMat);
      aquitardMesh.position.y = waterY - 7.8;
      scene.add(aquitardMesh);

      // Deep Malani Granite Basement Block
      const bedrockGeom = new THREE.BoxGeometry(158, 4.5, 158);
      const bedrockMat = new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        roughness: 0.96,
        side: THREE.DoubleSide,
        clippingPlanes: [clipPlaneX],
      });
      bedrockMesh = new THREE.Mesh(bedrockGeom, bedrockMat);
      bedrockMesh.position.y = waterY - 11.15;
      scene.add(bedrockMesh);

      // 8. Luni River Water Ribbon (Flat water surface in carved channel)
      const riverPts = [];
      for (let rx = -75; rx <= 42; rx += 2.5) {
        const rz = getRiverZ(rx);
        const ry = getRegionalElevation(rx, rz) + 0.10;
        riverPts.push(new THREE.Vector3(rx, ry, rz));
      }
      const riverCurve = new THREE.CatmullRomCurve3(riverPts);

      // Create flat ribbon geometry along the river spline
      const numPts = 80;
      const ribbonPts = riverCurve.getPoints(numPts);
      const riverGeom = new THREE.BufferGeometry();
      const rVertices = [];
      const rUvs = [];
      const riverWidth = 2.4;

      for (let i = 0; i < ribbonPts.length; i++) {
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
        rUvs.push(0, v);
        rUvs.push(1, v);
      }

      const rIndices = [];
      for (let i = 0; i < ribbonPts.length - 1; i++) {
        const a = i * 2;
        const b = i * 2 + 1;
        const c = (i + 1) * 2;
        const d = (i + 1) * 2 + 1;
        rIndices.push(a, b, c);
        rIndices.push(b, d, c);
      }

      riverGeom.setAttribute('position', new THREE.Float32BufferAttribute(rVertices, 3));
      riverGeom.setAttribute('uv', new THREE.Float32BufferAttribute(rUvs, 2));
      riverGeom.setIndex(rIndices);
      riverGeom.computeVertexNormals();

      const riverWaterMat = new THREE.MeshStandardMaterial({
        color: 0x0284c7,
        roughness: 0.12,
        metalness: 0.60,
        transparent: true,
        opacity: 0.88,
        side: THREE.DoubleSide,
        clippingPlanes: [clipPlaneX],
      });
      riverWaterMesh = new THREE.Mesh(riverGeom, riverWaterMat);
      scene.add(riverWaterMesh);

      // Highway Bridge crossing Luni River near Govindgarh
      const bridgeX = -6, bridgeZ = getRiverZ(bridgeX);
      const bridgeY = getRegionalElevation(bridgeX, bridgeZ) + 1.4;
      const bridgeDeckGeom = new THREE.BoxGeometry(3.6, 0.35, 9.5);
      const concreteMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.85 });
      const bridgeDeck = new THREE.Mesh(bridgeDeckGeom, concreteMat);
      bridgeDeck.position.set(bridgeX, bridgeY, bridgeZ);
      bridgeDeck.castShadow = true;
      scene.add(bridgeDeck);

      // Paved State Highway with Road Markings
      const roadPts = [
        new THREE.Vector3(48, 0, 32),
        new THREE.Vector3(30, 0, 18),
        new THREE.Vector3(12, 0, 8),
        new THREE.Vector3(-6, 0, -2), // Across bridge
        new THREE.Vector3(-24, 0, -10),
        new THREE.Vector3(-42, 0, -16),
        new THREE.Vector3(-60, 0, -26)
      ];
      roadPts.forEach(pt => {
        pt.y = getRegionalElevation(pt.x, pt.z) + 0.12;
      });
      const roadCurve = new THREE.CatmullRomCurve3(roadPts);
      const roadGeom = new THREE.TubeGeometry(roadCurve, 60, 0.65, 4, false);
      const roadMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.92 });
      const roadMesh = new THREE.Mesh(roadGeom, roadMat);
      scene.add(roadMesh);

      // 9. Populated Rural Settlements (Govindgarh, Pushkar, Pisangan, Srinagar)
      settlementGroup = new THREE.Group();
      scene.add(settlementGroup);

      const villages = [
        { name: "Govindgarh", x: -8, z: -2, count: 28 },
        { name: "Pushkar Rural", x: 16, z: 22, count: 22 },
        { name: "Pisangan", x: -32, z: -16, count: 24 },
        { name: "Srinagar", x: 26, z: -8, count: 20 },
      ];

      villages.forEach(v => {
        for (let b = 0; b < v.count; b++) {
          const bx = v.x + (Math.random() - 0.5) * 11;
          const bz = v.z + (Math.random() - 0.5) * 11;
          const by = getRegionalElevation(bx, bz);

          const w = 1.2 + Math.random() * 1.1;
          const h = 1.0 + Math.random() * 0.8;
          const d = 1.2 + Math.random() * 1.1;

          const isWhite = Math.random() > 0.45;
          const houseGeom = new THREE.BoxGeometry(w, h, d);
          const houseMat = new THREE.MeshStandardMaterial({
            color: isWhite ? 0xf8fafc : 0xd4a373,
            roughness: 0.88,
            clippingPlanes: [clipPlaneX],
          });
          const house = new THREE.Mesh(houseGeom, houseMat);
          house.position.set(bx, by + h / 2, bz);
          house.castShadow = true;
          settlementGroup.add(house);

          // Blue Rooftop Water Storage Tank
          if (Math.random() > 0.4) {
            const tankGeom = new THREE.CylinderGeometry(0.18, 0.18, 0.38, 8);
            const tankMat = new THREE.MeshStandardMaterial({ color: 0x0284c7 });
            const tank = new THREE.Mesh(tankGeom, tankMat);
            tank.position.set(bx + 0.2, by + h + 0.19, bz + 0.2);
            settlementGroup.add(tank);
          }
        }

        // Traditional Village Stepwell (Baori)
        const baoriY = getRegionalElevation(v.x + 3.2, v.z + 3.2);
        const baoriGeom = new THREE.CylinderGeometry(1.6, 1.2, 1.3, 8);
        const baoriMat = new THREE.MeshStandardMaterial({ color: 0x64748b, roughness: 0.9 });
        const baori = new THREE.Mesh(baoriGeom, baoriMat);
        baori.position.set(v.x + 3.2, baoriY + 0.2, v.z + 3.2);
        settlementGroup.add(baori);
      });

      // 10. Monitoring Wells with Status-Coded Beacons & Telemetry
      wellGroup = new THREE.Group();
      scene.add(wellGroup);

      const wellLocs = [
        { name: "Govindgarh Well", x: -8, z: -2, status: "Safe", color: 0x10b981 },
        { name: "Pisangan Central", x: -32, z: -16, status: "Critical", color: 0xf97316 },
        { name: "Srinagar Station", x: 26, z: -8, status: "Semi-Critical", color: 0xf59e0b },
        { name: "Pushkar Hydrowell", x: 16, z: 22, status: "Safe", color: 0x10b981 },
        { name: "Saradhna Piezometer", x: 2, z: -22, status: "Safe", color: 0x10b981 },
      ];

      wellLocs.forEach(w => {
        const wy = getRegionalElevation(w.x, w.z);

        // Borehole casing down to aquifer
        const tubeH = Math.max(2.0, wy - waterY + 2.0);
        const tubeGeom = new THREE.CylinderGeometry(0.16, 0.16, tubeH, 8);
        const tubeMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8 });
        const tube = new THREE.Mesh(tubeGeom, tubeMat);
        tube.position.set(w.x, wy - tubeH / 2, w.z);
        tube.castShadow = true;
        wellGroup.add(tube);

        // Concrete Apron
        const apronGeom = new THREE.CylinderGeometry(1.0, 1.2, 0.28, 8);
        const apronMat = new THREE.MeshStandardMaterial({ color: 0x64748b });
        const apron = new THREE.Mesh(apronGeom, apronMat);
        apron.position.set(w.x, wy + 0.14, w.z);
        wellGroup.add(apron);

        // Telemetry Mast & Solar Panel
        const mastGeom = new THREE.CylinderGeometry(0.06, 0.06, 2.0, 6);
        const mastMat = new THREE.MeshStandardMaterial({ color: 0x1e293b });
        const mast = new THREE.Mesh(mastGeom, mastMat);
        mast.position.set(w.x, wy + 1.15, w.z);
        wellGroup.add(mast);

        const panelGeom = new THREE.BoxGeometry(1.0, 0.04, 0.75);
        const panelMat = new THREE.MeshStandardMaterial({ color: 0x1e3a8a, metalness: 0.7 });
        const panel = new THREE.Mesh(panelGeom, panelMat);
        panel.position.set(w.x, wy + 1.9, w.z);
        panel.rotation.x = 0.45;
        wellGroup.add(panel);

        // LED Status Beacon
        const ledGeom = new THREE.SphereGeometry(0.28, 12, 12);
        const ledMat = new THREE.MeshBasicMaterial({ color: w.color });
        const led = new THREE.Mesh(ledGeom, ledMat);
        led.position.set(w.x, wy + 2.3, w.z);
        wellGroup.add(led);
      });

      // 11. Realistic Khejri & Rohida Trees (Organic Multi-Tiered Foliage)
      treeGroup = new THREE.Group();
      scene.add(treeGroup);

      const treeCount = 140;
      const trunkGeom = new THREE.CylinderGeometry(0.14, 0.24, 1.6, 6);
      const trunkMat = new THREE.MeshStandardMaterial({ color: 0x5c2c0e, roughness: 0.95, clippingPlanes: [clipPlaneX] });
      const canopyGeom = new THREE.DodecahedronGeometry(1.1, 1);
      const canopyMat = new THREE.MeshStandardMaterial({ color: 0x3f6212, roughness: 0.85, clippingPlanes: [clipPlaneX] });

      const trunkInst = new THREE.InstancedMesh(trunkGeom, trunkMat, treeCount);
      const canopyInst = new THREE.InstancedMesh(canopyGeom, canopyMat, treeCount);
      const mat4 = new THREE.Matrix4();
      const posV = new THREE.Vector3();
      const quat = new THREE.Quaternion();
      const scaleV = new THREE.Vector3(1, 1, 1);

      let placed = 0;
      for (let t = 0; t < treeCount; t++) {
        const tx = (Math.random() - 0.5) * 120;
        const tz = (Math.random() - 0.5) * 120;
        const ty = getRegionalElevation(tx, tz);
        if (ty < 8.0) { // On plains and fields
          posV.set(tx, ty + 0.8, tz);
          mat4.compose(posV, quat, scaleV);
          trunkInst.setMatrixAt(placed, mat4);

          posV.set(tx, ty + 1.8, tz);
          mat4.compose(posV, quat, scaleV);
          canopyInst.setMatrixAt(placed, mat4);
          placed++;
        }
      }
      trunkInst.count = placed;
      canopyInst.count = placed;
      trunkInst.castShadow = true;
      treeGroup.add(trunkInst);
      treeGroup.add(canopyInst);

      // 12. 3D Darcy Groundwater Flow Particles
      const pCount = 350;
      const pGeom = new THREE.BufferGeometry();
      const pPos = new Float32Array(pCount * 3);
      for (let p = 0; p < pCount; p++) {
        pPos[p * 3 + 0] = (Math.random() - 0.5) * 140;
        pPos[p * 3 + 1] = waterY + 0.05;
        pPos[p * 3 + 2] = (Math.random() - 0.5) * 140;
      }
      pGeom.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
      const pMat = new THREE.PointsMaterial({ color: 0x00f5ff, size: 0.38, transparent: true, opacity: 0.85 });
      flowParticles = new THREE.Points(pGeom, pMat);
      scene.add(flowParticles);

      // 13. Drifting Clouds
      cloudGroup = new THREE.Group();
      scene.add(cloudGroup);
      const cloudPuffGeom = new THREE.DodecahedronGeometry(5.5, 1);
      const cloudMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.95, transparent: true, opacity: 0.70 });
      for (let c = 0; c < 12; c++) {
        const puff = new THREE.Mesh(cloudPuffGeom, cloudMat);
        puff.position.set((Math.random() - 0.5) * 150, 42 + Math.random() * 10, (Math.random() - 0.5) * 150);
        puff.scale.set(1.8 + Math.random() * 1.2, 0.6 + Math.random() * 0.4, 1.2 + Math.random() * 0.8);
        cloudGroup.add(puff);
      }

      // Render Loop
      let clock = new THREE.Clock();
      function animate() {
        requestAnimationFrame(animate);
        const delta = clock.getDelta();
        const elapsed = clock.getElapsedTime();

        // Animate groundwater flow along regional hydraulic gradient
        if (flowParticles) {
          const arr = flowParticles.geometry.attributes.position.array;
          for (let i = 0; i < pCount; i++) {
            arr[i * 3 + 0] -= 0.05;
            arr[i * 3 + 2] -= 0.035;
            if (arr[i * 3 + 0] < -70) arr[i * 3 + 0] = 70;
            if (arr[i * 3 + 2] < -70) arr[i * 3 + 2] = 70;
          }
          flowParticles.geometry.attributes.position.needsUpdate = true;
        }

        // Drifting clouds
        if (cloudGroup) {
          cloudGroup.children.forEach(c => {
            c.position.x += delta * 1.2;
            if (c.position.x > 85) c.position.x = -85;
          });
        }

        controls.update();
        renderer.render(scene, camera);
      }
      animate();
    }

    function applyCameraPreset(preset) {
      document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
      const btn = document.getElementById('btn-' + preset);
      if (btn) btn.classList.add('active');

      if (preset === 'iso') {
        camera.position.set(15, 62, 82);
        controls.target.set(-8, 0, -8);
      } else if (preset === 'basin') {
        camera.position.set(0, 110, 100);
        controls.target.set(0, 0, 0);
      } else if (preset === 'top') {
        camera.position.set(0, 130, 0.001);
        controls.target.set(0, 0, 0);
      } else if (preset === 'oblique') {
        camera.position.set(45, 18, 55);
        controls.target.set(-8, 2, -8);
      } else if (preset === 'cutaway') {
        camera.position.set(40, 24, -40);
        controls.target.set(0, -3, 0);
        applyCutawayMode('partial');
      } else if (preset === 'settle') {
        camera.position.set(-8 + 14, 11, -2 + 14);
        controls.target.set(-8, 2, -2);
      } else if (preset === 'river') {
        camera.position.set(8, 16, 10);
        controls.target.set(-16, 1.5, -4);
      }
    }

    function applyCutawayMode(mode) {
      document.getElementById('cutaway-select').value = mode;
      const sliceSlider = document.getElementById('slice-slider');
      const sliceVal = document.getElementById('slice-val');
      if (mode === 'complete') {
        clipPlaneX.constant = 95.0;
        sliceSlider.value = 0;
        sliceVal.innerText = '0%';
        terrainMesh.visible = true;
      } else if (mode === 'partial') {
        clipPlaneX.constant = 20.0;
        sliceSlider.value = 35;
        sliceVal.innerText = '35%';
        terrainMesh.visible = true;
      } else if (mode === 'full') {
        clipPlaneX.constant = 0.0;
        sliceSlider.value = 50;
        sliceVal.innerText = '50%';
        terrainMesh.visible = true;
      } else if (mode === 'cross') {
        clipPlaneX.constant = -6.0;
        sliceSlider.value = 55;
        sliceVal.innerText = '55%';
        terrainMesh.visible = true;
      } else if (mode === 'groundwater') {
        terrainMesh.visible = false;
      }
    }

    function onSliceInput(val) {
      const pct = parseFloat(val);
      document.getElementById('slice-val').innerText = pct + '%';
      clipPlaneX.constant = 90.0 - (pct / 100.0) * 170.0;
    }

    function onExaggerationInput(val) {
      const factor = parseFloat(val);
      document.getElementById('exaggeration-val').innerText = factor.toFixed(1) + 'x';
      if (!terrainGeom) return;
      const pos = terrainGeom.attributes.position;
      for (let i = 0; i < pos.count; i++) {
        pos.setY(i, baseHeights[i] * (factor / 1.2));
      }
      pos.needsUpdate = true;
      terrainGeom.computeVertexNormals();
    }

    function setAmbiance(mode) {
      document.querySelectorAll('.action-btn').forEach(b => {
        if (b.id && b.id.startsWith('amb-')) b.classList.remove('active');
      });
      const btn = document.getElementById('amb-' + mode);
      if (btn) btn.classList.add('active');

      if (mode === 'day') {
        scene.background.set(0xbae6fd);
        scene.fog.color.set(0xfef3c7);
      } else if (mode === 'sunset') {
        scene.background.set(0xf97316);
        scene.fog.color.set(0xea580c);
      } else if (mode === 'night') {
        scene.background.set(0x070b14);
        scene.fog.color.set(0x070b14);
      }
    }

    function toggleLayerDrawer() {
      const p = document.getElementById('layer-panel');
      p.classList.toggle('open');
    }

    function updateLayers() {
      if (terrainMesh) terrainMesh.visible = document.getElementById('chk-terrain').checked;
      const showStrata = document.getElementById('chk-strata').checked;
      if (vadoseMesh) vadoseMesh.visible = showStrata;
      if (fracturedMesh) fracturedMesh.visible = showStrata;
      if (aquitardMesh) aquitardMesh.visible = showStrata;
      if (bedrockMesh) bedrockMesh.visible = showStrata;
      if (waterMesh) waterMesh.visible = document.getElementById('chk-water').checked;
      if (riverWaterMesh) riverWaterMesh.visible = document.getElementById('chk-river').checked;
      if (wellGroup) wellGroup.visible = document.getElementById('chk-wells').checked;
      if (settlementGroup) settlementGroup.visible = document.getElementById('chk-settle').checked;
      if (treeGroup) treeGroup.visible = document.getElementById('chk-trees').checked;
      if (flowParticles) flowParticles.visible = document.getElementById('chk-flow').checked;
    }

    window.addEventListener('DOMContentLoaded', initEngine);
  </script>
</body>
</html>
"""

with open(r"D:\NIH_roorkee\FULL WORK FINAL_DIGITAL_NAYA_PANI\NAYA_PAANI\scratch\prototype_v3.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Saved scratch/prototype_v3.html successfully!")
