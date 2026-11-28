"""Plan MuseTalk batching using small synthetic CPU placeholders only."""
from lib.isolated_library_operation import IsolatedLibraryOperation


class MusetalkBatchPlan(IsolatedLibraryOperation):
    name = 'musetalk_batch_plan'
    library = 'musetalk'
    capability = 'avatar_input_planning'
    provider = 'musetalk'
    input_schema = {'type':'object','additionalProperties':False,
                    'required':['project_id','audio_chunk_count','latent_frame_count','batch_size','delay_frame'], 'properties':{
                        'project_id':{'type':'string','minLength':1},
                        'audio_chunk_count':{'type':'integer','minimum':1,'maximum':32},
                        'latent_frame_count':{'type':'integer','minimum':1,'maximum':32},
                        'batch_size':{'type':'integer','minimum':1,'maximum':16},
                        'delay_frame':{'type':'integer','minimum':0,'maximum':1000}}}
