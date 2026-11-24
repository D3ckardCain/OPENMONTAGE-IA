"""Apply a declared homography without images, detector models or tracking."""
from lib.isolated_library_operation import IsolatedLibraryOperation

PAIR = {'type':'array','minItems':2,'maxItems':2,'items':{'type':'number'}}


class SoccervisionHomography(IsolatedLibraryOperation):
    name = 'soccervision_homography'
    library = 'soccervision'
    capability = 'sports_coordinate_analysis'
    provider = 'soccervision'
    input_schema = {'type':'object','additionalProperties':False,
                    'required':['project_id','matrix','points','source_units','target_units'], 'properties':{
                        'project_id':{'type':'string','minLength':1},
                        'matrix':{'type':'array','minItems':3,'maxItems':3,'items':{'type':'array','minItems':3,'maxItems':3,'items':{'type':'number'}}},
                        'points':{'type':'array','minItems':1,'maxItems':1000,'items':PAIR},
                        'source_units':{'enum':['pixels','metres','normalized','declared']},
                        'target_units':{'enum':['pixels','metres','normalized','declared']}}}
