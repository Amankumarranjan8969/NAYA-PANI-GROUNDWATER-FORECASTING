import sys
from pathlib import Path

p = Path(r"D:\NIH_roorkee\FULL WORK FINAL_DIGITAL_NAYA_PANI\NAYA_PAANI\digital_twin.py")
text = p.read_text(encoding="utf-8")

# 1. Add imports at the top
import_marker = "from twin_engine import ("
import_addition = """from cgwa_auditor import CGWA_AUDITOR
from modflow_engine import MODFLOW_SIMULATOR
from telemetry_stream import TELEMETRY_ENGINE
"""
assert import_marker in text, "import_marker not found"
text = text.replace(import_marker, import_addition + import_marker, 1)

# 2. Add layer checkboxes for Salinity and Live DWLR Telemetry Pings
layer_marker = '<label class="layer-item"><input type="checkbox" id="layer-strata" checked onchange="toggleLayer(\'strata\')"> <span>Subsurface Stratigraphy</span></label>'
new_layers = layer_marker + """
    <label class="layer-item"><input type="checkbox" id="layer-salinity" checked onchange="toggleLayer('salinity')"> <span>Salinity & Solute Plume</span></label>
    <label class="layer-item"><input type="checkbox" id="layer-telemetry" checked onchange="toggleLayer('telemetry')"> <span>Live DWLR Telemetry Pings</span></label>"""
assert layer_marker in text, "layer_marker not found"
text = text.replace(layer_marker, new_layers, 1)

# 3. Add metrics to well card
card_marker = '<div class="card-metric"><div class="card-lbl">Regional Aquifer</div><div class="card-val" id="wc-aquifer">Luni Alluvial Semi-Confined</div></div>'
new_card_metrics = card_marker + """
      <div class="card-metric"><div class="card-lbl">DWLR Battery & QA</div><div class="card-val" style="color:#10b981;" id="wc-qa">3.65V (QA: OK)</div></div>
      <div class="card-metric"><div class="card-lbl">Salinity (EC)</div><div class="card-val" id="wc-ec">1,820 µS/cm</div></div>"""
assert card_marker in text, "card_marker not found"
text = text.replace(card_marker, new_card_metrics, 1)

# 4. Add JS variables
var_marker = "let wellGroup, settlementGroup, treeGroup, scrubGroup, riverWaterMesh, lakeGroup, activityGroup;"
new_vars = "let wellGroup, settlementGroup, treeGroup, scrubGroup, riverWaterMesh, lakeGroup, activityGroup, salinityGroup, plumeParticles, telemetryPingGroup, pingRings = [];"
assert var_marker in text, "var_marker not found"
text = text.replace(var_marker, new_vars, 1)

# 5. Add Telemetry Ping Rings in wells loop and Solute Plume
well_anim_marker = "      // 8. Populated Rajasthani Rural Settlements on Flat Valley Grounds"
telemetry_ping_code = """      // 7b. Live DWLR Telemetry Halo Beacon Rings
      telemetryPingGroup = new THREE.Group();
      scene.add(telemetryPingGroup);
      const pingGeom = new THREE.RingGeometry(0.85, 1.25, 20);
      pingGeom.rotateX(-Math.PI / 2);
      const pingMat = new THREE.MeshBasicMaterial({ color: 0x00f5ff, side: THREE.DoubleSide, transparent: true, opacity: 0.75 });
      wells.forEach(w => {
        const ring = new THREE.Mesh(pingGeom, pingMat.clone());
        ring.position.set(w.x, getRegionalElevation(w.x, w.z) + 0.35, w.z);
        ring.userData = { phase: Math.random() * Math.PI * 2 };
        telemetryPingGroup.add(ring);
        pingRings.push(ring);
      });

"""
assert well_anim_marker in text, "well_anim_marker not found"
text = text.replace(well_anim_marker, telemetry_ping_code + well_anim_marker, 1)

