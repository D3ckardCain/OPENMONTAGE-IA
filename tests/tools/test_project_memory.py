"""Offline contract checks for explicit project-scoped memory."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sqlite3

from lib import production_studio as studio, production_agent as agent, project_memory


class ProjectMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_projects = studio.PROJECTS_DIR
        studio.PROJECTS_DIR = Path(self.temp.name) / 'projects'
        self.projects = studio.PROJECTS_DIR
        for project_id in ('alpha', 'beta'):
            path = self.projects / project_id
            path.mkdir(parents=True)
            (path / 'production_request.json').write_text(
                json.dumps({'title': 'Test project', 'project_id': project_id}), encoding='utf-8')
            (path / 'project.json').write_text(
                json.dumps({'project_id': project_id}), encoding='utf-8')

    def tearDown(self):
        studio.PROJECTS_DIR = self.previous_projects
        self.temp.cleanup()

    @staticmethod
    def local_agent(project_id):
        instance = agent.LocalAgent.__new__(agent.LocalAgent)
        instance.pid = project_id
        return instance

    def call(self, project_id, name, **args):
        return self.local_agent(project_id).dispatch(name, args)

    def test_spanish_search_provenance_and_cross_project_isolation(self):
        saved = self.call('alpha', 'project_memory_remember',
            kind='explicit_preference',
            text='Mantener el español y conservar la negación no traducida.',
            source_type='user_statement', source_ref='conversation:message-17')
        self.assertTrue(saved['stored'])
        found = self.call('alpha', 'project_memory_search', query='espanol negacion')
        self.assertEqual(found['method'], 'sqlite_fts5_bm25')
        self.assertEqual(len(found['results']), 1)
        result = found['results'][0]
        self.assertEqual(result['memory_id'], saved['memory_id'])
        self.assertEqual(result['source_ref'], 'conversation:message-17')
        self.assertFalse(result['instruction_eligible'])
        self.assertTrue(result['captured_revision_matches'])
        self.assertEqual(self.call('beta', 'project_memory_search', query='espanol')['results'], [])

    def test_duplicates_versions_and_supersession_are_explicit(self):
        initial = self.call('alpha', 'project_memory_remember',
            kind='creative_decision', text='Usar encuadre vertical 9:16.',
            source_type='user_statement', source_ref='conversation:message-22')
        duplicate = self.call('alpha', 'project_memory_remember',
            kind='creative_decision', text='Usar encuadre vertical 9:16.',
            source_type='user_statement', source_ref='conversation:message-22')
        self.assertTrue(duplicate['duplicate'])
        self.assertEqual(initial['memory_id'], duplicate['memory_id'])

        manual = self.projects / 'alpha' / 'artifacts' / 'manual_edit.json'
        manual.parent.mkdir(parents=True, exist_ok=True)
        manual.write_text(json.dumps({'revision': 2, 'edit_decisions': {'cuts': []}}), encoding='utf-8')
        updated = self.call('alpha', 'project_memory_remember',
            kind='creative_decision', text='Usar encuadre vertical 4:5.',
            source_type='user_statement', source_ref='conversation:message-23',
            supersedes_id=initial['memory_id'])
        rows = project_memory.search('alpha', 'encuadre')
        self.assertEqual([row['memory_id'] for row in rows['results']], [updated['memory_id']])
        self.assertTrue(rows['results'][0]['captured_revision_matches'])
        historical = project_memory.search('alpha', 'encuadre 9:16')['results']
        self.assertNotIn(initial['memory_id'], [row['memory_id'] for row in historical])

    def test_external_evidence_is_context_not_instruction_and_forget_is_soft(self):
        saved = self.call('alpha', 'project_memory_remember',
            kind='evidence', text='La fuente externa afirma una cifra de prueba.',
            source_type='external_source', source_ref='https://example.invalid/report')
        result = self.call('alpha', 'project_memory_search', query='fuente externa')
        self.assertFalse(result['results'][0]['instruction_eligible'])
        forgotten = self.call('alpha', 'project_memory_forget', memory_id=saved['memory_id'])
        self.assertTrue(forgotten['forgotten'])
        self.assertEqual(forgotten['storage'], 'retained_inactive_receipt')
        self.assertEqual(self.call('alpha', 'project_memory_search', query='fuente externa')['results'], [])
        self.assertTrue(project_memory.forget('alpha', saved['memory_id'])['already_inactive'])

    def test_fts_unavailable_uses_local_lexical_fallback(self):
        self.call('alpha', 'project_memory_remember',
            kind='verified_result', text='La búsqueda léxica funciona sin FTS.',
            source_type='tool_receipt', source_ref='receipt:qa-1')
        with mock.patch.object(project_memory, '_fts_rows',
                               side_effect=sqlite3.OperationalError('FTS5 unavailable')):
            result = self.call('alpha', 'project_memory_search', query='busqueda lexica')
        self.assertEqual(result['method'], 'local_lexical_fallback')
        self.assertEqual(len(result['results']), 1)


if __name__ == '__main__':
    unittest.main()
