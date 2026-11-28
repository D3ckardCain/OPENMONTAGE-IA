"""Read user supplied, period-specific channel performance in bounded pages."""
from jsonschema import validate, ValidationError

from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability


class SavedChannelPerformance(BaseTool):
    name = 'saved_channel_performance'
    version = '0.1.0'
    provider = 'openmontage_local'
    tier = ToolTier.SOURCE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    capability = 'local_research_evidence'
    capabilities = ['local_research_evidence', 'youtube_channel_research']
    side_effects = []
    install_instructions = 'Importa un CSV propio en /channels y copia el ID de la importación.'
    input_schema = {'type': 'object', 'additionalProperties': False,
        'required': ['import_id'], 'properties': {
            'import_id': {'type': 'string', 'pattern': '^[0-9a-f]{32}$'},
            'offset': {'type': 'integer', 'minimum': 0},
            'limit': {'type': 'integer', 'minimum': 1, 'maximum': 50}}}

    def execute(self, inputs):
        from lib.channel_performance import read, summary
        try:
            validate(inputs, self.input_schema)
            record = read(inputs['import_id'])
            return ToolResult(success=True, cost_usd=0,
                data=summary(record, inputs.get('offset', 0), inputs.get('limit', 20)))
        except (ValidationError, ValueError, KeyError, TypeError, FileNotFoundError):
            return ToolResult(success=False, cost_usd=0,
                error='SAVED_CHANNEL_PERFORMANCE_INVALID: revisa ID, archivo e integridad')
