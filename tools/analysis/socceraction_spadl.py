"""Functional SPADL validation using the existing Socceraction environment."""
from lib.isolated_library_operation import IsolatedLibraryOperation


class SocceractionSpadl(IsolatedLibraryOperation):
    name = 'socceraction_spadl_validate'
    library = 'socceraction'
    capability = 'sports_action_validation'
    provider = 'socceraction'
    input_schema = {'type': 'object', 'additionalProperties': False,
                    'required': ['project_id', 'coordinate_system', 'actions'], 'properties': {
                        'project_id': {'type': 'string', 'minLength': 1},
                        'coordinate_system': {'enum': ['spadl_105x68_bottom_left_home_to_right']},
                        'actions': {'type': 'array', 'minItems': 1, 'maxItems': 1000, 'items': {'type': 'object'}}}}
