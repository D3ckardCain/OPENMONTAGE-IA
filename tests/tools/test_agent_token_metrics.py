"""Actual usage fields from synthetic Ollama replies; no model or network call."""
import threading
import unittest
from unittest.mock import patch

from lib.production_agent import LocalAgent
from lib import production_studio as studio


class OllamaUsageTests(unittest.TestCase):
    def agent(self):
        value = object.__new__(LocalAgent)
        value.cancel = threading.Event()
        value._chat = None
        value.config = {'model': 'fixture-model', 'ollama_url': 'http://127.0.0.1:11434'}
        value.last_transport = {}
        return value

    def test_server_token_counts_and_durations_are_kept_in_transport(self):
        value = self.agent()
        response = {'message': {'role': 'assistant', 'content': 'synthetic'},
                    'prompt_eval_count': 321, 'eval_count': 17,
                    'total_duration': 800000, 'load_duration': 100000,
                    'prompt_eval_duration': 400000, 'eval_duration': 300000}
        with patch.object(studio, 'local_request', return_value=response):
            message = value.chat([{'role': 'user', 'content': 'fixture'}])
        self.assertEqual(message, response['message'])
        self.assertEqual(value.last_transport['ollama_usage'], {k: response[k] for k in (
            'prompt_eval_count', 'eval_count', 'total_duration', 'load_duration',
            'prompt_eval_duration', 'eval_duration')})

    def test_missing_or_invalid_usage_is_not_guessed(self):
        value = self.agent()
        response = {'message': {'role': 'assistant', 'content': 'synthetic'},
                    'prompt_eval_count': True, 'eval_count': -1,
                    'eval_duration': 'unknown'}
        with patch.object(studio, 'local_request', return_value=response):
            value.chat([{'role': 'user', 'content': 'fixture'}])
        self.assertNotIn('ollama_usage', value.last_transport)


if __name__ == '__main__':
    unittest.main()
