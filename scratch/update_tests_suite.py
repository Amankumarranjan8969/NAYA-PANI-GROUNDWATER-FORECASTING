from pathlib import Path

p = Path(r"D:\NIH_roorkee\FULL WORK FINAL_DIGITAL_NAYA_PANI\NAYA_PAANI\test_digital_twin_and_rag.py")
text = p.read_text(encoding="utf-8")

old_files = """        "security_engine.py",
        "rag/retriever.py","""

new_files = """        "security_engine.py",
        "modflow_engine.py",
        "telemetry_stream.py",
        "cgwa_auditor.py",
        "api_service.py",
        "rag/retriever.py","""
assert old_files in text, "old_files not found"
text = text.replace(old_files, new_files, 1)

test_8_code = """def test_8_industry_level_engines() -> None:
    from modflow_engine import MODFLOW_SIMULATOR
    from telemetry_stream import TELEMETRY_ENGINE
    from cgwa_auditor import CGWA_AUDITOR
    from fastapi.testclient import TestClient
    from api_service import app

    # 1. MODFLOW 6 3D Numerical Simulation
    mf_res = MODFLOW_SIMULATOR.solve_numerical_flow(baseline_dtwl=14.85, pumping_rate_m3_day=2400.0)
    assert mf_res.heads_3d.shape == (5, 40, 40)
    assert mf_res.drawdown_3d.shape == (5, 40, 40)
    assert float(mf_res.drawdown_3d.max()) > 0.0
    assert "Mass Balance Discrepancy (%)" in mf_res.mass_balance
    pkg = MODFLOW_SIMULATOR.generate_modflow6_package_bundle(sim_result=mf_res)
    assert len(pkg) > 1000

    # 2. Live DWLR Telemetry & Edge QA/QC Filter
    packets = TELEMETRY_ENGINE.simulate_telemetry_tick(introduce_noise=True)
    assert len(packets) >= 7
    for pkt in packets:
        assert pkt.qa_status in ("VERIFIED_VALID", "SUSPECT_SPIKE", "LOW_BATTERY_FAULT", "PHYSICAL_BOUNDS_ERROR")
        assert pkt.battery_volts > 2.0
    gj = TELEMETRY_ENGINE.to_geojson()
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) >= 7

    # 3. CGWA Statutory Regulatory Audit & MAR AHP Suitability
    cgwa_res = CGWA_AUDITOR.audit_block_status(district="Ajmer", block="Pisangan", dtwl_mean=18.5)
    assert cgwa_res.sogwe_percent > 0.0
    assert cgwa_res.category in ("Safe", "Semi-Critical", "Critical", "Over-Exploited", "Saline")
    assert len(cgwa_res.recharge_structures_recommended) >= 3
    assert cgwa_res.mandatory_recharge_ratio_pct >= 100

    # 4. FastAPI Microservice Client
    client = TestClient(app)
    h = client.get("/api/v1/health")
    assert h.status_code == 200
    assert h.json()["engines"]["modflow_numerical_solver"] == "ONLINE"

    t = client.get("/api/v1/telemetry/latest")
    assert t.status_code == 200
    assert len(t.json()) >= 7

    m = client.post("/api/v1/modflow/solve", json={"baseline_dtwl": 14.85})
    assert m.status_code == 200
    assert m.json()["max_drawdown_m"] > 0

    c = client.post("/api/v1/cgwa/audit", json={"district": "Ajmer", "block": "Pisangan"})
    assert c.status_code == 200
    assert "category" in c.json()

    o = client.get("/api/v1/digital-twin/omniverse-session")
    assert o.status_code == 200
    assert "session_nayapani_luni_basin_live" in o.json()["live_session_channel"]

    print("[PASS] 8. USGS MODFLOW 6 numerical solver, live DWLR telemetry stream, CGWA audit, and FastAPI microservices verified.")


"""

main_marker = 'if __name__ == "__main__":'
assert main_marker in text, "main_marker not found"
text = text.replace(main_marker, test_8_code + main_marker, 1)

main_call_marker = "    test_7_omniverse_openusd_and_simready(test_payload, test_twin_state)"
new_main_call = main_call_marker + "\n    test_8_industry_level_engines()"
assert main_call_marker in text, "main_call_marker not found"
text = text.replace(main_call_marker, new_main_call, 1)

p.write_text(text, encoding="utf-8")
print("SUCCESS: test_digital_twin_and_rag.py updated with Test 8!")
