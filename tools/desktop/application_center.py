"""Local application handoff tools exposed to the production agent registry."""
from tools.base_tool import BaseTool,ToolResult,ToolRuntime,ToolTier,ToolStatus,Determinism,ResourceProfile
from lib import external_applications as applications


class ApplicationCatalog(BaseTool):
    name='application_catalog'
    capability='local_application_discovery'
    provider='local_application_center'
    runtime=ToolRuntime.LOCAL
    tier=ToolTier.CORE
    determinism=Determinism.DETERMINISTIC
    resource_profile=ResourceProfile(network_required=False)
    input_schema={'type':'object','properties':{},'additionalProperties':False}
    def get_status(self):return ToolStatus.AVAILABLE
    def estimate_cost(self,inputs):return 0.0
    def execute(self,inputs):
        if inputs:return ToolResult(success=False,error='No se admiten argumentos')
        return ToolResult(success=True,data={'applications':applications.catalog(),'cost_usd':0})


class ApplicationOpenProjectFile(BaseTool):
    name='application_open_project_file'
    capability='local_application_handoff'
    provider='local_application_center'
    runtime=ToolRuntime.LOCAL
    tier=ToolTier.CORE
    determinism=Determinism.STOCHASTIC
    resource_profile=ResourceProfile(network_required=False)
    side_effects=['opens a configured local desktop application with an existing project file']
    user_visible_verification=['The application opening is not an exported or completed production artifact.']
    input_schema={'type':'object','additionalProperties':False,'required':['application','project_id','file'],
        'properties':{'application':{'enum':[key for key,row in applications.CATALOG.items() if row['mode']=='desktop']},
                      'project_id':{'type':'string'},'file':{'type':'string','minLength':1}}}
    def get_status(self):return ToolStatus.AVAILABLE if any(a['file_found'] and a['mode']=='desktop' for a in applications.catalog()) else ToolStatus.UNAVAILABLE
    def estimate_cost(self,inputs):return 0.0
    def execute(self,inputs):
        from jsonschema import validate
        try:
            validate(inputs,self.input_schema)
            result=applications.launch(inputs['application'],inputs['project_id'],inputs['file'])
            return ToolResult(success=True,data={**result,'production_completed':False,'cost_usd':0})
        except Exception as exc:return ToolResult(success=False,error=str(exc)[:1500])
