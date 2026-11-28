"""Synthetic files and a fake native process exercise the real adapter."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
from jsonschema import validate

from lib import external_applications as applications
from lib import production_studio as studio
from lib.pipeline_loader import load_pipeline_readonly
from lib.production_agent import LocalAgent
from tools.base_tool import ToolResult, ToolStatus
from tools.character import rhubarb_lip_sync as rhubarb
from tools.tool_registry import ToolRegistry


class RhubarbIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / 'projects' / 'fixture'
        self.project.mkdir(parents=True)
        studio.save_json(self.project / 'production_request.json', {'pipeline': 'animation'})
        self.executable = self.root / 'runtime' / 'rhubarb.exe'
        self.executable.parent.mkdir()
        self.executable.write_bytes(b'synthetic executable, never run')
        self.resources = self.executable.parent / 'res' / 'sphinx'
        for name in ('cmudict-en-us.dict', 'en-us-phone.lm.bin', 'en-us.lm.bin',
                     'acoustic-model/mdef', 'acoustic-model/means', 'acoustic-model/variances'):
            file = self.resources / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b'synthetic resource')
        for owner, name, value in (
            (studio, 'CONFIG_DIR', self.root / 'config'),
            (studio, 'PROJECTS_DIR', self.root / 'projects'),
        ):
            replacement = patch.object(owner, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)
        self.previous = {name: {'executable': 'saved-' + name}
                         for name in ('blender', 'freecad', 'krita', 'kinovea', 'openscad', 'avogadro')}
        studio.save_json(studio.CONFIG_DIR / 'applications.json', self.previous)
        applications.configure('rhubarb', {'executable': str(self.executable)})
        self.audio = self.project / 'input.wav'
        self.audio.write_bytes(b'synthetic audio fixture, never analyzed')
        self.inputs = {'project_id': 'fixture', 'audio_path': 'input.wav',
                       'language': 'es', 'output_path': 'assets/cues.json'}
        probe_patch = patch.object(rhubarb, 'AudioProbe')
        self.probe = probe_patch.start()
        self.addCleanup(probe_patch.stop)
        self.probe.return_value.get_status.return_value = ToolStatus.AVAILABLE
        self.probe.return_value.execute.return_value = ToolResult(success=True, data={
            'duration_seconds': 1.0, 'format_name': 'wav', 'audio': {'codec': 'pcm_s16le'}})
        self.commands = []
        self.transform = lambda data: data
        runner_patch = patch.object(rhubarb.subprocess, 'run', side_effect=self.native)
        self.runner = runner_patch.start()
        self.addCleanup(runner_patch.stop)

    def native(self, command, **options):
        self.commands.append(command)
        if command[1:] == ['--version']:
            return subprocess.CompletedProcess(command, 0, 'Rhubarb Lip Sync version 1.14.0', '')
        self.assertIs(options['shell'], False)
        self.assertEqual(Path(command[-1]).read_bytes(), self.audio.read_bytes())
        native = {'metadata': {'soundFile': command[-1], 'duration': 1.0},
                  'mouthCues': [{'start': 0.0, 'end': 0.5, 'value': 'A'},
                                {'start': 0.5, 'end': 1.0, 'value': 'X'}]}
        output = Path(command[command.index('--output') + 1])
        output.write_text(json.dumps(self.transform(native)), encoding='utf-8')
        return subprocess.CompletedProcess(command, 0)

    def test_configuration_and_doctor_preserve_bindings(self):
        result = rhubarb.RhubarbDoctor().execute({})
        self.assertTrue(result.success, result.error)
        validate(result.data, rhubarb.RhubarbDoctor.output_schema)
        self.assertEqual(result.data['version'], '1.14.0')
        self.assertFalse(result.data['audio_analyzed'])
        self.assertEqual(result.data['executable_sha256'], rhubarb.sha256(self.executable))
        self.assertEqual(len(result.data['resource_sha256']), 6)
        for identifier, value in self.previous.items():
            self.assertEqual(applications.configuration()[identifier], value)
        self.assertTrue(all(command[1:] == ['--version'] for command in self.commands))

    def test_missing_executable_resources_and_version_failure(self):
        self.executable.unlink()
        self.assertIn('RHUBARB_NOT_CONFIGURED', rhubarb.RhubarbDoctor().execute({}).error)
        self.executable.write_bytes(b'fixture')
        (self.resources / 'en-us.lm.bin').unlink()
        self.assertIn('RHUBARB_RESOURCES_MISSING', rhubarb.RhubarbDoctor().execute({}).error)
        (self.resources / 'en-us.lm.bin').write_bytes(b'fixture')
        self.runner.side_effect = None
        self.runner.return_value = subprocess.CompletedProcess([], 1, '', 'version failed')
        self.assertIn('RHUBARB_VERSION_FAILED', rhubarb.RhubarbDoctor().execute({}).error)

    def test_analysis_report_and_input_provenance(self):
        original = self.audio.read_bytes()
        result = rhubarb.RhubarbLipSync().execute(self.inputs)
        self.assertTrue(result.success, result.error)
        validate(result.data, rhubarb.RhubarbLipSync.output_schema)
        report = json.loads(Path(result.artifacts[0]).read_text(encoding='utf-8'))
        self.assertEqual(report['metadata']['soundFile'], 'input.wav')
        self.assertEqual(report['provenance']['recognizer'], 'phonetic')
        self.assertEqual(report['provenance']['audio']['sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(result.data['report_sha256'], rhubarb.sha256(result.artifacts[0]))
        self.assertFalse(report['animation_generated'])
        self.assertEqual(result.data['cue_count'], 2)
        self.assertEqual(self.audio.read_bytes(), original)
        self.assertFalse(list((self.project / 'assets').glob('.rhubarb-*')))

    def test_english_default_and_dialog_snapshot(self):
        dialog = self.project / 'dialog.txt'
        dialog.write_text('Synthetic dialog', encoding='utf-8')
        result = rhubarb.RhubarbLipSync().execute({**self.inputs, 'language': 'en-US', 'dialog_path': 'dialog.txt'})
        self.assertTrue(result.success, result.error)
        self.assertEqual(result.data['provenance']['recognizer'], 'pocketSphinx')
        self.assertEqual(result.data['provenance']['dialog']['sha256'], rhubarb.sha256(dialog))
        self.assertIn('--dialogFile', self.commands[-1])

    def test_nonenglish_pocketsphinx_rejected_before_execution(self):
        result = rhubarb.RhubarbLipSync().execute({**self.inputs, 'recognizer': 'pocketSphinx'})
        self.assertFalse(result.success)
        self.assertIn('inglés', result.error)
        self.assertFalse(self.commands)

    def test_output_validation_rejects_bad_cues_and_metadata(self):
        cases = [
            lambda data: {**data, 'mouthCues': [{'start': 0, 'end': 1, 'value': 'Z'}]},
            lambda data: {**data, 'mouthCues': [{'start': -1, 'end': 1, 'value': 'A'}]},
            lambda data: {**data, 'mouthCues': [{'start': 0, 'end': float('nan'), 'value': 'A'}]},
            lambda data: {**data, 'mouthCues': [{'start': 0, 'end': 0.8, 'value': 'A'},
                                              {'start': 0.5, 'end': 1, 'value': 'X'}]},
            lambda data: {**data, 'metadata': {'duration': 2, 'soundFile': data['metadata']['soundFile']}},
            lambda data: {**data, 'metadata': {'duration': 1, 'soundFile': 'other.wav'}},
        ]
        for transform in cases:
            with self.subTest(transform=transform):
                self.transform = transform
                result = rhubarb.RhubarbLipSync().execute(self.inputs)
                self.assertIn('RHUBARB_OUTPUT_INVALID', result.error)
                self.assertFalse((self.project / 'assets/cues.json').exists())

    def test_existing_output_and_publication_race_preserve_previous_data(self):
        output = self.project / 'assets/cues.json'
        output.parent.mkdir()
        output.write_text('previous report', encoding='utf-8')
        self.assertIn('RHUBARB_OUTPUT_EXISTS', rhubarb.RhubarbLipSync().execute(self.inputs).error)
        self.assertEqual(output.read_text(), 'previous report')
        output.unlink()
        def race(source, destination):
            Path(destination).write_text('concurrent report')
            raise FileExistsError()
        with patch.object(rhubarb.os, 'link', side_effect=race):
            result = rhubarb.RhubarbLipSync().execute(self.inputs)
        self.assertIn('RHUBARB_OUTPUT_EXISTS', result.error)
        self.assertEqual(output.read_text(), 'concurrent report')

    def test_timeout_and_native_failure_leave_no_report(self):
        original = self.native
        def timeout(command, **options):
            if '--version' in command:
                return original(command, **options)
            raise subprocess.TimeoutExpired(command, 300)
        self.runner.side_effect = timeout
        self.assertIn('RHUBARB_TIMEOUT', rhubarb.RhubarbLipSync().execute(self.inputs).error)
        def failed(command, **options):
            if '--version' in command:
                return original(command, **options)
            options['stderr'].write(b'{"type":"failure","reason":"synthetic failure"}')
            return subprocess.CompletedProcess(command, 1)
        self.runner.side_effect = failed
        result = rhubarb.RhubarbLipSync().execute(self.inputs)
        self.assertIn('RHUBARB_PROCESS_FAILED', result.error)
        self.assertIn('synthetic failure', result.error)
        self.assertFalse((self.project / 'assets/cues.json').exists())

    def test_probe_and_codec_errors_are_clear(self):
        self.probe.return_value.execute.return_value = ToolResult(success=False, error='synthetic probe failure')
        self.assertIn('RHUBARB_AUDIO_INVALID', rhubarb.RhubarbLipSync().execute(self.inputs).error)
        ogg = self.project / 'input.ogg'
        ogg.write_bytes(b'synthetic Ogg fixture')
        self.probe.return_value.execute.return_value = ToolResult(success=True, data={
            'duration_seconds': 1.0, 'format_name': 'ogg', 'audio': {'codec': 'opus'}})
        result = rhubarb.RhubarbLipSync().execute({**self.inputs, 'audio_path': 'input.ogg'})
        self.assertIn('Vorbis', result.error)

    def test_paths_are_project_confined(self):
        outside = self.root / 'outside.wav'
        outside.write_bytes(b'private fixture')
        for fields in ({'audio_path': str(outside)}, {'dialog_path': str(outside)},
                       {'output_path': str(self.root / 'outside.json')}, {'output_path': 'job.json'}):
            with self.subTest(fields=fields):
                result = rhubarb.RhubarbLipSync().execute({**self.inputs, **fields})
                self.assertFalse(result.success)
        self.assertFalse(self.commands)

    def test_registry_and_agent_bridge(self):
        registry = ToolRegistry()
        registry.register_module(rhubarb)
        self.assertIsNotNone(registry.get('rhubarb_doctor'))
        self.assertEqual(registry.get('rhubarb_lip_sync').get_status(), ToolStatus.AVAILABLE)
        worker = LocalAgent.__new__(LocalAgent)
        worker.pid = 'fixture'
        worker.path = self.project
        worker.request = {'pipeline': 'animation'}
        worker.manifest = load_pipeline_readonly('animation')
        worker.registry = registry
        worker.reads = {'skills/' + worker.manifest['stages'][0]['skill'] + '.md'}
        worker.event = Mock()
        doctor = worker.dispatch('execute_tool', {'name': 'rhubarb_doctor', 'inputs': {}})
        self.assertTrue(doctor['success'], doctor['error'])
        result = worker.dispatch('execute_tool', {'name': 'rhubarb_lip_sync', 'inputs': self.inputs})
        self.assertTrue(result['success'], result['error'])
        self.assertEqual(result['cost_usd'], 0)
        self.assertFalse(result['data']['animation_generated'])

    def test_runtime_changes_are_rejected(self):
        def change(data):
            (self.resources / 'en-us.lm.bin').write_bytes(b'changed model')
            return data
        self.transform = change
        result = rhubarb.RhubarbLipSync().execute(self.inputs)
        self.assertIn('RHUBARB_RUNTIME_CHANGED', result.error)
        self.assertFalse((self.project / 'assets/cues.json').exists())

    def test_invalid_json_and_missing_output_are_reported(self):
        original = self.native
        def corrupted(command, **options):
            result = original(command, **options)
            if '--output' in command:
                Path(command[command.index('--output') + 1]).write_text('{broken')
            return result
        self.runner.side_effect = corrupted
        self.assertIn('RHUBARB_OUTPUT_INVALID', rhubarb.RhubarbLipSync().execute(self.inputs).error)
        def missing(command, **options):
            if '--version' in command:
                return original(command, **options)
            return subprocess.CompletedProcess(command, 0)
        self.runner.side_effect = missing
        self.assertIn('RHUBARB_OUTPUT_INVALID', rhubarb.RhubarbLipSync().execute(self.inputs).error)

    def test_bad_dialog_and_missing_probe_prevent_native_analysis(self):
        dialog = self.project / 'invalid.txt'
        dialog.write_bytes(b'\xff\xff')
        result = rhubarb.RhubarbLipSync().execute({**self.inputs, 'dialog_path': 'invalid.txt'})
        self.assertIn('RHUBARB_INPUT_INVALID', result.error)
        self.assertTrue(all(command[1:] == ['--version'] for command in self.commands))
        self.probe.return_value.get_status.return_value = ToolStatus.UNAVAILABLE
        self.assertIn('RHUBARB_FFPROBE_MISSING', rhubarb.RhubarbLipSync().execute(self.inputs).error)
