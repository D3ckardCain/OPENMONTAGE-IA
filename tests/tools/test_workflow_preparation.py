"""Compiler/transport contracts only; no models, GUIs or inference servers."""
from copy import deepcopy
from pathlib import Path
import pytest
from lib.comfy_workflow_compile import compile_canvas,widget_values
from lib import production_studio as studio
from lib import workflow_preparation as prep
from lib import model_adapters as adapters
from lib.model_comfy_adapter import graph_config,validate_graph
from lib.original_model_engines import patch_assignments


def info():
    return {'Generator':{'input':{'required':{'text':['STRING'],'seed':['INT']}},'output':['IMAGE']},
            'SaveImage':{'input':{'required':{'images':['IMAGE'],'filename_prefix':['STRING']}},'output_node':True,'output':[]}}


def canvas():
    return {'nodes':[{'id':1,'type':'Generator','inputs':[],'widgets_values':['original',4]},
            {'id':2,'type':'SaveImage','inputs':[{'name':'images','type':'IMAGE','link':1}],'widgets_values':['fixture']},
            {'id':99,'type':'UninstalledAlternative','mode':0,'widgets_values':['unused']}],
            'links':[[1,1,0,2,0,'IMAGE']]}


def test_compiler_prunes_unrelated_branch_and_keeps_literal_inputs():
    source=canvas();graph,output=compile_canvas(source,info(),'2')
    assert set(graph)=={'1','2'} and output=='2'
    assert graph['1']['inputs']=={'text':'original','seed':4}
    assert graph['2']['inputs']['images']==['1',0]
    assert source==canvas()


def test_subgraph_instances_keep_separate_exposed_values_and_ids():
    graph=canvas();graph['nodes']=graph['nodes'][:2]
    graph['nodes'][0]['inputs']=[{'name':'text','link':8}]
    graph['links'].append({'id':8,'origin_id':-10,'origin_slot':0,'target_id':1,'target_slot':0,'type':'STRING'})
    graph.update(id='sub',inputNode={'id':-10},outputs=[{'linkIds':[1]}],inputs=[{'name':'text','type':'STRING','linkIds':[8]}])
    outer={'nodes':[{'id':10,'type':'sub','inputs':[],'widgets_values':['first']},
                    {'id':20,'type':'sub','inputs':[],'widgets_values_named':{'text':'second'}},
                    {'id':30,'type':'SaveImage','inputs':[{'name':'images','link':2}],'widgets_values':['out']}],
           'links':[[2,20,0,30,0,'IMAGE']],'definitions':{'subgraphs':[graph]}}
    result,_=compile_canvas(outer,info(),'30')
    assert result['20:1']['inputs']['text']=='second'
    assert not any(key.startswith('10:') for key in result)


@pytest.mark.parametrize('kind,raw,expected',[
 ('Generator',['test',5,'randomize'],{'text':'test','seed':5}),
 ('Generator',{'text':'test','seed':5,'preview':'not an API input'},{'text':'test','seed':5})])
def test_frontend_widgets_are_not_submitted_as_backend_inputs(kind,raw,expected):
    assert widget_values({'id':1,'type':kind,'widgets_values':raw},info()[kind])==expected


def test_ambiguous_widgets_and_external_service_nodes_fail_before_submission():
    source=canvas();source['nodes'][0]['widgets_values'].append('unknown extra')
    with pytest.raises(ValueError,match='Widgets ambiguos'):compile_canvas(source,info(),'2')
    metadata=info();metadata['Generator']['api_node']=True
    with pytest.raises(ValueError,match='externo'):compile_canvas(canvas(),metadata,'2')


def test_disabled_dependency_and_cycle_fail_explicitly():
    source=canvas();source['nodes'][0]['mode']=2
    with pytest.raises(ValueError,match='desactivado'):compile_canvas(source,info(),'2')
    source=canvas();source['nodes'][0]['inputs']=[{'name':'text','link':2}]
    source['links'].append([2,1,0,1,0,'STRING'])
    with pytest.raises(ValueError,match='Ciclo'):compile_canvas(source,info(),'2')


