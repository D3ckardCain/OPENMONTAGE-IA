"""Transform declared TVCalib parameter features without camera fitting or images."""
from lib.isolated_library_operation import IsolatedLibraryOperation


class TvcalibParameters(IsolatedLibraryOperation):
    name = 'tvcalib_parameters'
    library = 'tvcalib'
    capability = 'camera_parameter_analysis'
    provider = 'tvcalib'
    input_schema = {'type':'object','additionalProperties':False,
                    'required':['project_id','loc','scale','values','mode','feature_name','feature_unit'],'properties':{
                        'project_id':{'type':'string','minLength':1},
                        'loc':{'type':'number','minimum':-1e9,'maximum':1e9},
                        'scale':{'type':'number','minimum':1e-9,'maximum':1e9},
                        'values':{'type':'array','minItems':1,'maxItems':1000,'items':{'type':'number','minimum':-1e9,'maximum':1e9}},
                        'mode':{'enum':['normalize','denormalize']},
                        'feature_name':{'type':'string','minLength':1,'maxLength':80},
                        'feature_unit':{'type':'string','minLength':1,'maxLength':80}}}
