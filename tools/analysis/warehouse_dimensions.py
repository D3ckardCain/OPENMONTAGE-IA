"""Read numeric sizing helpers from cq_warehouse without building solids."""
from lib.isolated_library_operation import IsolatedLibraryOperation


class WarehouseDimensions(IsolatedLibraryOperation):
    name = 'warehouse_dimensions'
    library = 'cq_warehouse'
    capability = 'cad_parameter_analysis'
    provider = 'cq_warehouse'
    input_schema = {'type': 'object', 'additionalProperties': False,
                    'required': ['project_id', 'size', 'across_flats_mm', 'sides'], 'properties': {
                        'project_id': {'type': 'string', 'minLength': 1},
                        'size': {'type': 'string', 'minLength': 3, 'maxLength': 30},
                        'across_flats_mm': {'type': 'number', 'exclusiveMinimum': 0, 'maximum': 10000},
                        'sides': {'type': 'integer', 'minimum': 3, 'maximum': 24}}}
