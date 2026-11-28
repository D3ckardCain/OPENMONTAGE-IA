from pathlib import Path


def test_preferences_expose_capabilities_from_the_active_api_contract():
    root = Path(__file__).resolve().parents[2]
    html = (root / 'backlot' / 'ui' / 'studio.html').read_text(encoding='utf-8')
    js = (root / 'backlot' / 'ui' / 'studio.js').read_text(encoding='utf-8')
    assert 'id="module-settings"' in html and 'id="capability-list"' in html
    assert "'Disponible en API'" in js
    assert 'capabilityLabels' in js
    assert "hidden=!capabilities.has('audio_mix')" not in js
    assert "hasCapability('audio_mix')" in js
