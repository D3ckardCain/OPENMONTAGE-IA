"""Delivery contract for the shared local agent activity panel."""
import unittest
from fastapi.testclient import TestClient
from backlot.server import create_app


class AgentActivityPanelTests(unittest.TestCase):
    def test_studio_serves_compact_accessible_recent_activity(self):
        client = TestClient(create_app(), base_url='http://127.0.0.1')
        html = client.get('/studio')
        self.assertEqual(html.status_code, 200)
        self.assertIn('id="events" class="agent-activity" role="log"', html.text)
        self.assertIn('aria-live="polite"', html.text)
        self.assertNotIn('<pre id="events">', html.text)

        script = client.get('/ui/studio.js')
        self.assertEqual(script.status_code, 200)
        self.assertIn('function renderAgentActivity(events)', script.text)
        self.assertIn('all.slice(-12).reverse()', script.text)
        self.assertIn("kind==='model_usage'", script.text)
        self.assertIn("usage[key]", script.text)
        self.assertIn("ev.outcome==='unknown'", script.text)
        self.assertNotIn("$('#events').textContent=", script.text)

        css = client.get('/ui/studio.css')
        self.assertEqual(css.status_code, 200)
        self.assertIn('.agent-activity-card[data-kind=error]', css.text)
        self.assertIn('.agent-activity-metrics', css.text)


if __name__ == '__main__':
    unittest.main()
