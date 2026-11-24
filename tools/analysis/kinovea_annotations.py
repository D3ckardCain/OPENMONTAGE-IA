"""Read existing project annotations; no video analysis or app process."""
from jsonschema import validate, ValidationError
from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability


class KinoveaAnnotations(BaseTool):
    name = 'kinovea_annotations'
    capability = 'local_application_inspection'
    provider = 'kinovea_kva'
    tier = ToolTier.ANALYZE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    input_schema = {'type': 'object', 'additionalProperties': False,
                    'required': ['project_id', 'input_path'], 'properties': {
                        'project_id': {'type': 'string', 'minLength': 1},
                        'input_path': {'type': 'string', 'minLength': 1}}}

    def execute(self, inputs):
        try:
            validate(inputs, self.input_schema)
            from lib.kinovea_annotations import inspect
            return ToolResult(success=True, data=inspect(**inputs), cost_usd=0)
        except (OSError, ValueError, ValidationError) as exc:
            return ToolResult(success=False, error=str(exc)[:500], cost_usd=0)
