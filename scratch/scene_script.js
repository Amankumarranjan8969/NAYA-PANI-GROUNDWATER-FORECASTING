
    const CFG = {"season": "Monsoon", "year": 2022, "district": "Ajmer", "block": "Srinagar", "selectedVillage": "All Monitoring Wells (Basin Aggregate)", "mode": "Simulated", "dtwl": 8.08, "rainfall": 45.0, "et": 3.2, "soil": 18.0, "stressCat": "Safe", "stressColor": "#10b981", "lat": 26.45, "lon": 74.63, "elev": 480.0, "wells": [], "initialPreset": "\ud83d\udcd0 Elevated Isometric View (Default)", "initialCutaway": "Complete Surface Landscape", "initialExaggeration": 1.5, "initialAmbiance": "\u2600\ufe0f High Noon Thar Sun"};
    const wrap = document.getElementById('desert-canvas-wrap');
    const canvas = document.getElementById('three-canvas');
    const loader = document.getElementById('loading-indicator');
    const tooltip = document.getElementById('well-tooltip');

    if (typeof THREE === 'undefined') {
      loader.innerHTML = '<span style="color:#ef4444;">WebGL / Three.js library loading... Please check connection or use Plotly tab.</span>';
    } else {
      initDesertScene();
    }

    let scene, camera, renderer, controls;
    let terrainMesh, terrainGeom, baseHeights = [];
    let waterMesh, vadoseMesh, fracturedMesh, aquitardMesh, bedrockMesh;
    let clipPlaneX;
    let dustParticles, rainParticles, flowParticles, cloudGroup, wildlifeGroup;
    let wellGroup, floraGroup, riverGroup, settlementGroup, farmGroup, roadGroup;
    let raycaster, mouse;
    let activeSelectedWell = CFG.selectedVillage;
    let selectedWellCoords = { x: 0, y: 0, z: 0 };

    // Camera Animation State
    let isAnimatingCamera = false;
    let camStartPos = new THREE.Vector3(), camEndPos = new THREE.Vector3();
    let camStartTarget = new THREE.Vector3(), camEndTarget = new THREE.Vector3();
    let animStartTime = 0, animDuration = 1200;

    // Lighting & Atmosphere
    let dirLight, hemiLight, ambLight, sunSphere;
    let currentAmbiance = 'day';

    function initDesertScene() {
      loader.style.display = 'none';
      const w = wrap.clientWidth || 800;
      const h = wrap.clientHeight || 760;

      // 1. Scene & Elevated Isometric Camera Setup (50 km scope)
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0xfef3c7);
      scene.fog = new THREE.FogExp2(0xfef3c7, 0.0055);

      camera = new THREE.PerspectiveCamera(40, w / h, 0.5, 600);
      // Default Elevated Isometric View (~35 deg pitch downward, 45 deg azimuth, framing entire 150-unit 50km extent)
      camera.position.set(68, 52, 68);

      // 2. WebGL Renderer with Soft Shadow Mapping & Local Clipping
      renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: false, powerPreference: "high-performance" });
      renderer.setSize(w, h);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      renderer.localClippingEnabled = true;

      // 3. OrbitControls
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.maxPolarAngle = Math.PI / 2 - 0.02;
      controls.minDistance = 8;
      controls.maxDistance = 280;
      controls.target.set(0, 0, 0);

      // 4. Photorealistic Solar Lighting System
      hemiLight = new THREE.HemisphereLight(0xffedd5, 0x78350f, 0.70);
      scene.add(hemiLight);

      ambLight = new THREE.AmbientLight(0xffedd5, 0.25);
      scene.add(ambLight);

      dirLight = new THREE.DirectionalLight(0xfffbeb, 1.45);
      dirLight.position.set(70, 95, 55);
      dirLight.castShadow = true;
      dirLight.shadow.mapSize.width = 2048;
      dirLight.shadow.mapSize.height = 2048;
      dirLight.shadow.camera.near = 10;
      dirLight.shadow.camera.far = 320;
      dirLight.shadow.camera.left = -90;
      dirLight.shadow.camera.right = 90;
      dirLight.shadow.camera.top = 90;
      dirLight.shadow.camera.bottom = -90;
      dirLight.shadow.bias = -0.0004;
      scene.add(dirLight);

      // Sun Visible Disc
      const sunGeom = new THREE.SphereGeometry(4.5, 16, 16);
      const sunMat = new THREE.MeshBasicMaterial({ color: 0xfffbeb });
      sunSphere = new THREE.Mesh(sunGeom, sunMat);
      sunSphere.position.copy(dirLight.position);
      scene.add(sunSphere);

      // 5. Geological Cutaway Slicer Plane (Horizontal Extent: -75 to +75)
      clipPlaneX = new THREE.Plane(new THREE.Vector3(1, 0, 0), 90.0);

      // 6. Regional 50 km Continuous Terrain Mesh (150 x 150 units, 150x150 segments = 22,801 vertices)
      buildRegional50kmTerrain();

      // 7. Subsurface 3D Geological Stratigraphy (6 Solid Strata Blocks)
      const waterY = Math.max(-6.5, 1.0 - (CFG.dtwl / 18.0));
      buildSubsurfaceStratigraphy(waterY);

      // 8. Dynamic Luni River Network, Tributaries & Highway Bridge
      riverGroup = new THREE.Group();
      scene.add(riverGroup);
      buildLuniRiverNetwork();

      // 9. Populated Human Settlements, Architecture & Roadways
      settlementGroup = new THREE.Group();
      scene.add(settlementGroup);
      roadGroup = new THREE.Group();
      scene.add(roadGroup);
      buildSettlementsAndRoads();

      // 10. Agricultural Land Mosaic, Tube-Well Pump Houses & Solar Pumping Arrays
      farmGroup = new THREE.Group();
      scene.add(farmGroup);
      buildFarmsAndSolarPumps();

      // 11. Monitoring Well Piezometers (Real WGS84 Geodesic Placement)
      wellGroup = new THREE.Group();
      scene.add(wellGroup);
      instantiateMonitoringWells(waterY);

      // 12. Thar Desert Xerophytic Ecosystem & Flora (Khejri, Rohida, Sewan Grass)
      floraGroup = new THREE.Group();
      scene.add(floraGroup);
      buildTharFlora();

      // 13. Dynamic Atmosphere, Layered Drifting Clouds, Wildlife & Rain Simulation
      cloudGroup = new THREE.Group();
      scene.add(cloudGroup);
      wildlifeGroup = new THREE.Group();
      scene.add(wildlifeGroup);
      buildCloudsAndAtmosphere();
      buildWildlife();
      createFlowParticles(waterY);
      createDustParticles();
      createRainParticles();

      // 14. Raycasting & User Interaction
      raycaster = new THREE.Raycaster();
      mouse = new THREE.Vector2();
      window.addEventListener('resize', onWindowResize);
      wrap.addEventListener('mousemove', onMouseMove);
      wrap.addEventListener('click', onCanvasClick);

      // Apply initial settings
      applyAmbiance(CFG.initialAmbiance);
      if (CFG.initialCutaway && CFG.initialCutaway !== 'Complete Surface Landscape') {
        if (CFG.initialCutaway.includes('Partial')) applyCutawayMode('partial');
        else if (CFG.initialCutaway.includes('Full')) applyCutawayMode('full');
        else if (CFG.initialCutaway.includes('Cross')) applyCutawayMode('cross');
        else if (CFG.initialCutaway.includes('Groundwater')) applyCutawayMode('groundwater');
        else if (CFG.initialCutaway.includes('Combined')) applyCutawayMode('combined');
      }

      // Animation Render Loop
      let clock = new THREE.Clock();
      function animate() {
        requestAnimationFrame(animate);
        const delta = clock.getDelta();
        const elapsed = clock.getElapsedTime();

        // Smooth camera tweening
        if (isAnimatingCamera) {
          const progress = (performance.now() - animStartTime) / animDuration;
          if (progress >= 1.0) {
            camera.position.copy(camEndPos);
            controls.target.copy(camEndTarget);
            isAnimatingCamera = false;
          } else {
            const ease = 1.0 - Math.pow(1.0 - progress, 3); // Cubic ease out
            camera.position.lerpVectors(camStartPos, camEndPos, ease);
            controls.target.lerpVectors(camStartTarget, camEndTarget, ease);
          }
        }

        // River water normal ripples animation
        if (riverGroup && riverGroup.userData.waterMaterial) {
          riverGroup.userData.waterMaterial.opacity = (CFG.rainfall > 20) ? 0.90 : 0.75;
        }

        // Drifting Clouds
        if (cloudGroup && cloudGroup.visible) {
          cloudGroup.children.forEach((cloud, i) => {
            cloud.position.x += delta * (0.8 + i * 0.1);
            if (cloud.position.x > 85) cloud.position.x = -85;
          });
        }

        // Soaring Wildlife (Eagles circling thermal currents over Aravalli ridges)
        if (wildlifeGroup && wildlifeGroup.visible) {
          wildlifeGroup.children.forEach((bird, i) => {
            const angle = elapsed * 0.45 + i * 2.1;
            const radius = 18 + i * 6;
            bird.position.x = 35 + Math.cos(angle) * radius;
            bird.position.z = 10 + Math.sin(angle) * radius;
            bird.position.y = 28 + Math.sin(elapsed * 0.8 + i) * 2.5;
            bird.rotation.y = -angle - Math.PI / 2;
          });
        }

        // Dynamic 3D Groundwater Darcy Flow Particles
        if (flowParticles && flowParticles.visible) {
          const fPos = flowParticles.geometry.attributes.position.array;
          for (let i = 0; i < 400; i++) {
            // Regional hydraulic gradient flow from NE to SW
            fPos[i * 3 + 0] -= 0.055;
            fPos[i * 3 + 2] -= 0.038;
            fPos[i * 3 + 1] = waterY + 0.04 + Math.sin(fPos[i * 3 + 0] * 0.2) * 0.03;
            if (fPos[i * 3 + 0] < -70) fPos[i * 3 + 0] = 70;
            if (fPos[i * 3 + 2] < -70) fPos[i * 3 + 2] = 70;
          }
          flowParticles.geometry.attributes.position.needsUpdate = true;
        }

        // Drifting Desert Sand Dust
        if (dustParticles && dustParticles.visible) {
          const dPos = dustParticles.geometry.attributes.position.array;
          for (let i = 0; i < 450; i++) {
            dPos[i * 3 + 0] += 0.06;
            dPos[i * 3 + 2] += 0.04;
            if (dPos[i * 3 + 0] > 75) dPos[i * 3 + 0] = -75;
            if (dPos[i * 3 + 2] > 75) dPos[i * 3 + 2] = -75;
          }
          dustParticles.geometry.attributes.position.needsUpdate = true;
        }

        // Rainfall animation if active
        if (rainParticles && rainParticles.visible) {
          const rPos = rainParticles.geometry.attributes.position.array;
          for (let i = 0; i < 500; i++) {
            rPos[i * 3 + 1] -= 0.85;
            if (rPos[i * 3 + 1] < -2) rPos[i * 3 + 1] = 60;
          }
          rainParticles.geometry.attributes.position.needsUpdate = true;
        }

        // Update North compass rose rotation
        const compass = document.getElementById('compass-rose');
        if (compass && controls) {
          const az = controls.getAzimuthalAngle();
          compass.style.transform = `rotate(${-az}rad)`;
        }

        controls.update();
        renderer.render(scene, camera);
      }
      animate();
    }

    // -------------------------------------------------------------
    // REGIONAL GEOMORPHOLOGY & ELEVATION SAMPLING (50 km Territory)
    // -------------------------------------------------------------
    function sampleRegionalElevationRaw(x, z) {
      // 1. Regional topographic slope (Luni basin drainage tilts NE down towards SW)
      const baseTilt = (-x * 0.045 + z * 0.035);

      // 2. Aravalli Mountain Range (East & Southeast sector: x > -15, aligned NE-SW)
      let aravalli = 0;
      if (x > -18) {
        // Ridge axis 1 (Main Aravalli Strike Ridge)
        const dRidge1 = Math.abs(x - 30 - Math.sin(z * 0.07) * 14);
        const r1 = Math.max(0, 1.0 - dRidge1 / 15.0);
        const h1 = Math.pow(r1, 1.7) * 19.5;

        // Ridge axis 2 (Secondary Parallel Ridge)
        const dRidge2 = Math.abs(x - 52 - Math.cos(z * 0.06) * 10);
        const r2 = Math.max(0, 1.0 - dRidge2 / 14.0);
        const h2 = Math.pow(r2, 1.7) * 22.0;

        // Transverse gullies, saddle gaps & crags
        const crags = Math.sin(z * 0.25) * Math.cos(x * 0.18) * 2.2;
        aravalli = (h1 + h2 + (h1 > 1.0 || h2 > 1.0 ? crags : 0));
      }

      // 3. Luni Ephemeral River Channel Incision
      const riverCenterZ = getLuniRiverCenterZ(x);
      const dRiv = Math.abs(z - riverCenterZ);
      let riverIncision = 0;
      if (dRiv < 6.5 && x < 45) {
        riverIncision = -Math.pow(1.0 - dRiv / 6.5, 2) * 2.5;
      }

      // 4. Western Thar Aeolian Dunefield (West & Northwest sector: x < 20)
      let dunes = 0;
      if (x < 22) {
        const u = (x * 0.78 + z * 0.62) * 0.14;
        const v = (-x * 0.62 + z * 0.78) * 0.14;
        // Longitudinal Seif dunes
        const seif = 2.4 * Math.sin(v * 4.2 + 0.35 * Math.sin(u * 2.6));
        // Asymmetric Barchan dunes
        const barchan = 1.7 * (Math.sin(u * 5.2) + 0.3 * Math.sin(u * 10.4));
        // Interdunal deflation swales
        const swale = -1.2 * Math.cos(v * 2.0);
        const duneWeight = Math.max(0, Math.min(1.0, (22 - x) / 50.0));
        dunes = (seif + barchan + swale) * duneWeight;
      }

      // 5. Undulating central alluvial pediment plain
      const pediment = 1.4 * Math.sin(x * 0.06) * Math.cos(z * 0.06) + 2.0;

      return baseTilt + aravalli + riverIncision + dunes + pediment;
    }

    function sampleRegionalElevation(x, z) {
      const exag = parseFloat(document.getElementById('exaggeration-slider') ? document.getElementById('exaggeration-slider').value : 1.5);
      return sampleRegionalElevationRaw(x, z) * exag;
    }

    function getLuniRiverCenterZ(x) {
      // Sinuous Luni river channel from Aravalli origins through Govindgarh to SW
      return 6.5 * Math.sin(x * 0.065) - 0.55 * x - 3.5;
    }

    // -------------------------------------------------------------
    // 6. BUILD REGIONAL 50 KM TERRAIN MESH WITH MULTI-ZONE SHADING
    // -------------------------------------------------------------
    function buildRegional50kmTerrain() {
      // 150x150 world extent = 100 km diameter (50 km radius circular area)
      const segments = 140;
      terrainGeom = new THREE.PlaneGeometry(150, 150, segments, segments);
      terrainGeom.rotateX(-Math.PI / 2);

      const pos = terrainGeom.attributes.position;
      const colors = [];
      baseHeights = new Float32Array(pos.count);
      const exag = CFG.initialExaggeration || 1.5;

      for (let i = 0; i < pos.count; i++) {
        const x = pos.getX(i);
        const z = pos.getZ(i);
        const rawH = sampleRegionalElevationRaw(x, z);
        baseHeights[i] = rawH;
        pos.setY(i, rawH * exag);

        // Geomorphological Multi-Zone Vertex Coloring
        const dRiv = Math.abs(z - getLuniRiverCenterZ(x));
        let r, g, b;

        // Zone 1: Aravalli Rocky Mountain Ridges (high elevation in eastern quadrant)
        if (x > -10 && rawH > 7.5) {
          const rockT = Math.min(1.0, (rawH - 7.5) / 14.0);
          if (rockT > 0.6) { // Quartzite ridge crests
            r = 0.45; g = 0.42; b = 0.40;
          } else { // Weathered metamorphic scree
            r = 0.58; g = 0.38; b = 0.22;
          }
        }
        // Zone 2: Ephemeral Luni River Valley Bed
        else if (dRiv < 4.2 && x < 40) {
          if (dRiv < 2.0) { // Active channel sandbar
            r = 0.88; g = 0.78; b = 0.60;
          } else { // Riparian alluvial silt
            r = 0.62; g = 0.52; b = 0.34;
          }
        }
        // Zone 3: Western Thar Sand Dunes (x < 0)
        else if (x < -8) {
          const duneNorm = (rawH + 1.0) / 7.0;
          if (duneNorm > 0.75) { // Sunlit dune crest
            r = 0.96; g = 0.86; b = 0.54;
          } else if (duneNorm > 0.40) { // Golden Thar sand flank
            r = 0.86; g = 0.54; b = 0.18;
          } else { // Interdunal silt flat
            r = 0.68; g = 0.38; b = 0.14;
          }
        }
        // Zone 4: Central Alluvial Floodplain & Agricultural Cadastral Mosaic
        else {
          // Procedural agricultural field parcel hashing
          const gridX = Math.floor((x + 80) / 4.2);
          const gridZ = Math.floor((z + 80) / 4.2);
          const parcelHash = Math.abs(Math.sin(gridX * 12.9898 + gridZ * 78.233)) * 10000;
          const parcelType = Math.floor(parcelHash) % 5;

          if (parcelType === 0) { // Irrigated green Kharif/Rabi crops (Bajra, Mustard, Wheat)
            r = 0.14; g = 0.50; b = 0.20;
          } else if (parcelType === 1) { // Fresh irrigated green
            r = 0.20; g = 0.60; b = 0.26;
          } else if (parcelType === 2) { // Golden harvest parcel
            r = 0.82; g = 0.64; b = 0.16;
          } else if (parcelType === 3) { // Dark plowed clay loam
            r = 0.42; g = 0.28; b = 0.16;
          } else { // Arid fallow pasture / pediment
            r = 0.70; g = 0.48; b = 0.24;
          }
        }

        colors.push(r, g, b);
      }

      terrainGeom.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
      terrainGeom.computeVertexNormals();

      const terrainMat = new THREE.MeshStandardMaterial({
        vertexColors: true,
        roughness: (CFG.rainfall > 10) ? 0.35 : 0.82,
        metalness: 0.05,
        side: THREE.DoubleSide,
        clippingPlanes: [clipPlaneX],
        clipShadows: true,
      });

      terrainMesh = new THREE.Mesh(terrainGeom, terrainMat);
      terrainMesh.receiveShadow = true;
      terrainMesh.castShadow = true;
      scene.add(terrainMesh);
    }

    // -------------------------------------------------------------
    // 7. SUBSURFACE 3D STRATIGRAPHY (6 Solid Strata Blocks)
    // -------------------------------------------------------------
    function buildSubsurfaceStratigraphy(waterY) {
      // Strata horizontal dimensions match 50 km coverage (150x150 units)
      // 1. Saturated Luni Principal Aquifer Water Table
      const waterGeom = new THREE.PlaneGeometry(148, 148, 48, 48);
      waterGeom.rotateX(-Math.PI / 2);
      const waterMat = new THREE.MeshStandardMaterial({
        color: 0x00b4d8,
        roughness: 0.15,
        metalness: 0.60,
        transparent: true,
        opacity: 0.82,
        side: THREE.DoubleSide,
      });
      waterMesh = new THREE.Mesh(waterGeom, waterMat);
      waterMesh.position.y = waterY;
      scene.add(waterMesh);

      // 2. Vadose Zone Murrum & Kankar Block
      const vadoseGeom = new THREE.BoxGeometry(148, 4.2, 148);
      const vadoseMat = new THREE.MeshStandardMaterial({
        color: 0x854d0e,
        roughness: 0.90,
        side: THREE.DoubleSide,
        clippingPlanes: [clipPlaneX],
      });
      vadoseMesh = new THREE.Mesh(vadoseGeom, vadoseMat);
      vadoseMesh.position.y = waterY - 2.1;
      scene.add(vadoseMesh);

      // 3. Fractured Quartzite & Weathered Sandstone Block
      const fracGeom = new THREE.BoxGeometry(148, 3.8, 148);
      const fracMat = new THREE.MeshStandardMaterial({
        color: 0xb45309,
        roughness: 0.88,
        side: THREE.DoubleSide,
        clippingPlanes: [clipPlaneX],
      });
      fracturedMesh = new THREE.Mesh(fracGeom, fracMat);
      fracturedMesh.position.y = waterY - 6.1;
      scene.add(fracturedMesh);

      // 4. Confining Clayey Aquitard Block
      const aquitardGeom = new THREE.BoxGeometry(148, 2.5, 148);
      const aquitardMat = new THREE.MeshStandardMaterial({
        color: 0x475569,
        roughness: 0.92,
        side: THREE.DoubleSide,
        clippingPlanes: [clipPlaneX],
      });
      aquitardMesh = new THREE.Mesh(aquitardGeom, aquitardMat);
      aquitardMesh.position.y = waterY - 9.25;
      scene.add(aquitardMesh);

      // 5. Deep Pre-Cambrian Malani Granite Basement Block
      const bedrockGeom = new THREE.BoxGeometry(148, 5.0, 148);
      const bedrockMat = new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        roughness: 0.95,
        side: THREE.DoubleSide,
        clippingPlanes: [clipPlaneX],
      });
      bedrockMesh = new THREE.Mesh(bedrockGeom, bedrockMat);
      bedrockMesh.position.y = waterY - 13.0;
      scene.add(bedrockMesh);
    }

    // -------------------------------------------------------------
    // 8. LUNI RIVER NETWORK, TRIBUTARIES & HIGHWAY BRIDGE
    // -------------------------------------------------------------
    function buildLuniRiverNetwork() {
      // Primary Luni river course curving across 50 km from Aravalli hills to SW
      const mainPts = [];
      for (let x = -70; x <= 45; x += 3) {
        const z = getLuniRiverCenterZ(x);
        const y = sampleRegionalElevation(x, z) + 0.12;
        mainPts.push(new THREE.Vector3(x, y, z));
      }
      const curve = new THREE.CatmullRomCurve3(mainPts);
      const riverGeom = new THREE.TubeGeometry(curve, 90, 1.35, 8, false);

      const isMonsoon = (CFG.rainfall >= 25.0);
      const riverMat = new THREE.MeshStandardMaterial({
        color: isMonsoon ? 0x0284c7 : 0x0ea5e9,
        roughness: isMonsoon ? 0.15 : 0.35,
        metalness: isMonsoon ? 0.65 : 0.25,
        transparent: true,
        opacity: isMonsoon ? 0.92 : 0.78,
        clippingPlanes: [clipPlaneX],
      });
      const riverMesh = new THREE.Mesh(riverGeom, riverMat);
      riverGroup.add(riverMesh);
      riverGroup.userData.waterMaterial = riverMat;

      // Tributary Creek (Saraswati nallah from Pushkar valley joining at Govindgarh)
      const tribPts = [];
      for (let t = 0; t <= 1.0; t += 0.05) {
        const tx = 22 * (1 - t) - 4 * t;
        const tz = 28 * (1 - t) + 0 * t;
        const ty = sampleRegionalElevation(tx, tz) + 0.08;
        tribPts.push(new THREE.Vector3(tx, ty, tz));
      }
      const tribCurve = new THREE.CatmullRomCurve3(tribPts);
      const tribGeom = new THREE.TubeGeometry(tribCurve, 30, 0.65, 6, false);
      const tribMesh = new THREE.Mesh(tribGeom, riverMat);
      riverGroup.add(tribMesh);

      // Concrete Girder Highway Bridge crossing the Luni River near Govindgarh
      const bridgeX = -4, bridgeZ = getLuniRiverCenterZ(bridgeX);
      const bridgeY = sampleRegionalElevation(bridgeX, bridgeZ) + 1.6;

      const deckGeom = new THREE.BoxGeometry(3.6, 0.45, 12);
      const concreteMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.85, clippingPlanes: [clipPlaneX] });
      const deck = new THREE.Mesh(deckGeom, concreteMat);
      deck.position.set(bridgeX, bridgeY, bridgeZ);
      deck.castShadow = true;
      riverGroup.add(deck);

      // Bridge Support Piers
      [-3.8, 3.8].forEach(pz => {
        const pierGeom = new THREE.CylinderGeometry(0.5, 0.6, 3.2, 8);
        const pier = new THREE.Mesh(pierGeom, concreteMat);
        pier.position.set(bridgeX, bridgeY - 1.6, bridgeZ + pz);
        pier.castShadow = true;
        riverGroup.add(pier);
      });

      // Bridge Railings
      const railGeom = new THREE.BoxGeometry(0.12, 0.6, 12);
      const railMat = new THREE.MeshStandardMaterial({ color: 0xef4444, metalness: 0.4 });
      const rail1 = new THREE.Mesh(railGeom, railMat);
      rail1.position.set(bridgeX - 1.65, bridgeY + 0.5, bridgeZ);
      const rail2 = new THREE.Mesh(railGeom, railMat);
      rail2.position.set(bridgeX + 1.65, bridgeY + 0.5, bridgeZ);
      riverGroup.add(rail1);
      riverGroup.add(rail2);
    }

    // -------------------------------------------------------------
    // 9. SETTLEMENTS, RAJASTHANI ARCHITECTURE & ROAD NETWORK
    // -------------------------------------------------------------
    function buildSettlementsAndRoads() {
      // 5 Named Regional Villages/Tehsils in the Upper Luni Basin:
      const settlements = [
        { name: "Govindgarh", x: -8, z: -2, count: 24 },    // Confluence hub
        { name: "Pushkar Rural", x: 24, z: 28, count: 20 }, // Aravalli sacred valley
        { name: "Pisangan", x: -36, z: -18, count: 22 },    // Agricultural plain hub
        { name: "Srinagar", x: 38, z: -6, count: 18 },      // Eastern pediment township
        { name: "Saradhna", x: 6, z: -28, count: 18 },      // Southern transport corridor
      ];

      settlements.forEach(s => {
        const villageGroup = new THREE.Group();
        villageGroup.userData = { name: s.name, x: s.x, z: s.z };

        // Village Buildings
        for (let b = 0; b < s.count; b++) {
          const ox = s.x + (Math.random() - 0.5) * 11;
          const oz = s.z + (Math.random() - 0.5) * 11;
          const oy = sampleRegionalElevation(ox, oz);

          const w = 1.4 + Math.random() * 1.2;
          const h = 1.2 + Math.random() * 1.0;
          const d = 1.4 + Math.random() * 1.2;

          // Sandstone / Whitewashed House
          const houseGeom = new THREE.BoxGeometry(w, h, d);
          const isWhite = Math.random() > 0.45;
          const houseMat = new THREE.MeshStandardMaterial({
            color: isWhite ? 0xf1f5f9 : 0xd4a373,
            roughness: 0.88,
            clippingPlanes: [clipPlaneX],
          });
          const house = new THREE.Mesh(houseGeom, houseMat);
          house.position.set(ox, oy + h / 2, oz);
          house.castShadow = true;
          house.receiveShadow = true;
          villageGroup.add(house);

          // Rooftop Sintex / Concrete Water Storage Tank
          if (Math.random() > 0.35) {
            const tankGeom = new THREE.CylinderGeometry(0.22, 0.22, 0.45, 8);
            const isBlue = Math.random() > 0.4;
            const tankMat = new THREE.MeshStandardMaterial({ color: isBlue ? 0x0284c7 : 0xffffff, roughness: 0.4 });
            const tank = new THREE.Mesh(tankGeom, tankMat);
            tank.position.set(ox + 0.3, oy + h + 0.22, oz + 0.3);
            villageGroup.add(tank);
          }
        }

        // Traditional Village Stepwell (Baori)
        const baoriY = sampleRegionalElevation(s.x + 3.5, s.z + 3.5);
        const baoriGeom = new THREE.CylinderGeometry(1.8, 1.4, 1.5, 8);
        const baoriMat = new THREE.MeshStandardMaterial({ color: 0x78716c, roughness: 0.95, clippingPlanes: [clipPlaneX] });
        const baori = new THREE.Mesh(baoriGeom, baoriMat);
        baori.position.set(s.x + 3.5, baoriY + 0.3, s.z + 3.5);
        baori.castShadow = true;
        villageGroup.add(baori);

        // Traditional Domed Pavilion (Chhatri) on high ground
        const chhatriY = sampleRegionalElevation(s.x - 3.8, s.z - 3.8);
        const chhatriDomeGeom = new THREE.SphereGeometry(0.9, 12, 12, 0, Math.PI * 2, 0, Math.PI / 2);
        const chhatriMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.75, clippingPlanes: [clipPlaneX] });
        const dome = new THREE.Mesh(chhatriDomeGeom, chhatriMat);
        dome.position.set(s.x - 3.8, chhatriY + 2.4, s.z - 3.8);
        villageGroup.add(dome);

        // 4 Chhatri Pillars
        [[-0.6, -0.6], [-0.6, 0.6], [0.6, -0.6], [0.6, 0.6]].forEach(pil => {
          const pilGeom = new THREE.CylinderGeometry(0.08, 0.08, 2.2, 6);
          const pillar = new THREE.Mesh(pilGeom, chhatriMat);
          pillar.position.set(s.x - 3.8 + pil[0], chhatriY + 1.1, s.z - 3.8 + pil[1]);
          villageGroup.add(pillar);
        });

        // Traditional Rainwater Harvesting Kund / Tanka
        const tankaY = sampleRegionalElevation(s.x - 4.5, s.z + 4.5);
        const tankaApronGeom = new THREE.CylinderGeometry(2.4, 2.8, 0.15, 12);
        const tankaMat = new THREE.MeshStandardMaterial({ color: 0xa8a29e, roughness: 0.9, clippingPlanes: [clipPlaneX] });
        const tankaApron = new THREE.Mesh(tankaApronGeom, tankaMat);
        tankaApron.position.set(s.x - 4.5, tankaY + 0.08, s.z + 4.5);
        villageGroup.add(tankaApron);

        const tankaDomeGeom = new THREE.SphereGeometry(0.75, 10, 10, 0, Math.PI * 2, 0, Math.PI / 2);
        const tankaDome = new THREE.Mesh(tankaDomeGeom, tankaMat);
        tankaDome.position.set(s.x - 4.5, tankaY + 0.15, s.z + 4.5);
        villageGroup.add(tankaDome);

        settlementGroup.add(villageGroup);
      });

      // Paved 2-Lane State Highway connecting settlements across 50 km extent
      const roadPts = [
        new THREE.Vector3(55, 0, 40),
        new THREE.Vector3(38, 0, 24),
        new THREE.Vector3(20, 0, 12),
        new THREE.Vector3(4, 0, 2),
        new THREE.Vector3(-4, 0, -2),   // Over bridge
        new THREE.Vector3(-18, 0, -10),
        new THREE.Vector3(-36, 0, -18),  // Through Pisangan
        new THREE.Vector3(-58, 0, -32),
      ];
      roadPts.forEach(pt => {
        pt.y = sampleRegionalElevation(pt.x, pt.z) + 0.16;
      });
      const roadCurve = new THREE.CatmullRomCurve3(roadPts);
      const roadGeom = new THREE.TubeGeometry(roadCurve, 64, 0.75, 4, false);
      const roadMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.92, clippingPlanes: [clipPlaneX] });
      const roadMesh = new THREE.Mesh(roadGeom, roadMat);
      roadGroup.add(roadMesh);

      // High-Voltage Electrical Transmission Pylons across the basin
      const pylonCoords = [[-42, 28], [-24, 20], [-6, 14], [12, 6], [30, -2], [48, -10]];
      pylonCoords.forEach(c => {
        const py = sampleRegionalElevation(c[0], c[1]);
        const pylonGroup = new THREE.Group();
        const bodyGeom = new THREE.CylinderGeometry(0.3, 0.8, 6.5, 4);
        const pylonMat = new THREE.MeshStandardMaterial({ color: 0x64748b, wireframe: true, clippingPlanes: [clipPlaneX] });
        const pylon = new THREE.Mesh(bodyGeom, pylonMat);
        pylon.position.y = py + 3.25;
        pylonGroup.add(pylon);

        const armGeom = new THREE.BoxGeometry(3.2, 0.12, 0.12);
        const arm = new THREE.Mesh(armGeom, pylonMat);
        arm.position.y = py + 5.5;
        pylonGroup.add(arm);

        pylonGroup.position.set(c[0], 0, c[1]);
        roadGroup.add(pylonGroup);
      });
    }

    // -------------------------------------------------------------
    // 10. FARMS, TUBE-WELL PUMP HOUSES & SOLAR IRRIGATION PUMPS
    // -------------------------------------------------------------
    function buildFarmsAndSolarPumps() {
      // Tube-well pump houses & solar panels scattered in the agricultural plains
      const pumpLocs = [
        [-16, 8], [-22, -6], [-12, -18], [-28, 14], [12, -14],
        [18, 10], [-4, 22], [-32, -8], [2, -18], [28, -14]
      ];

      pumpLocs.forEach(loc => {
        const py = sampleRegionalElevation(loc[0], loc[1]);
        const group = new THREE.Group();

        // Masonry Pump Shed (Kuan Kothi)
        const shedGeom = new THREE.BoxGeometry(1.6, 1.3, 1.6);
        const shedMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.9, clippingPlanes: [clipPlaneX] });
        const shed = new THREE.Mesh(shedGeom, shedMat);
        shed.position.set(0, 0.65, 0);
        shed.castShadow = true;
        group.add(shed);

        // Blue Electric Pump Motor & Discharge Pipe
        const pipeGeom = new THREE.CylinderGeometry(0.1, 0.1, 1.2, 8);
        const pipeMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.7 });
        const pipe = new THREE.Mesh(pipeGeom, pipeMat);
        pipe.rotation.z = Math.PI / 2;
        pipe.position.set(1.1, 0.4, 0);
        group.add(pipe);

        // Solar Photovoltaic Pumping Array (4-panel array tilted 26 deg South)
        const solarGeom = new THREE.BoxGeometry(1.8, 0.04, 1.2);
        const solarMat = new THREE.MeshStandardMaterial({ color: 0x1e3a8a, metalness: 0.75, roughness: 0.25 });
        const solar = new THREE.Mesh(solarGeom, solarMat);
        solar.position.set(-1.4, 1.1, 0);
        solar.rotation.x = 0.45; // South-facing tilt
        solar.castShadow = true;
        group.add(solar);

        const poleGeom = new THREE.CylinderGeometry(0.06, 0.06, 1.0, 6);
        const poleMat = new THREE.MeshStandardMaterial({ color: 0x475569 });
        const pole = new THREE.Mesh(poleGeom, poleMat);
        pole.position.set(-1.4, 0.5, 0);
        group.add(pole);

        group.position.set(loc[0], py, loc[1]);
        farmGroup.add(group);
      });
    }

    // -------------------------------------------------------------
    // 11. MONITORING WELLS (WGS84 Geodesic Placement)
    // -------------------------------------------------------------
    function instantiateMonitoringWells(waterY) {
      const wells = CFG.wells || [];
      if (wells.length === 0) return;

      let minLat = 90, maxLat = -90, minLon = 180, maxLon = -180;
      wells.forEach(w => {
        if (w.lat < minLat) minLat = w.lat;
        if (w.lat > maxLat) maxLat = w.lat;
        if (w.lon < minLon) minLon = w.lon;
        if (w.lon > maxLon) maxLon = w.lon;
      });
      const spanLat = Math.max(maxLat - minLat, 0.01);
      const spanLon = Math.max(maxLon - minLon, 0.01);
      const midLat = (minLat + maxLat) / 2;
      const midLon = (minLon + maxLon) / 2;

      wells.forEach(w => {
        // Map to 50 km coordinate frame (span 110 units across)
        const relX = ((w.lon - midLon) / spanLon) * 110;
        const relZ = -((w.lat - midLat) / spanLat) * 110;
        const groundY = sampleRegionalElevation(relX, relZ);

        const group = new THREE.Group();
        group.userData = w;

        // Borehole Tube extending down into the aquifer
        const tubeH = Math.max(2.0, groundY - waterY + 2.0);
        const tubeGeom = new THREE.CylinderGeometry(0.2, 0.2, tubeH, 8);
        const tubeMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.85, roughness: 0.2 });
        const tube = new THREE.Mesh(tubeGeom, tubeMat);
        tube.position.y = groundY - tubeH / 2;
        tube.castShadow = true;
        group.add(tube);

        // Concrete Apron
        const apronGeom = new THREE.CylinderGeometry(1.2, 1.4, 0.35, 8);
        const apronMat = new THREE.MeshStandardMaterial({ color: 0x64748b, roughness: 0.9 });
        const apron = new THREE.Mesh(apronGeom, apronMat);
        apron.position.y = groundY + 0.17;
        group.add(apron);

        // Telemetry Datalogger Mast
        const mastGeom = new THREE.CylinderGeometry(0.08, 0.08, 2.5, 6);
        const mastMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.9 });
        const mast = new THREE.Mesh(mastGeom, mastMat);
        mast.position.y = groundY + 1.5;
        group.add(mast);

        // Status-Coded LED Beacon Sphere with Halo
        const ledGeom = new THREE.SphereGeometry(0.35, 12, 12);
        const ledMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(w.color) });
        const led = new THREE.Mesh(ledGeom, ledMat);
        led.position.set(0, groundY + 2.8, 0);
        group.add(led);

        // South-Facing Solar PV Panel
        const panelGeom = new THREE.BoxGeometry(1.3, 0.05, 0.9);
        const panelMat = new THREE.MeshStandardMaterial({ color: 0x1e3a8a, metalness: 0.6 });
        const panel = new THREE.Mesh(panelGeom, panelMat);
        panel.position.set(0, groundY + 2.3, 0);
        panel.rotation.x = 0.45;
        group.add(panel);

        // Invisible Raycasting Hit Proxy
        const hitGeom = new THREE.CylinderGeometry(1.6, 1.6, 4.0, 8);
        const hitMat = new THREE.MeshBasicMaterial({ visible: false });
        const hit = new THREE.Mesh(hitGeom, hitMat);
        hit.position.y = groundY + 2.0;
        hit.userData = w;
        group.add(hit);

        group.position.set(relX, 0, relZ);
        wellGroup.add(group);

        if (w.village === activeSelectedWell || w.isSelected) {
          selectedWellCoords = { x: relX, y: groundY, z: relZ };
          updateInspectorPanel(w);
        }
      });
    }

    // -------------------------------------------------------------
    // 12. THAR DESERT FLORA (Khejri, Rohida, Sewan Grass)
    // -------------------------------------------------------------
    function buildTharFlora() {
      // 1. Instanced Khejri Trees (Prosopis cineraria) - State Tree of Rajasthan
      const khejriCount = 140;
      const trunkGeom = new THREE.CylinderGeometry(0.18, 0.32, 2.2, 6);
      const trunkMat = new THREE.MeshStandardMaterial({ color: 0x5c2c0e, roughness: 0.92, clippingPlanes: [clipPlaneX] });
      const canopyGeom = new THREE.CylinderGeometry(2.0, 0.6, 0.8, 8);
      const canopyMat = new THREE.MeshStandardMaterial({ color: 0x3f6212, roughness: 0.82, clippingPlanes: [clipPlaneX] });

      const trunkInst = new THREE.InstancedMesh(trunkGeom, trunkMat, khejriCount);
      const canopyInst = new THREE.InstancedMesh(canopyGeom, canopyMat, khejriCount);
      const mat4 = new THREE.Matrix4();
      const posV = new THREE.Vector3();
      const quat = new THREE.Quaternion();
      const scaleV = new THREE.Vector3(1, 1, 1);

      let placed = 0;
      for (let i = 0; i < khejriCount; i++) {
        const tx = (Math.random() - 0.5) * 130;
        const tz = (Math.random() - 0.5) * 130;
        const ty = sampleRegionalElevation(tx, tz);

        // Place mainly on plains, dunes and field edges (not steep mountains)
        if (ty < 12.0) {
          posV.set(tx, ty + 1.1, tz);
          mat4.compose(posV, quat, scaleV);
          trunkInst.setMatrixAt(placed, mat4);

          posV.set(tx, ty + 2.4, tz);
          mat4.compose(posV, quat, scaleV);
          canopyInst.setMatrixAt(placed, mat4);
          placed++;
        }
      }
      trunkInst.count = placed;
      canopyInst.count = placed;
      trunkInst.castShadow = true;
      canopyInst.castShadow = true;
      floraGroup.add(trunkInst);
      floraGroup.add(canopyInst);

      // 2. Instanced Rohida Trees (Tecomella undulata - Desert Teak with Flame Flowers)
      const rohidaCount = 60;
      const rCanopyGeom = new THREE.SphereGeometry(1.2, 8, 8);
      const rCanopyMat = new THREE.MeshStandardMaterial({ color: 0xd97706, roughness: 0.85, clippingPlanes: [clipPlaneX] });
      const rohidaInst = new THREE.InstancedMesh(rCanopyGeom, rCanopyMat, rohidaCount);
      for (let j = 0; j < rohidaCount; j++) {
        const rx = (Math.random() - 0.5) * 120;
        const rz = (Math.random() - 0.5) * 120;
        const ry = sampleRegionalElevation(rx, rz);
        posV.set(rx, ry + 1.4, rz);
        mat4.compose(posV, quat, scaleV);
        rohidaInst.setMatrixAt(j, mat4);
      }
      floraGroup.add(rohidaInst);

      // 3. Sewan Grass Clumps (Lasiurus scindicus)
      const grassCount = 180;
      const grassGeom = new THREE.ConeGeometry(0.65, 0.8, 5);
      const grassMat = new THREE.MeshStandardMaterial({ color: 0x84cc16, roughness: 0.9, clippingPlanes: [clipPlaneX] });
      const grassInst = new THREE.InstancedMesh(grassGeom, grassMat, grassCount);
      for (let g = 0; g < grassCount; g++) {
        const gx = (Math.random() - 0.5) * 135;
        const gz = (Math.random() - 0.5) * 135;
        const gy = sampleRegionalElevation(gx, gz);
        posV.set(gx, gy + 0.4, gz);
        mat4.compose(posV, quat, scaleV);
        grassInst.setMatrixAt(g, mat4);
      }
      floraGroup.add(grassInst);
    }

    // -------------------------------------------------------------
    // 13. CLOUDS, WILDLIFE & DYNAMIC PARTICLES
    // -------------------------------------------------------------
    function buildCloudsAndAtmosphere() {
      // 14 Volumetric-style Billowy Cloud Puffs drifting over the 50 km sky
      const cloudGeom = new THREE.DodecahedronGeometry(6.5, 1);
      const cloudMat = new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.95,
        transparent: true,
        opacity: (CFG.rainfall > 20) ? 0.85 : 0.65,
      });

      for (let c = 0; c < 14; c++) {
        const puff = new THREE.Mesh(cloudGeom, cloudMat);
        puff.position.set(
          (Math.random() - 0.5) * 150,
          42 + Math.random() * 12,
          (Math.random() - 0.5) * 150
        );
        puff.scale.set(1.8 + Math.random() * 1.5, 0.6 + Math.random() * 0.4, 1.2 + Math.random() * 1.0);
        cloudGroup.add(puff);
      }
    }

    function buildWildlife() {
      // 3 Desert Eagles soaring high over the Aravalli peaks
      const eagleGeom = new THREE.ConeGeometry(0.3, 1.6, 3);
      eagleGeom.rotateX(Math.PI / 2);
      const eagleMat = new THREE.MeshBasicMaterial({ color: 0x1e293b });
      for (let e = 0; e < 3; e++) {
        const eagle = new THREE.Mesh(eagleGeom, eagleMat);
        wildlifeGroup.add(eagle);
      }
    }

    function createFlowParticles(waterY) {
      const count = 400;
      const pGeom = new THREE.BufferGeometry();
      const pPos = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        pPos[i * 3 + 0] = (Math.random() - 0.5) * 140;
        pPos[i * 3 + 1] = waterY + 0.05;
        pPos[i * 3 + 2] = (Math.random() - 0.5) * 140;
      }
      pGeom.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
      const pMat = new THREE.PointsMaterial({
        color: 0x00f5ff,
        size: 0.42,
        transparent: true,
        opacity: 0.85,
      });
      flowParticles = new THREE.Points(pGeom, pMat);
      scene.add(flowParticles);
    }

    function createDustParticles() {
      const count = 450;
      const pGeom = new THREE.BufferGeometry();
      const pPos = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        pPos[i * 3 + 0] = (Math.random() - 0.5) * 150;
        pPos[i * 3 + 1] = Math.random() * 15 + 0.5;
        pPos[i * 3 + 2] = (Math.random() - 0.5) * 150;
      }
      pGeom.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
      const pMat = new THREE.PointsMaterial({
        color: 0xfde047,
        size: 0.35,
        transparent: true,
        opacity: 0.65,
      });
      dustParticles = new THREE.Points(pGeom, pMat);
      scene.add(dustParticles);
    }

    function createRainParticles() {
      const count = 500;
      const pGeom = new THREE.BufferGeometry();
      const pPos = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        pPos[i * 3 + 0] = (Math.random() - 0.5) * 150;
        pPos[i * 3 + 1] = Math.random() * 60;
        pPos[i * 3 + 2] = (Math.random() - 0.5) * 150;
      }
      pGeom.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
      const pMat = new THREE.PointsMaterial({
        color: 0x38bdf8,
        size: 0.38,
        transparent: true,
        opacity: 0.75,
      });
      rainParticles = new THREE.Points(pGeom, pMat);
      rainParticles.visible = (CFG.rainfall > 0);
      scene.add(rainParticles);
    }

    // -------------------------------------------------------------
    // 14. 10 CAMERA PRESETS (Smooth Tweened Transitions)
    // -------------------------------------------------------------
    function applyCameraPreset(preset) {
      document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
      const btn = document.getElementById('btn-' + preset);
      if (btn) btn.classList.add('active');

      let targetPos = new THREE.Vector3();
      let targetLook = new THREE.Vector3(0, 0, 0);

      if (preset === 'iso') { // Elevated Isometric View (Default, 35 deg pitch downward, 45 deg azimuth)
        targetPos.set(68, 52, 68);
        targetLook.set(0, 0, 0);
      } else if (preset === 'basin') { // 50 km Basin Regional Overview
        targetPos.set(0, 115, 110);
        targetLook.set(0, 0, 0);
      } else if (preset === 'top') { // Top-Down Satellite GIS View
        targetPos.set(0, 135, 0.001);
        targetLook.set(0, 0, 0);
      } else if (preset === 'oblique') { // Low Oblique Landscape Flyover
        targetPos.set(75, 16, 75);
        targetLook.set(0, 3, 0);
      } else if (preset === 'cutaway') { // Subsurface Cutaway View
        targetPos.set(58, 28, -52);
        targetLook.set(0, -4, 0);
        applyCutawayMode('partial');
      } else if (preset === 'section') { // Vertical Geological Cross-Section
        targetPos.set(0, -2, 95);
        targetLook.set(0, -3, 0);
        applyCutawayMode('cross');
      } else if (preset === 'well') { // Selected Well Focus
        focusSelectedWell();
        return;
      } else if (preset === 'village') { // Govindgarh Confluence Settlement Focus
        targetPos.set(-8 + 14, 10, -2 + 14);
        targetLook.set(-8, 2.5, -2);
      } else if (preset === 'river') { // Luni River Corridor Flyover
        targetPos.set(12, 18, 16);
        targetLook.set(-18, 2, -6);
      } else if (preset === 'fit') { // Fit 50 km Extent
        targetPos.set(60, 48, 60);
        targetLook.set(0, 0, 0);
      }
      animateCameraTo(targetPos, targetLook);
    }

    function animateCameraTo(endPos, endTarget, durationMs = 1200) {
      camStartPos.copy(camera.position);
      camEndPos.copy(endPos);
      camStartTarget.copy(controls.target);
      camEndTarget.copy(endTarget);
      animStartTime = performance.now();
      animDuration = durationMs;
      isAnimatingCamera = true;
    }

    function focusSelectedWell() {
      const endPos = new THREE.Vector3(selectedWellCoords.x + 9, selectedWellCoords.y + 6, selectedWellCoords.z + 9);
      const endTarget = new THREE.Vector3(selectedWellCoords.x, selectedWellCoords.y, selectedWellCoords.z);
      animateCameraTo(endPos, endTarget);
    }

    // -------------------------------------------------------------
    // 15. GEOLOGICAL CUTAWAY & SLICER CONTROLS
    // -------------------------------------------------------------
    function applyCutawayMode(mode) {
      document.getElementById('cutaway-select').value = mode;
      const sliceSlider = document.getElementById('slice-slider');
      const sliceVal = document.getElementById('slice-val');

      if (mode === 'complete') {
        clipPlaneX.constant = 95.0;
        sliceSlider.value = 0;
        sliceVal.innerText = '0%';
        terrainMesh.visible = true;
        terrainMesh.material.transparent = false;
      } else if (mode === 'partial') {
        clipPlaneX.constant = 25.0;
        sliceSlider.value = 35;
        sliceVal.innerText = '35%';
        terrainMesh.visible = true;
        terrainMesh.material.transparent = false;
      } else if (mode === 'full') {
        clipPlaneX.constant = 0.0;
        sliceSlider.value = 50;
        sliceVal.innerText = '50%';
        terrainMesh.visible = true;
        terrainMesh.material.transparent = false;
      } else if (mode === 'cross') {
        clipPlaneX.constant = -6.0;
        sliceSlider.value = 55;
        sliceVal.innerText = '55%';
        terrainMesh.visible = true;
        terrainMesh.material.transparent = false;
      } else if (mode === 'groundwater') {
        terrainMesh.visible = false;
      } else if (mode === 'combined') {
        clipPlaneX.constant = 95.0;
        terrainMesh.visible = true;
        terrainMesh.material.transparent = true;
        terrainMesh.material.opacity = 0.45;
      }
    }

    function onSliceInput(val) {
      const pct = parseFloat(val);
      document.getElementById('slice-val').innerText = pct + '%';
      clipPlaneX.constant = 90.0 - (pct / 100.0) * 170.0;
      if (pct > 0 && terrainMesh.visible && !terrainMesh.material.transparent) {
        document.getElementById('cutaway-select').value = 'partial';
      }
    }

    function onExaggerationInput(val) {
      const factor = parseFloat(val);
      document.getElementById('exaggeration-val').innerText = factor.toFixed(2) + 'x';
      if (!terrainGeom) return;
      const pos = terrainGeom.attributes.position;
      for (let i = 0; i < pos.count; i++) {
        pos.setY(i, baseHeights[i] * factor);
      }
      pos.needsUpdate = true;
      terrainGeom.computeVertexNormals();
    }

    // -------------------------------------------------------------
    // 16. LAYER VISIBILITY DRAWER
    // -------------------------------------------------------------
    function updateLayers() {
      if (terrainMesh) terrainMesh.visible = document.getElementById('chk-terrain').checked;
      const showStrata = document.getElementById('chk-strata').checked;
      if (vadoseMesh) vadoseMesh.visible = showStrata;
      if (fracturedMesh) fracturedMesh.visible = showStrata;
      if (aquitardMesh) aquitardMesh.visible = showStrata;
      if (bedrockMesh) bedrockMesh.visible = showStrata;
      if (waterMesh) waterMesh.visible = document.getElementById('chk-water').checked;
      if (flowParticles) flowParticles.visible = document.getElementById('chk-flow').checked;
      if (riverGroup) riverGroup.visible = document.getElementById('chk-river').checked;
      if (wellGroup) wellGroup.visible = document.getElementById('chk-wells').checked;
      const showSettlements = document.getElementById('chk-settlements').checked;
      if (settlementGroup) settlementGroup.visible = showSettlements;
      if (roadGroup) roadGroup.visible = showSettlements;
      if (farmGroup) farmGroup.visible = document.getElementById('chk-farms').checked;
      if (floraGroup) floraGroup.visible = document.getElementById('chk-flora').checked;
      const showWeather = document.getElementById('chk-weather').checked;
      if (cloudGroup) cloudGroup.visible = showWeather;
      if (wildlifeGroup) wildlifeGroup.visible = showWeather;
      if (rainParticles) rainParticles.visible = showWeather && (CFG.rainfall > 0);
      if (dustParticles) dustParticles.visible = showWeather;
    }

    function toggleLayerDrawer() {
      const p = document.getElementById('layer-panel');
      p.classList.toggle('open');
    }

    // -------------------------------------------------------------
    // 17. ATMOSPHERIC AMBIANCE & LIGHTING MODES
    // -------------------------------------------------------------
    function setAmbiance(mode) {
      currentAmbiance = mode;
      document.querySelectorAll('.action-btn').forEach(b => {
        if (b.id && b.id.startsWith('amb-')) b.classList.remove('active');
      });
      const btn = document.getElementById('amb-' + mode);
      if (btn) btn.classList.add('active');

      if (mode === 'day') {
        scene.background.set(0xfef3c7);
        scene.fog.color.set(0xfef3c7);
        scene.fog.density = 0.0055;
        hemiLight.color.set(0xffedd5);
        hemiLight.intensity = 0.70;
        dirLight.color.set(0xfffbeb);
        dirLight.intensity = 1.45;
        dirLight.position.set(70, 95, 55);
        if (sunSphere) { sunSphere.material.color.set(0xfffbeb); sunSphere.visible = true; }
      } else if (mode === 'sunset') {
        scene.background.set(0xf97316);
        scene.fog.color.set(0xea580c);
        scene.fog.density = 0.007;
        hemiLight.color.set(0xfde047);
        hemiLight.intensity = 0.55;
        dirLight.color.set(0xfb923c);
        dirLight.intensity = 1.25;
        dirLight.position.set(85, 25, 45);
        if (sunSphere) { sunSphere.material.color.set(0xfb923c); sunSphere.visible = true; }
      } else if (mode === 'night') {
        scene.background.set(0x070b14);
        scene.fog.color.set(0x070b14);
        scene.fog.density = 0.006;
        hemiLight.color.set(0x1e293b);
        hemiLight.intensity = 0.35;
        dirLight.color.set(0x38bdf8);
        dirLight.intensity = 0.40;
        dirLight.position.set(-50, 75, -50);
        if (sunSphere) sunSphere.visible = false;
      } else if (mode === 'storm') {
        scene.background.set(0x334155);
        scene.fog.color.set(0x475569);
        scene.fog.density = 0.012;
        hemiLight.color.set(0x64748b);
        hemiLight.intensity = 0.45;
        dirLight.color.set(0x94a3b8);
        dirLight.intensity = 0.85;
        if (rainParticles) rainParticles.visible = true;
        if (sunSphere) sunSphere.visible = false;
      }
    }

    function applyAmbiance(str) {
      if (str.includes('Sunset') || str.includes('Golden')) setAmbiance('sunset');
      else if (str.includes('Night')) setAmbiance('night');
      else if (str.includes('Monsoon') || str.includes('Storm')) setAmbiance('storm');
      else setAmbiance('day');
    }

    function toggleFullscreen() {
      if (!document.fullscreenElement) {
        wrap.requestFullscreen().catch(err => {});
      } else {
        document.exitFullscreen();
      }
    }

    // -------------------------------------------------------------
    // 18. RAYCASTING & CLICK-TO-INSPECT WELLHEADS
    // -------------------------------------------------------------
    function onMouseMove(event) {
      const rect = wrap.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);

      // Check well intersection for hover tooltip
      if (wellGroup && wellGroup.visible) {
        const intersects = raycaster.intersectObjects(wellGroup.children, true);
        if (intersects.length > 0) {
          let obj = intersects[0].object;
          while (obj && !obj.userData.village && obj.parent) obj = obj.parent;
          if (obj && obj.userData.village) {
            tooltip.style.display = 'block';
            tooltip.style.left = (event.clientX - rect.left + 12) + 'px';
            tooltip.style.top = (event.clientY - rect.top - 10) + 'px';
            tooltip.innerHTML = `<b>${obj.userData.village}</b><br>DTWL: ${obj.userData.dtwl.toFixed(2)} mbgl (${obj.userData.stress})`;
            wrap.style.cursor = 'pointer';
            return;
          }
        }
      }
      tooltip.style.display = 'none';
      wrap.style.cursor = 'default';

      // Sample ground GPS coordinates for live HUD
      if (terrainMesh) {
        const hits = raycaster.intersectObject(terrainMesh);
        if (hits.length > 0) {
          const p = hits[0].point;
          const approxLat = CFG.lat - (p.z / 55.0) * 0.45;
          const approxLon = CFG.lon + (p.x / 55.0) * 0.50;
          const approxElev = CFG.elev + p.y * 14.0;
          document.getElementById('mouse-coords').innerText = `📍 ${approxLat.toFixed(4)}°N, ${approxLon.toFixed(4)}°E | Elev: ${approxElev.toFixed(0)}m`;
        }
      }
    }

    function onCanvasClick(event) {
      const rect = wrap.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      if (wellGroup && wellGroup.visible) {
        const intersects = raycaster.intersectObjects(wellGroup.children, true);
        if (intersects.length > 0) {
          let obj = intersects[0].object;
          while (obj && !obj.userData.village && obj.parent) obj = obj.parent;
          if (obj && obj.userData.village) {
            activeSelectedWell = obj.userData.village;
            selectedWellCoords = {
              x: obj.position.x,
              y: sampleRegionalElevation(obj.position.x, obj.position.z),
              z: obj.position.z
            };
            updateInspectorPanel(obj.userData);
          }
        }
      }
    }

    function updateInspectorPanel(data) {
      document.getElementById('ins-village').innerText = data.village;
      document.getElementById('ins-geo').innerText = `${data.district || CFG.district} (${data.block || CFG.block})`;
      document.getElementById('ins-coords').innerText = `${data.lat.toFixed(4)}°N, ${data.lon.toFixed(4)}°E`;
      document.getElementById('ins-elev').innerText = `${data.elev.toFixed(1)} m ASL`;
      document.getElementById('ins-dtwl').innerText = `${data.dtwl.toFixed(2)} mbgl`;
      const wtElev = (data.elev - data.dtwl).toFixed(1);
      document.getElementById('ins-wtelev').innerText = `${wtElev} m ASL`;
      document.getElementById('ins-trend').innerText = `${data.trend >= 0 ? '+' : ''}${data.trend.toFixed(3)} mbgl/yr`;
      const badge = document.getElementById('ins-badge');
      badge.innerText = data.stress || 'Safe';
      badge.style.background = data.color || '#10b981';
    }

    function onWindowResize() {
      const w = wrap.clientWidth;
      const h = wrap.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    }
  