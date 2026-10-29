import sys
from pathlib import Path

p = Path(r"D:\NIH_roorkee\FULL WORK FINAL_DIGITAL_NAYA_PANI\NAYA_PAANI\digital_twin.py")
text = p.read_text(encoding="utf-8")

# 1. Update CSS in template for fullscreen
css_old = "#desert-canvas-wrap { position: relative; width: 100%; height: 760px; overflow: hidden; background: #070b14; user-select: none; }"
css_new = """#desert-canvas-wrap { position: relative; width: 100%; height: 760px; overflow: hidden; background: #070b14; user-select: none; }
    :fullscreen #desert-canvas-wrap, :-webkit-full-screen #desert-canvas-wrap { width: 100vw !important; height: 100vh !important; border-radius: 0 !important; }
    :fullscreen #three-canvas, :-webkit-full-screen #three-canvas { width: 100vw !important; height: 100vh !important; }"""
assert css_old in text, "css_old not found"
text = text.replace(css_old, css_new, 1)

# 2. Update Top Actions toolbar for Fullscreen & Dedicated Tab buttons
act_old = """    <div class="top-actions">
      <button class="action-btn" id="btn-rain" onclick="toggleRainSimulation()">🌧️ Rain Simulation</button>"""
act_new = """    <div class="top-actions">
      <button class="action-btn" id="btn-fullscreen" onclick="toggleFullScreen()" title="Toggle Full Screen (F11 / Esc to exit)">⛶ Full Screen</button>
      <button class="action-btn" id="btn-tab" onclick="openFullTab()" title="Open Stage in Dedicated Browser Window">↗ Dedicated Window</button>
      <button class="action-btn" id="btn-rain" onclick="toggleRainSimulation()">🌧️ Rain Simulation</button>"""
assert act_old in text, "act_old not found"
text = text.replace(act_old, act_new, 1)

# 3. Update Layer Panel: change grass to scrub
layer_old = '<label class="layer-item"><input type="checkbox" id="layer-grass" checked onchange="toggleLayer(\'grass\')"> <span>3D Grass Cover</span></label>'
layer_new = '<label class="layer-item"><input type="checkbox" id="layer-scrub" checked onchange="toggleLayer(\'scrub\')"> <span>Desert Scrub & Flora</span></label>'
assert layer_old in text, "layer_old not found"
text = text.replace(layer_old, layer_new, 1)

# 4. Update JS variables
var_old = "let wellGroup, settlementGroup, treeGroup, grassGroup, riverWaterMesh, lakeGroup, activityGroup;"
var_new = "let wellGroup, settlementGroup, treeGroup, scrubGroup, riverWaterMesh, lakeGroup, activityGroup;"
assert var_old in text, "var_old not found"
text = text.replace(var_old, var_new, 1)

# 5. Replace Tree and Grass section with Photorealistic Multi-Species Trees & Authentic Desert Scrub
start_marker = "      // Load User 3D OBJ Tree Model"
end_marker = "      // 13. Subsurface Stratigraphy Blocks & Hydrogeological Cutaway"

idx_start = text.find(start_marker)
idx_end = text.find(end_marker)
assert idx_start != -1 and idx_end != -1, f"Markers not found: {idx_start}, {idx_end}"

tree_start_marker = "      const treePositions = [];"
idx_tree_start = text.rfind(tree_start_marker, 0, idx_start)
assert idx_tree_start != -1, "treePositions marker not found"

