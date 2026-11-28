"""Project-local memory API: provenance, supersession and reversible index retirement."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_agent as agent, production_studio as studio, project_memory


class ProjectMemoryRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_projects = studio.PROJECTS_DIR
        studio.PROJECTS_DIR = Path(self.temp.name) / 'projects'
        self.pid = 'memory-qa'
        project = studio.PROJECTS_DIR / self.pid
        project.mkdir(parents=True)
        (project / 'production_request.json').write_text(
            json.dumps({'title': 'Memory QA', 'project_id': self.pid}), encoding='utf-8')
        (project / 'project.json').write_text(json.dumps({'project_id': self.pid}), encoding='utf-8')
        self.client = TestClient(create_app(), base_url='http://127.0.0.1')

    def tearDown(self):
        studio.PROJECTS_DIR = self.previous_projects
        self.temp.cleanup()

    def test_project_list_supersedes_and_soft_retirement_keep_provenance(self):
        first = project_memory.remember(
            self.pid, kind='explicit_preference', text='Conservar la negación en español.',
            source_type='user_statement', source_ref='conversation:message-14')
        listed = self.client.get(f'/api/studio/projects/{self.pid}/memory')
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()['scope'], 'project')
        self.assertEqual(listed.json()['entries'][0]['memory_id'], first['memory_id'])
        self.assertTrue(listed.json()['entries'][0]['captured_revision_matches'])
        self.assertFalse(listed.json()['entries'][0]['instruction_eligible'])

        corrected = self.client.post(f'/api/studio/projects/{self.pid}/memory', json={
            'operation': 'remember', 'kind': 'explicit_preference',
            'text': 'Conservar negaciones y su contexto original.',
            'source_ref': 'conversation:message-15', 'supersedes_id': first['memory_id']})
        self.assertEqual(corrected.status_code, 200)
        self.assertTrue(corrected.json()['stored'])
        rows = self.client.get(f'/api/studio/projects/{self.pid}/memory').json()['entries']
        by_id = {row['memory_id']: row for row in rows}
        self.assertFalse(by_id[first['memory_id']]['active'])
        new_id = corrected.json()['memory_id']
        self.assertTrue(by_id[new_id]['active'])
        self.assertEqual(by_id[new_id]['source_type'], 'user_statement')
        self.assertEqual(by_id[new_id]['source_ref'], 'conversation:message-15')

        forgotten = self.client.post(f'/api/studio/projects/{self.pid}/memory', json={
            'operation': 'forget', 'memory_id': new_id})
        self.assertEqual(forgotten.status_code, 200)
        self.assertTrue(forgotten.json()['forgotten'])
        second = self.client.post(f'/api/studio/projects/{self.pid}/memory', json={
            'operation': 'forget', 'memory_id': new_id})
        self.assertTrue(second.json()['already_inactive'])
        historical = self.client.get(f'/api/studio/projects/{self.pid}/memory').json()['entries']
        self.assertFalse(next(row for row in historical if row['memory_id'] == new_id)['active'])

    def test_unknown_fields_invalid_kind_and_active_agent_block_writes(self):
        bad = self.client.post(f'/api/studio/projects/{self.pid}/memory', json={
            'operation': 'remember', 'kind': 'verified_result', 'text': 'No evidence',
            'source_ref': 'conversation:message-2', 'extra': 'ignored'})
        self.assertEqual(bad.status_code, 400)
        unsupported = self.client.post(f'/api/studio/projects/{self.pid}/memory', json={
            'operation': 'remember', 'kind': 'evidence', 'text': 'No evidence',
            'source_ref': 'conversation:message-2'})
        self.assertEqual(unsupported.status_code, 400)
        with patch.dict(agent.ACTIVE, {self.pid: object()}):
            response = self.client.post(f'/api/studio/projects/{self.pid}/memory', json={
                'operation': 'remember', 'kind': 'creative_decision',
                'text': 'No concurrent edits.', 'source_ref': 'conversation:message-3'})
        self.assertEqual(response.status_code, 409)


if __name__ == '__main__':
    unittest.main()
