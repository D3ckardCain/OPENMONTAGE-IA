"""One discoverable, concrete provider per downloaded model family."""
from tools.base_tool import ToolRuntime
from lib.model_adapters import CATALOG, LocalModelAdapter, spec

for _family in CATALOG:
    _name='model_'+_family.replace('-','_')
    globals()[_name]=type(_name,(LocalModelAdapter,),{'__module__':__name__,'name':_name,'family':_family,
        'runtime':ToolRuntime.LOCAL if spec(_family)['backend']=='native' else ToolRuntime.LOCAL_GPU,'agent_skills':['comfyui'] if spec(_family)['backend']=='comfyui' else [],'capability':spec(_family)['capability'],'capabilities':[spec(_family)['capability']]})