new_vegetation_code = """      const assetBasePath = (window.location.protocol === 'file:') ? '../static/' : '/app/static/';
      const mtlLoader = new THREE.MTLLoader();
      mtlLoader.setPath(assetBasePath);
      mtlLoader.setResourcePath(assetBasePath);
      mtlLoader.setCrossOrigin('anonymous');

      const treePositions = [];
      // 1. Riparian tree groves along Luni River corridor (dense green belt)
      for (let t = 0; t < 65; t++) {
        const u = (Math.random() * 2 - 1);
        const rx = u * 45;
        const rz = rx * 0.95 + (Math.random() - 0.5) * 10;
        const ry = getRegionalElevation(rx, rz);
        if (ry > 0.05 && ry < 2.0) {
          treePositions.push({
            x: rx, y: ry, z: rz,
            scale: 0.16 + Math.random() * 0.12,
            rot: Math.random() * Math.PI * 2,
            type: (t % 2 === 0) ? 'sonnerat' : 'walnut'
          });
        }
      }
      // 2. Settlement & Oasis trees around villages
      for (let s = 0; s < SETTLEMENTS.length; s++) {
        const st = SETTLEMENTS[s];
        for (let j = 0; j < 8; j++) {
          const ang = Math.random() * Math.PI * 2;
          const dist = 3.5 + Math.random() * 7.0;
          const tx = st.x + Math.cos(ang) * dist;
          const tz = st.z + Math.sin(ang) * dist;
          const ty = getRegionalElevation(tx, tz);
          treePositions.push({
            x: tx, y: ty, z: tz,
            scale: 0.18 + Math.random() * 0.14,
            rot: Math.random() * Math.PI * 2,
            type: (j % 2 === 0) ? 'sonnerat' : 'walnut'
          });
        }
      }
      // 3. Scattered drought-hardy Khejri trees across interdunal plains
      for (let k = 0; k < 45; k++) {
        const kx = (Math.random() - 0.5) * 120;
        const kz = (Math.random() - 0.5) * 120;
        const ky = getRegionalElevation(kx, kz);
        if (ky > 0.2 && ky < 3.0) {
          treePositions.push({
            x: kx, y: ky, z: kz,
            scale: 0.14 + Math.random() * 0.10,
            rot: Math.random() * Math.PI * 2,
            type: 'sonnerat'
          });
        }
      }

      function spawnProceduralTrees(targetType) {
        const targetPositions = treePositions.filter(tp => tp.type === targetType);
        if (!targetPositions.length) return;
        const tCount = targetPositions.length;
        const trunkGeom = new THREE.CylinderGeometry(0.12, 0.22, 1.4, 6);
        const trunkMat = new THREE.MeshStandardMaterial({ color: 0x3f2d1c, roughness: 0.95, clippingPlanes: [clipPlaneX] });
        const canopyGeom1 = new THREE.CylinderGeometry(0.95, 0.65, 0.40, 8);
        const canopyGeom2 = new THREE.CylinderGeometry(0.70, 0.40, 0.32, 8);
        const canopyMat = new THREE.MeshStandardMaterial({ color: targetType === 'sonnerat' ? 0x365314 : 0x2d4a1d, roughness: 0.92, clippingPlanes: [clipPlaneX] });
        const canopyMatTop = new THREE.MeshStandardMaterial({ color: targetType === 'sonnerat' ? 0x3f6212 : 0x365d24, roughness: 0.90, clippingPlanes: [clipPlaneX] });

        const trunkInst = new THREE.InstancedMesh(trunkGeom, trunkMat, tCount);
        const c1Inst = new THREE.InstancedMesh(canopyGeom1, canopyMat, tCount);
        const c2Inst = new THREE.InstancedMesh(canopyGeom2, canopyMatTop, tCount);
        const mat = new THREE.Matrix4();
        const posV = new THREE.Vector3();
        const quat = new THREE.Quaternion();
        const scV = new THREE.Vector3(1, 1, 1);

        for (let i = 0; i < tCount; i++) {
          const tp = targetPositions[i];
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
        }
        trunkInst.castShadow = true;
        treeGroup.add(trunkInst);
        treeGroup.add(c1Inst);
        treeGroup.add(c2Inst);
      }

      function load3DTreeSpecies(mtlFile, objFile, speciesType) {
        if (!THREE.OBJLoader || !THREE.MTLLoader) {
          spawnProceduralTrees(speciesType);
          return;
        }
        mtlLoader.load(mtlFile, (materials) => {
          materials.preload();
          const objLoader = new THREE.OBJLoader();
          objLoader.setMaterials(materials);
          objLoader.setPath(assetBasePath);
          objLoader.load(objFile, (objModel) => {
            console.log('Real 3D Tree (' + speciesType + ') loaded successfully!');
            objModel.traverse((child) => {
              if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
                if (child.material) {
                  child.material.clippingPlanes = [clipPlaneX];
                  child.material.side = THREE.DoubleSide;
                  child.material.roughness = 0.85;
                  child.material.metalness = 0.05;
                }
              }
            });
            treePositions.filter(tp => tp.type === speciesType).forEach(tp => {
              const clone = objModel.clone();
              clone.position.set(tp.x, tp.y, tp.z);
              clone.scale.set(tp.scale, tp.scale, tp.scale);
              clone.rotation.y = tp.rot;
              treeGroup.add(clone);
            });
          }, undefined, (err) => {
            console.warn('OBJLoader failed for ' + speciesType, err);
            spawnProceduralTrees(speciesType);
          });
        }, undefined, (err) => {
          console.warn('MTLLoader failed for ' + speciesType, err);
          spawnProceduralTrees(speciesType);
        });
      }

      load3DTreeSpecies('tree_sonnerat.mtl', 'tree_sonnerat.obj', 'sonnerat');
      load3DTreeSpecies('tree_walnut.mtl', 'tree_walnut.obj', 'walnut');

      // 12. Authentic Thar Desert Xerophytic Scrub (Capparis decidua / Kair bushes)
      // Low rounded desert scrub clusters hugging dune swales - NO giant upright leaves!
      scrubGroup = new THREE.Group();
      scene.add(scrubGroup);

      const scrubGeom = new THREE.DodecahedronGeometry(0.55, 1);
      scrubGeom.scale(1.2, 0.55, 1.1);

      const scrubMat = new THREE.MeshStandardMaterial({
        color: 0x5a6838,
        roughness: 0.96,
        metalness: 0.02,
        clippingPlanes: [clipPlaneX],
      });

      const scrubCount = 280;
      const scrubInst = new THREE.InstancedMesh(scrubGeom, scrubMat, scrubCount);
      const sMat = new THREE.Matrix4();
      const sPos = new THREE.Vector3();
      const sQuat = new THREE.Quaternion();
      const sSc = new THREE.Vector3(1, 1, 1);

      let sPlaced = 0;
      for (let s = 0; s < scrubCount; s++) {
        const sx = (Math.random() - 0.5) * 125;
        const sz = (Math.random() - 0.5) * 125;
        const sy = getRegionalElevation(sx, sz);
        if (sy > 0.1 && sy < 3.2) {
          const sc = 0.5 + Math.random() * 0.7;
          sSc.set(sc, sc * (0.8 + Math.random() * 0.4), sc);
          sPos.set(sx, sy + 0.18 * sc, sz);
          sQuat.setFromAxisAngle(new THREE.Vector3(0, 1, 0), Math.random() * Math.PI * 2);
          sMat.compose(sPos, sQuat, sSc);
          scrubInst.setMatrixAt(sPlaced, sMat);
          sPlaced++;
        }
      }
      scrubInst.count = sPlaced;
      scrubInst.castShadow = true;
      scrubGroup.add(scrubInst);

"""
text = text[:idx_tree_start] + new_vegetation_code + text[idx_end:]

