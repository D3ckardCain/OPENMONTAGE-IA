from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from backlot import system_monitor
from backlot.server import create_app


class StudioSystemMonitorTests(unittest.TestCase):
    def test_real_snapshot_uses_local_sources_and_preserves_unavailable_values(self):
        first = system_monitor.snapshot()
        second = system_monitor.snapshot()

        self.assertTrue(first["source"].startswith("local "))
        self.assertIsNone(first["cpu"]["temperature_c"])  # Generic ACPI zone is not a CPU sensor.
        self.assertGreater(second["memory"]["total_bytes"], 0)
        self.assertGreaterEqual(second["memory"]["usage_percent"], 0)
        self.assertLessEqual(second["memory"]["usage_percent"], 100)
        self.assertIsInstance(second["disks"], list)
        for disk in second["disks"]:
            self.assertGreater(disk["total_bytes"], 0)
            self.assertGreaterEqual(disk["usage_percent"], 0)
            self.assertLessEqual(disk["usage_percent"], 100)
        for gpu in second["gpus"]:
            self.assertTrue(gpu["name"])
            self.assertTrue(gpu["usage_percent"] is None or 0 <= gpu["usage_percent"] <= 100)
            self.assertTrue(gpu["temperature_c"] is None or 0 <= gpu["temperature_c"] <= 150)

    def test_gpu_cli_unknown_sensors_remain_none(self):
        with TemporaryDirectory() as directory:
            executable = f"{directory}\\nvidia-smi.exe"
            with patch.object(system_monitor.shutil, "which", return_value=executable), patch.object(
                system_monitor.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=0, stdout="NVIDIA test, N/A, N/A, N/A, N/A\n"),
            ):
                self.assertEqual(
                    system_monitor._gpu_devices(),
                    [{
                        "name": "NVIDIA test",
                        "usage_percent": None,
                        "temperature_c": None,
                        "memory_used_mb": None,
                        "memory_total_mb": None,
                    }],
                )

    def test_system_metrics_api_is_loopback_only_and_not_cached(self):
        sample = {
            "cpu": {"usage_percent": None, "temperature_c": None},
            "gpus": [],
            "memory": {"usage_percent": 50, "used_bytes": 50, "total_bytes": 100},
            "disks": [],
        }
        with patch.object(system_monitor, "snapshot", return_value=sample):
            with TestClient(create_app(), base_url="http://127.0.0.1", client=("127.0.0.1", 55001)) as local:
                response = local.get("/api/studio/system-metrics")
            with TestClient(create_app(), base_url="http://127.0.0.1", client=("203.0.113.8", 55002)) as remote:
                denied = remote.get("/api/studio/system-metrics")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.json(), sample)
        self.assertEqual(denied.status_code, 403)
        self.assertIn("solo se consultan desde este dispositivo", denied.json()["detail"])

    def test_timeline_monitor_precedes_split_and_calls_local_endpoint(self):
        from pathlib import Path

        root = Path(__file__).parents[2]
        html = (root / "backlot" / "ui" / "studio.html").read_text(encoding="utf-8")
        js = (root / "backlot" / "ui" / "studio.js").read_text(encoding="utf-8")
        css = (root / "backlot" / "ui" / "studio.css").read_text(encoding="utf-8")

        self.assertLess(html.index('id="system-monitor"'), html.index('id="clip-split"'))
        self.assertIn('id="system-cpu-temp">—', html)
        self.assertIn('id="system-gpu-temp">—', html)
        self.assertIn("'/api/studio/system-metrics'", js)
        self.assertIn("system-monitor-status", js)
        self.assertIn("data.collected_at||'sin fecha'}", js)
        self.assertIn(".system-monitor{", css)


if __name__ == "__main__":
    unittest.main()
