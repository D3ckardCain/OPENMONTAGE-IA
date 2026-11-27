import re
import unittest
from pathlib import Path


class StudioEditorCapabilitiesTest(unittest.TestCase):
    def test_visible_capability_summary_separates_working_features_from_gaps(self):
        html = (Path(__file__).resolve().parents[2] / 'backlot' / 'ui' / 'studio.html').read_text(encoding='utf-8')
        match = re.search(r'<summary>Alcance y funciones pendientes</summary>(.*?)</details>', html)
        self.assertIsNotNone(match, 'the collapsed editor capability panel remains available')
        panel = match.group(1)
        self.assertIn('Disponibles:', panel)
        self.assertIn('mezcla por pistas', panel)
        self.assertIn('automatizaci&#243;n de volumen y ducking', panel)
        self.assertIn('EQ/compresor y bypass durante la exportaci&#243;n local', panel)
        self.assertIn('rampas de velocidad y keyframes visuales de capas', panel)
        self.assertIn('matiz HSL global', panel)
        self.assertRegex(panel, r'Pendiente: buses de mezcla.*DSP en directo.*HSL por rangos, LUT/scopes.*clips principales y t&#237;tulos')
        self.assertNotRegex(panel, r'Pendientes:.*curvas de velocidad')


if __name__ == '__main__':
    unittest.main()
