"""telemetry_stream.py — Real-Time IoT Telemetry Stream & Edge QA/QC Engine for Naya Pani.

Provides enterprise-grade telemetry ingestion from CGWB Digital Water Level Recorders (DWLR)
and solar tube-well SCADA sensors across the Rajasthan Luni Basin:
1. Ingests or simulates streaming live piezometric telemetry packets (DTWL, water temp, EC, battery V, RSSI).
2. Edge QA/QC Validation Filters:
   - Rate-of-Change (Spike) Filter: flags casing reflections or sensor drop glitches (>2.5 m/hr delta).
   - Voltage Integrity Filter: flags battery depletion anomalies (<3.3V).
   - Out-of-Range Physical Bounds: flags dry sensor casing or sub-bedrock readings.
3. Thread-Safe Live Buffer for real-time 3D Digital Twin animation and telemetry beacon synchronization.
"""

from __future__ import annotations

import math
import random
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TelemetryPacket:
    station_id: str
    station_name: str
    village: str
    block: str
    latitude: float
    longitude: float
    surface_elev_m: float
    measured_dtwl_mbgl: float
    water_temp_c: float
    electrical_conductivity_us_cm: float  # Salinity indicator
    battery_volts: float
    signal_rssi_dbm: int
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    qa_status: str = "VERIFIED_VALID"     # "VERIFIED_VALID", "SUSPECT_SPIKE", "LOW_BATTERY_FAULT", "PHYSICAL_BOUNDS_ERROR"
    qa_flags: list[str] = field(default_factory=list)


# Reference CGWB DWLR Telemetry Stations across Upper Luni Basin (Ajmer - Nagaur - Pali corridor)
DEFAULT_DWLR_STATIONS: list[dict[str, Any]] = [
    {"id": "DWLR-RJ-AJM-001", "name": "Govindgarh CGWB Piezometer", "village": "Govindgarh", "block": "Pisangan", "lat": 26.4520, "lon": 74.6290, "elev": 482.0, "base_dtwl": 14.85, "base_ec": 1820.0},
    {"id": "DWLR-RJ-AJM-002", "name": "Pushkar Ghat Hydro-Telemetry", "village": "Pushkar Rural", "block": "Pisangan", "lat": 26.4880, "lon": 74.5510, "elev": 496.0, "base_dtwl": 12.40, "base_ec": 1420.0},
    {"id": "DWLR-RJ-AJM-003", "name": "Pisangan Alluvial Observatory", "village": "Pisangan Plains", "block": "Pisangan", "lat": 26.3950, "lon": 74.4820, "elev": 458.0, "base_dtwl": 22.10, "base_ec": 3250.0},
    {"id": "DWLR-RJ-AJM-004", "name": "Srinagar Granite Contact Well", "village": "Srinagar East", "block": "Srinagar", "lat": 26.4380, "lon": 74.7890, "elev": 512.0, "base_dtwl": 18.60, "base_ec": 1640.0},
    {"id": "DWLR-RJ-AJM-005", "name": "Saradhna Highway Piezometer", "village": "Saradhna South", "block": "Pisangan", "lat": 26.3310, "lon": 74.5720, "elev": 465.0, "base_dtwl": 16.90, "base_ec": 2410.0},
    {"id": "DWLR-RJ-NAG-006", "name": "Riyan Badi Basin Border Well", "village": "Riyan Badi", "block": "Riyan", "lat": 26.5410, "lon": 74.3120, "elev": 435.0, "base_dtwl": 28.40, "base_ec": 4120.0},
    {"id": "DWLR-RJ-PAL-007", "name": "Jaitaran Downstream Piezometer", "village": "Jaitaran Outflow", "block": "Jaitaran", "lat": 26.2110, "lon": 73.9450, "elev": 395.0, "base_dtwl": 31.80, "base_ec": 5480.0},
]