def test_constant_switch_does_not_require_unselected_models():
    source=canvas();source['nodes'][1]['inputs'][0]['link']=3
    source['nodes'].append({'id':3,'type':'ComfySwitchNode','widgets_values_named':{'switch':False},
        'inputs':[{'name':'on_false','link':1},{'name':'on_true','link':2}]})
    source['links']=[[1,1,0,3,0,'IMAGE'],[2,99,0,3,1,'IMAGE'],[3,3,0,2,0,'IMAGE']]
    metadata=info();metadata['ComfySwitchNode']={'input':{'required':{'switch':['BOOLEAN']}}}
    graph,_=compile_canvas(source,metadata,'2')
    assert set(graph)=={'1','2'}
    assert graph['2']['inputs']['images']==['1',0]


def test_all_catalogued_families_have_implemented_workflow_recipes():
    rows=prep.recipes()
    assert {r['family'] for r in rows}==set(adapters.CATALOG)
    assert sum(r['engine']=='native' for r in rows)==32
    assert all(r['preparation_implemented'] for r in rows)
    assert all(r['required_inputs'] and not r['inference_verified'] for r in rows)
    assert all((prep.TEMPLATES/r['reference']['file']).is_file() for r in rows if r['recipe_kind']=='canvas_compiler')


def test_semantic_parameters_are_applied_and_unsupported_parameters_are_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    path=tmp_path/'graph.json';g={'1':{'class_type':'Generator','inputs':{'text':'old','seed':1}},'2':{'class_type':'SaveImage','inputs':{'images':['1',0]}}}
    studio.save_json(path,g)
    adapters.configure('mochi',{'workflow_path':str(path),'output_node':'2','parameter_bindings':{'text':[{'node':'1','field':'text'}]}})
    patched,_=graph_config('mochi',{'text':'New original script'})
    assert patched['1']['inputs']['text']=='New original script'
    assert studio.read_json(path)['1']['inputs']['text']=='old'
    with pytest.raises(ValueError,match='no expone'):graph_config('mochi',{'width':832})


def test_preparation_reads_schemas_and_never_submits_a_prompt(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    weight=next(e['path'].rsplit('/',1)[-1] for e in adapters.CATALOG['mochi']['entries'] if 'diffusion_models/' in e['path'])
    g={'6':{'class_type':'Generator','inputs':{'text':'example','seed':4,'model_name':weight}},
       '42':{'class_type':'SaveImage','inputs':{'images':['6',0],'filename_prefix':'fixture'}}}
    metadata=info();metadata['Generator']['input']['required']['model_name']=[[weight]]
    calls=[]
    def local_request(server,path,**kwargs):calls.append(path);assert path=='/object_info';return metadata
    monkeypatch.setattr(studio,'local_request',local_request)
    monkeypatch.setattr(prep,'compile_canvas',lambda *args:(deepcopy(g),'42'))
    result=prep.prepare('mochi',{})
    assert calls==['/object_info'] and result['generation_started'] is False
    assert result['parameter_bindings']['text']==[{'node':'6','field':'text'}]
    assert Path(adapters.configuration('mochi')['workflow_path']).is_file()


def test_original_script_patch_is_exact_and_does_not_execute_source():
    code=patch_assignments("model_name='remote'\nseed=42\nraise RuntimeError('must not run')",{'model_name':'/local/weights','seed':0},'fixture.py')
    assert code.co_filename=='fixture.py'
    with pytest.raises(ValueError,match='no expone'):patch_assignments('seed=1',{'output':'/local/project'},'fixture.py')
    with pytest.raises(ValueError,match='ambigua'):patch_assignments('seed=1\nseed=2',{'seed':3},'fixture.py')


def test_registered_application_tools_are_discoverable_without_launching():
    from tools.tool_registry import ToolRegistry
    registry=ToolRegistry();registry.discover('tools.desktop')
    assert registry.get('application_catalog')
    assert registry.get('application_open_project_file')