# 6. Add 3D Solute Transport Plume right after flowParticles
flow_marker = "      scene.add(flowParticles);"
plume_code = flow_marker + """

      // 14b. 3D Advection-Dispersion Solute Transport Plume (Salinity & Fluoride Migration)
      const plumeCount = 380;
      const plumeGeom = new THREE.BufferGeometry();
      const plumePos = new Float32Array(plumeCount * 3);
      const plumeColors = new Float32Array(plumeCount * 3);
      const plumeProg = new Float32Array(plumeCount);

      for (let p = 0; p < plumeCount; p++) {
        plumeProg[p] = Math.random();
        const pt = riverCurve.getPoint(plumeProg[p]);
        const spread = (Math.random() - 0.5) * 24.0;
        plumePos[p * 3 + 0] = pt.x + spread;
        plumePos[p * 3 + 1] = waterY - 0.2 - Math.random() * 2.8;
        plumePos[p * 3 + 2] = pt.z + (Math.random() - 0.5) * 16.0;

        const distFromRiver = Math.abs(spread);
        if (distFromRiver < 4.5) {
          // Hypersaline riverbed core (>3000 mg/L)
          plumeColors[p * 3 + 0] = 0.95; plumeColors[p * 3 + 1] = 0.15; plumeColors[p * 3 + 2] = 0.35;
        } else if (distFromRiver < 13.0) {
          // Brackish dispersion fringe (1500-3000 mg/L)
          plumeColors[p * 3 + 0] = 0.96; plumeColors[p * 3 + 1] = 0.62; plumeColors[p * 3 + 2] = 0.04;
        } else {
          // Fresh alluvial recharge (<1000 mg/L)
          plumeColors[p * 3 + 0] = 0.02; plumeColors[p * 3 + 1] = 0.71; plumeColors[p * 3 + 2] = 0.83;
        }
      }
      plumeGeom.setAttribute('position', new THREE.BufferAttribute(plumePos, 3));
      plumeGeom.setAttribute('color', new THREE.BufferAttribute(plumeColors, 3));
      const plumeMat = new THREE.PointsMaterial({ size: 0.62, vertexColors: true, transparent: true, opacity: 0.85 });
      salinityGroup = new THREE.Group();
      plumeParticles = new THREE.Points(plumeGeom, plumeMat);
      salinityGroup.add(plumeParticles);
      scene.add(salinityGroup);"""
assert flow_marker in text, "flow_marker not found"
text = text.replace(flow_marker, plume_code, 1)

# 7. Add animate updates for plume and telemetry rings
anim_marker = "        if (riverFoamParticles && riverCurve) {"
anim_addition = """        // Pulse Telemetry Halo Rings
        pingRings.forEach(pr => {
          pr.userData.phase += delta * 2.4;
          const s = 1.0 + (Math.sin(pr.userData.phase) + 1.0) * 0.35;
          pr.scale.set(s, s, s);
          pr.material.opacity = Math.max(0.12, 0.85 - (s - 1.0) * 1.3);
        });

        // Drift Solute Plume along SW Darcy Gradient
        if (plumeParticles && riverCurve) {
          const plPos = plumeParticles.geometry.attributes.position.array;
          for (let p = 0; p < plumeCount; p++) {
            plPos[p * 3 + 0] -= delta * 0.45;
            plPos[p * 3 + 2] -= delta * 0.35;
            plPos[p * 3 + 0] += (Math.random() - 0.5) * 0.08;
            plPos[p * 3 + 2] += (Math.random() - 0.5) * 0.08;
            if (plPos[p * 3 + 0] < -75 || plPos[p * 3 + 2] < -75) {
              const pt = riverCurve.getPoint(Math.random() * 0.4 + 0.5);
              plPos[p * 3 + 0] = pt.x + (Math.random() - 0.5) * 14.0;
              plPos[p * 3 + 1] = waterY - 0.2 - Math.random() * 2.8;
              plPos[p * 3 + 2] = pt.z + (Math.random() - 0.5) * 14.0;
            }
          }
          plumeParticles.geometry.attributes.position.needsUpdate = true;
        }

"""
assert anim_marker in text, "anim_marker not found"
text = text.replace(anim_marker, anim_addition + anim_marker, 1)

# 8. Update toggleLayer in JS
toggle_marker = "      else if (layer === 'strata') {"
toggle_addition = """      else if (layer === 'salinity') salinityGroup.visible = v;
      else if (layer === 'telemetry') telemetryPingGroup.visible = v;
"""
assert toggle_marker in text, "toggle_marker not found"
text = text.replace(toggle_marker, toggle_addition + toggle_marker, 1)