# 6. Update toggleLayer & add Fullscreen functions
old_toggle = "      else if (layer === 'trees') treeGroup.visible = v;\n      else if (layer === 'grass') grassGroup.visible = v;"
new_toggle = "      else if (layer === 'trees') treeGroup.visible = v;\n      else if (layer === 'scrub') scrubGroup.visible = v;"
assert old_toggle in text, "old_toggle not found"
text = text.replace(old_toggle, new_toggle, 1)

old_close = """    function closeWellCard() {
      document.getElementById('well-card').style.display = 'none';
    }"""
new_close = """    function closeWellCard() {
      document.getElementById('well-card').style.display = 'none';
    }

    // Full Screen & Dedicated Window Handlers
    function toggleFullScreen() {
      const wrap = document.getElementById('desert-canvas-wrap') || document.documentElement;
      if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.mozFullScreenElement && !document.msFullscreenElement) {
        if (wrap.requestFullscreen) {
          wrap.requestFullscreen().catch(() => openFullTab());
        } else if (wrap.webkitRequestFullscreen) {
          wrap.webkitRequestFullscreen();
        } else if (wrap.mozRequestFullScreen) {
          wrap.mozRequestFullScreen();
        } else if (wrap.msRequestFullscreen) {
          wrap.msRequestFullscreen();
        }
      } else {
        if (document.exitFullscreen) {
          document.exitFullscreen().catch(() => {});
        } else if (document.webkitExitFullscreen) {
          document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
          document.mozCancelFullScreen();
        } else if (document.msExitFullscreen) {
          document.msExitFullscreen();
        }
      }
    }

    function openFullTab() {
      window.open('/app/static/twin_fullscreen.html', '_blank');
    }

    function onFsChange() {
      const isFs = Boolean(document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement);
      const btn = document.getElementById('btn-fullscreen');
      if (btn) btn.innerHTML = isFs ? '🗗 Exit Full Screen' : '⛶ Full Screen';
      setTimeout(onWindowResize, 100);
      setTimeout(onWindowResize, 300);
    }
    document.addEventListener('fullscreenchange', onFsChange);
    document.addEventListener('webkitfullscreenchange', onFsChange);
    document.addEventListener('mozfullscreenchange', onFsChange);
    document.addEventListener('MSFullscreenChange', onFsChange);"""
assert old_close in text, "old_close not found"
text = text.replace(old_close, new_close, 1)

# 7. Update _render_threejs_desert_twin to write static/twin_fullscreen.html and add link button
render_old = "    components.html(rendered_html, height=760)"
render_new = """    # Persist standalone fullscreen HTML for direct tab opening and ultra-low latency rendering
    try:
        from pathlib import Path as _P
        fs_path = _P(__file__).resolve().parent / "static" / "twin_fullscreen.html"
        fs_path.write_text(rendered_html, encoding="utf-8")
    except Exception:
        pass

    col_fs1, col_fs2 = st.columns([2.8, 1.2])
    with col_fs1:
        st.caption("🎮 **Real-time 3D Three.js Engine**: Drag to orbit, right-drag to pan, scroll to zoom. Use top buttons for camera presets and lighting.")
    with col_fs2:
        st.link_button(
            "⛶ Open Fullscreen 3D Twin",
            url="/app/static/twin_fullscreen.html",
            use_container_width=True,
            type="primary",
            help="Open the 3D digital twin in a dedicated, borderless browser tab with native monitor fullscreen support.",
        )

    components.html(rendered_html, height=760)"""
assert render_old in text, "render_old not found"
text = text.replace(render_old, render_new, 1)

p.write_text(text, encoding="utf-8")
print("SUCCESS: digital_twin.py fully transformed!")
