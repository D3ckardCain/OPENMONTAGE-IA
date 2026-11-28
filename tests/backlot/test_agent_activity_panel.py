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
        self.assertIn('id="agent-memory-list"', html.text)
        self.assertIn('id="agent-memory-form"', html.text)
        self.assertNotIn('<pre id="events">', html.text)

        script = client.get('/ui/studio.js')
        self.assertEqual(script.status_code, 200)
        self.assertIn('function renderAgentActivity(projectState={})', script.text)
        self.assertIn('events.slice(-12).reverse()', script.text)
        self.assertIn('projectState?.stages', script.text)
        self.assertIn('projectState?.production_pipeline_available!==false', script.text)
        self.assertIn('Proyecto de edición', script.text)
        self.assertIn('projectState?.artifacts', script.text)
        self.assertIn('safeProjectMediaUrl', script.text)
        self.assertIn('state.identity?.restart_required===false', script.text)
        self.assertIn('function startAgentActivityPolling()', script.text)
        self.assertIn('if(open){startAgentActivityPolling();loadAgentActivity()}', script.text)
        self.assertIn('setInterval(()=>{if(!document.hidden&&!$(\'#agent-drawer\').hidden)loadAgentActivity()},5000)', script.text)
        self.assertIn('requestId!==agentActivityRequest||pid!==state.pid', script.text)
        self.assertIn('stopAgentActivityPolling()', script.text)
        self.assertIn('Solicitar detención', html.text)
        self.assertIn('el cierre del proceso aún no está confirmado', script.text)
        self.assertIn("runAgentAction('approve')", script.text)
        self.assertIn("kind==='model_usage'", script.text)
        self.assertIn("usage[key]", script.text)
        self.assertIn("ev.outcome==='unknown'", script.text)
        self.assertNotIn("$('#events').textContent=", script.text)
        self.assertIn('async function loadAgentMemory(', script.text)
        self.assertIn('captured_revision_matches', script.text)
        self.assertIn('Retirar del índice', script.text)
        self.assertIn("operation:'forget'", script.text)

        css = client.get('/ui/studio.css')
        self.assertEqual(css.status_code, 200)
        self.assertIn('.agent-activity-card[data-kind=error]', css.text)
        self.assertIn('.agent-activity-metrics', css.text)
        self.assertIn('.agent-stage-list', css.text)
        self.assertIn('.agent-artifact-list', css.text)


if __name__ == '__main__':
    unittest.main()