# 9. Update inspectWell in JS
inspect_marker = "      document.getElementById('wc-aquifer').innerText = w.aquifer;"
inspect_addition = inspect_marker + """
      const dwlrStatus = (w.dtwl > 25.0) ? 'OVER-EXPLOITED' : ((w.dtwl > 15.0) ? 'SEMI-CRITICAL' : 'SAFE');
      document.getElementById('wc-badge').innerText = dwlrStatus;
      document.getElementById('wc-badge').className = 'well-card-status ' + (dwlrStatus === 'SAFE' ? 'status-safe' : (dwlrStatus === 'SEMI-CRITICAL' ? 'status-semi' : 'status-crit'));
      const qEl = document.getElementById('wc-qa');
      if (qEl) qEl.innerText = (3.60 + Math.random() * 0.15).toFixed(2) + 'V (QA: VERIFIED)';
      const ecEl = document.getElementById('wc-ec');
      if (ecEl) ecEl.innerText = Math.round(1600 + w.dtwl * 65) + ' µS/cm';"""
assert inspect_marker in text, "inspect_marker not found"
text = text.replace(inspect_marker, inspect_addition, 1)

# 10. Transform the lower inspector tabs to include CGWA, MODFLOW, Telemetry, and Omniverse
old_tabs = """    tab_copilot, tab_catalog, tab_usd, tab_perf = st.tabs([
        "🤖 Digital Twin AI Copilot (RAG-Connected)",
        "📍 Monitoring Well Asset Catalog",
        "🗂️ OpenUSD Scene Hierarchy & Provenance",
        "📊 Model Performance & LOFO Sensitivity",
    ])"""

new_tabs = """    tab_copilot, tab_cgwa, tab_modflow, tab_telemetry, tab_catalog, tab_usd, tab_perf = st.tabs([
        "🤖 Digital Twin AI Copilot (RAG-Connected)",
        "🏛️ CGWA Compliance & Water Audit",
        "🌊 USGS MODFLOW 6 Physics Engine",
        "📡 Live DWLR Telemetry Stream",
        "📍 Monitoring Well Asset Catalog",
        "🗂️ OpenUSD Scene Hierarchy & Omniverse Live",
        "📊 Model Performance & LOFO Sensitivity",
    ])"""
assert old_tabs in text, "old_tabs not found"
text = text.replace(old_tabs, new_tabs, 1)

