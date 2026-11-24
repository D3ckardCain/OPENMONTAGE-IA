"""Read-only connections between registered applications, Studio and local agents."""
from jsonschema import validate, ValidationError
from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability


class LocalApplicationInventory(BaseTool):
    name = 'local_application_inventory'
    capability = 'local_application_inspection'
    provider = 'studio'
    tier = ToolTier.ANALYZE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    input_schema = {'type': 'object', 'properties': {}, 'additionalProperties': False}

    def execute(self, inputs):
        try:
            validate(inputs, self.input_schema)
            from lib.external_applications import catalog
            fields = ('id', 'label', 'mode', 'configured', 'file_found', 'extensions', 'automation_tools', 'inspection_tools', 'numeric_tools', 'integration')
            return ToolResult(success=True, data={'applications': [
                {key: row[key] for key in fields if key in row} for row in catalog()],
                'scope': 'registration_and_file_presence_only', 'applications_launched': False,
                'automation_verified': False}, cost_usd=0)
        except (OSError, ValueError, ValidationError) as exc:
            return ToolResult(success=False, error='APPLICATION_INVENTORY_INVALID: ' + str(exc)[:300], cost_usd=0)


class KritaDocumentInspect(BaseTool):
    name = 'krita_document_inspect'
    capability = 'local_application_inspection'
    provider = 'krita_archive'
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
            from lib.krita_document import inspect
            return ToolResult(success=True, data=inspect(**inputs), cost_usd=0)
        except (OSError, ValueError, ValidationError) as exc:
            return ToolResult(success=False, error=str(exc)[:500], cost_usd=0)