class EdgeQAQCValidator:
    """Automated edge telemetry validation & anomaly filter."""

    @staticmethod
    def validate_packet(
        current_packet: TelemetryPacket,
        previous_packet: TelemetryPacket | None = None,
    ) -> TelemetryPacket:
        flags: list[str] = []
        status = "VERIFIED_VALID"

        # 1. Physical Bounds Check
        dtwl = current_packet.measured_dtwl_mbgl
        if dtwl < 0.1 or dtwl > 200.0:
            flags.append(f"DTWL {dtwl} mbgl exceeds physical basin limits [0.1, 200.0]")
            status = "PHYSICAL_BOUNDS_ERROR"

        # 2. Battery Health Filter
        if current_packet.battery_volts < 3.30:
            flags.append(f"Telemetry station battery low: {current_packet.battery_volts:.2f}V (threshold: 3.30V)")
            if status == "VERIFIED_VALID":
                status = "LOW_BATTERY_FAULT"

        # 3. Rate-of-Change (Spike) Filter
        if previous_packet is not None:
            delta_h = abs(dtwl - previous_packet.measured_dtwl_mbgl)
            if delta_h > 2.50:  # More than 2.5m shift in 1 telemetry tick
                flags.append(f"Suspicious rate-of-change spike: {delta_h:.2f}m delta from previous observation")
                status = "SUSPECT_SPIKE"

        # 4. Salinity (Electrical Conductivity) Sanity
        if current_packet.electrical_conductivity_us_cm > 25_000.0:
            flags.append("Electrical conductivity sensor clipping at hyper-saline ceiling")

        current_packet.qa_status = status
        current_packet.qa_flags = flags
        return current_packet


class LiveTelemetryBuffer:
    """Thread-safe in-memory buffer storing real-time DWLR telemetry feeds."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stations: dict[str, dict[str, Any]] = {s["id"]: dict(s) for s in DEFAULT_DWLR_STATIONS}
        self._latest_packets: dict[str, TelemetryPacket] = {}
        self._history: list[TelemetryPacket] = []
        self._max_history = 500

        # Initialize with baseline packets
        self.simulate_telemetry_tick(introduce_noise=False)

    def simulate_telemetry_tick(self, introduce_noise: bool = True) -> list[TelemetryPacket]:
        """Generate a simulated 15-minute telemetry sync tick across all CGWB DWLR stations."""
        with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            new_packets: list[TelemetryPacket] = []

            for st_id, st in self._stations.items():
                prev_packet = self._latest_packets.get(st_id)

                # Diurnal solar pumping drawdown effect + subtle Brownian walk
                hour = datetime.now(timezone.utc).hour
                diurnal_drawdown = 0.35 * math.sin((hour - 8) * math.pi / 12) if 8 <= hour <= 18 else -0.15

                noise = (random.gauss(0, 0.04)) if introduce_noise else 0.0
                curr_dtwl = round(max(1.0, st["base_dtwl"] + diurnal_drawdown + noise), 2)

                # Battery voltage: slight drain or solar recharge during daytime
                batt = 3.65 + (0.15 * math.sin(hour * math.pi / 12)) + random.gauss(0, 0.01)
                rssi = int(random.gauss(-78, 4))
                temp = round(26.5 + random.gauss(0, 0.3), 1)

                # Salinity EC variation
                ec = round(st["base_ec"] + random.gauss(0, 25.0), 1)

                raw_pkt = TelemetryPacket(
                    station_id=st_id,
                    station_name=st["name"],
                    village=st["village"],
                    block=st["block"],
                    latitude=st["lat"],
                    longitude=st["lon"],
                    surface_elev_m=st["elev"],
                    measured_dtwl_mbgl=curr_dtwl,
                    water_temp_c=temp,
                    electrical_conductivity_us_cm=ec,
                    battery_volts=round(batt, 2),
                    signal_rssi_dbm=rssi,
                    timestamp_utc=now_iso,
                )

                validated_pkt = EdgeQAQCValidator.validate_packet(raw_pkt, prev_packet)
                self._latest_packets[st_id] = validated_pkt
                self._history.append(validated_pkt)
                new_packets.append(validated_pkt)

            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

            return new_packets

    def get_latest_telemetry(self) -> list[dict[str, Any]]:
        """Return all latest verified telemetry readings."""
        with self._lock:
            return [asdict(pkt) for pkt in self._latest_packets.values()]

    def get_station_packet(self, station_id: str) -> dict[str, Any] | None:
        with self._lock:
            pkt = self._latest_packets.get(station_id)
            return asdict(pkt) if pkt else None

    def to_geojson(self) -> dict[str, Any]:
        """Format live telemetry stations as GeoJSON FeatureCollection."""
        with self._lock:
            features = []
            for pkt in self._latest_packets.values():
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [pkt.longitude, pkt.latitude, pkt.surface_elev_m],
                    },
                    "properties": asdict(pkt),
                })
            return {
                "type": "FeatureCollection",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "features": features,
            }


TELEMETRY_ENGINE = LiveTelemetryBuffer()
