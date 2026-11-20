"""Registry entry for the public, undocumented FIFA website feeds."""
from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability, ResourceProfile
from tools.football.fifa_live import FIFA


class OfficialFIFA(BaseTool):
    name = 'official_fifa_live'
    version = '0.2.0'
    provider = 'fifa_official'
    tier = ToolTier.SOURCE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.EXPERIMENTAL
    capability = 'football_statistics'
    capabilities = ['football_statistics', 'official_live_data']
    idempotency_key_fields = []
    side_effects = ['read_public_fifa_web_services']
    fallback = None
    fallback_tools = []
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=0, network_required=True)
    dependencies = []
    install_instructions = 'Python local y HTTPS a FIFA. Sin API de pago. Servicio no documentado, cobertura por edición.'
    supports = {'offline': False, 'persistent_cache': False, 'name_resolution': True}
    input_schema = {'type': 'object', 'additionalProperties': False, 'required': ['action', 'competition_id'], 'properties': {
        'action': {'enum': ['seasons', 'teams', 'squad', 'resolve_players', 'compare_players', 'player_statistics']},
        'competition_id': {'type': 'string', 'pattern': '^[0-9]{1,12}$'},
        'season_id': {'type': 'string', 'pattern': '^[0-9]{1,12}$'},
        'team_id': {'type': 'string', 'pattern': '^[0-9]{1,12}$'},
        'subjects': {'type': 'array', 'minItems': 1, 'maxItems': 10, 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['name'], 'properties': {
                'name': {'type': 'string', 'minLength': 1, 'maxLength': 150},
                'team_name': {'type': 'string', 'minLength': 1, 'maxLength': 150}}}},
        'player_ids': {'type': 'array', 'minItems': 1, 'maxItems': 10, 'uniqueItems': True,
                       'items': {'type': 'string', 'pattern': '^[0-9]{1,12}$'}},
        'metrics': {'type': 'array', 'minItems': 1, 'maxItems': 30, 'uniqueItems': True,
                    'items': {'type': 'string', 'pattern': '^[A-Za-z][A-Za-z0-9]{0,99}$'}}}}

    def __init__(self):
        self.client = FIFA()

    def execute(self, inputs):
        from jsonschema import validate
        try:
            validate(inputs, self.input_schema)
            action = inputs['action']
            allowed = {'seasons': {'competition_id'}, 'teams': {'competition_id', 'season_id'},
                       'squad': {'competition_id', 'season_id', 'team_id'},
                       'resolve_players': {'competition_id', 'season_id', 'subjects'},
                       'compare_players': {'competition_id', 'season_id', 'subjects', 'metrics'},
                       'player_statistics': {'competition_id', 'season_id', 'player_ids', 'metrics'}}[action]
            if set(inputs) - allowed - {'action'}:
                raise ValueError('Parámetros no aplicables a esta consulta')
            result = getattr(self.client, action)(**{k: v for k, v in inputs.items() if k != 'action'})
            return ToolResult(success=True, data=result, artifacts=[], cost_usd=0, from_cache=False)
        except Exception as exc:
            return ToolResult(success=False, error='FIFA_QUERY_REJECTED: ' + str(exc),
                              data={'fresh_query_failed': True, 'stale_fallback': False}, cost_usd=0, from_cache=False)