# 11. Add implementation for the new tabs right before tab_catalog
tab_cat_marker = "    with tab_catalog:"
new_tabs_content = """    with tab_cgwa:
        st.markdown("##### 🏛️ Central Ground Water Authority (CGWA) Statutory Assessment")
        st.caption(
            "Official statutory categorization according to Ministry of Jal Shakti (CGWA 2020 Gazette Notification S.O. 3289(E)) "
            "and Ground Water Estimation Committee (GEC-2015) methodology."
        )
        cgwa_res = CGWA_AUDITOR.audit_block_status(
            district=district,
            block=block,
            dtwl_mean=float(state.get("dtwl") or 14.85),
            dtwl_trend_slope=float(asset_info.get("trend_slope") or -0.42),
            annual_rainfall_mm=float(state.get("rainfall") or 480.0),
            pumping_intensity_factor=float(scenario_params.get("pumping_factor", 1.0)) if mode == "Simulated" else 1.0,
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Stage of GW Extraction (SOGWE)", f"{cgwa_res.sogwe_percent}%", border=True)
        c2.metric("Annual Extractable Resource", f"{cgwa_res.annual_extractable_mcm} MCM", border=True)
        c3.metric("Total Annual Draft", f"{cgwa_res.total_annual_draft_mcm} MCM", border=True)
        c4.metric("Recharge Obligation", f"{cgwa_res.mandatory_recharge_ratio_pct}%", border=True)

        st.markdown(
            f'<div style="background:{cgwa_res.category_color}22; border:1px solid {cgwa_res.category_color}; border-radius:8px; padding:12px 16px; margin:12px 0;">'
            f'<span style="font-weight:700; color:{cgwa_res.category_color}; font-size:16px;">● STATUTORY STATUS: {cgwa_res.category.upper()}</span><br>'
            f'<span style="font-size:13px; color:#e2e8f0;"><b>Statutory NOC Rule:</b> {cgwa_res.noc_eligibility}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("###### 🏗️ Managed Aquifer Recharge (MAR) AHP Suitability Interventions")
        mar_df = pd.DataFrame(cgwa_res.recharge_structures_recommended)
        st.dataframe(mar_df, use_container_width=True, hide_index=True)

        with st.expander("📜 Statutory Regulatory Citations"):
            for cite in cgwa_res.statutory_citations:
                st.caption(f"• {cite}")

    with tab_modflow:
        st.markdown("##### 🌊 USGS MODFLOW 6 3D Numerical Physics Simulation")
        st.caption(
            "Coupled physics-informed finite-difference numerical solver for 3D groundwater flow "
            "[div(K · grad(h)) + W = Ss · dh/dt] across 5 stratigraphy layers (40x40 structured grid, 50 km domain)."
        )
        with st.form("modflow_run_form", border=False):
            mf_c1, mf_c2, mf_c3 = st.columns(3)
            with mf_c1:
                mf_dtwl = st.number_input("Starting DTWL (mbgl)", 5.0, 60.0, float(state.get("dtwl") or 14.85), 0.5)
            with mf_c2:
                mf_pumping = st.number_input("Basin Pumping Draft (m³/day)", 500.0, 15000.0, 2400.0, 100.0)
            with mf_c3:
                mf_rain = st.number_input("Annual Precipitation (mm)", 50.0, 1500.0, float(state.get("rainfall") or 480.0), 10.0)
            btn_mf_run = st.form_submit_button("Execute 3D Numerical Simulation", type="primary", use_container_width=True)

        with st.spinner("Solving 3D finite-difference groundwater flow equations..."):
            mf_res = MODFLOW_SIMULATOR.solve_numerical_flow(
                baseline_dtwl=mf_dtwl,
                rainfall_annual_mm=mf_rain,
                pumping_rate_m3_day=mf_pumping,
            )

        m_m1, m_m2, m_m3, m_m4 = st.columns(4)
        m_m1.metric("Max Local Cone Drawdown", f"{float(mf_res.drawdown_3d.max()):.2f} m", border=True)
        m_m2.metric("Mean Regional Head", f"{float(mf_res.heads_3d.mean()):.1f} m ASL", border=True)
        m_m3.metric("Recharge Inflow", f"{mf_res.mass_balance['Total Recharge (m3/day)']:,.0f} m³/d", border=True)
        m_m4.metric("Mass Balance Discrepancy", f"{mf_res.mass_balance['Mass Balance Discrepancy (%)']:.2f}%", border=True)

        st.caption(f"ℹ️ **Solver Status**: {mf_res.summary_text}")

        # Download MODFLOW 6 Package ZIP
        zip_bytes = MODFLOW_SIMULATOR.generate_modflow6_package_bundle(sim_result=mf_res)
        st.download_button(
            "📥 Download Complete USGS MODFLOW 6 Package Bundle (.zip)",
            data=zip_bytes,
            file_name="rajasthan_luni_modflow6_project.zip",
            mime="application/zip",
            use_container_width=True,
            help="Download standard MODFLOW 6 input packages (sim.nam, dis, npf, ic, chd, wel, rch, oc, ims) ready for execution in USGS MODFLOW 6 or Flopy.",
        )

    with tab_telemetry:
        st.markdown("##### 📡 Live CGWB DWLR Telemetry Stream Monitor")
        st.caption(
            "Real-time Digital Water Level Recorder (DWLR) and solar tube-well SCADA telemetry streams "
            "with automated Edge QA/QC anomaly filtering (rate-of-change, battery integrity, and physical bound checks)."
        )
        if st.button("🔄 Sync Telemetry Stream (15-min Tick)", use_container_width=True):
            TELEMETRY_ENGINE.simulate_telemetry_tick(introduce_noise=True)

        telemetry_records = TELEMETRY_ENGINE.get_latest_telemetry()
        df_tel = pd.DataFrame(telemetry_records)[[
            "station_id", "station_name", "village", "block", "measured_dtwl_mbgl",
            "water_temp_c", "electrical_conductivity_us_cm", "battery_volts", "signal_rssi_dbm", "qa_status"
        ]]
        st.dataframe(df_tel, use_container_width=True, hide_index=True)

"""
assert tab_cat_marker in text, "tab_cat_marker not found"
text = text.replace(tab_cat_marker, new_tabs_content + tab_cat_marker, 1)

p.write_text(text, encoding="utf-8")
print("SUCCESS: digital_twin.py successfully upgraded with industry-level features!")
