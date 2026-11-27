"""Protect the browser CI runner from latest-image package-set drift."""
import re
from pathlib import Path

def test_browser_job_pins_supported_ubuntu_lts_and_keeps_browser_setup():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "openmontage-connectors.yml").read_text(encoding="utf-8")
    match = re.search(r"(?ms)^  browser-regressions:\n(.*)\Z", workflow)
    assert match, "browser-regressions job missing"
    job = match.group(1)
    assert re.search(r"(?m)^    runs-on: ubuntu-24\.04$", job)
    assert "timeout-minutes: 6" in job
    assert "timeout-minutes: 6\n        run: bash .github/scripts/ensure-media-cli.sh" in job
    assert "python -m playwright install --with-deps chromium" in job
    assert "Browser tests with external networking disabled" in job
