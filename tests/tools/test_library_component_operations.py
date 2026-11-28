"""Component operations use prepared runtimes, synthetic values and shared transport."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import Mock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backlot.studio_routes import create_studio_router
from lib import production_studio as studio, isolated_library_operation as transport
from lib.production_agent import LocalAgent
from lib.pipeline_loader import load_pipeline_readonly
from tools.analysis import warehouse_dimensions
from tools.analysis import soccervision_homography
from tools.analysis import musetalk_batch_plan
from tools.analysis import tvcalib_parameters
from tools.tool_registry import ToolRegistry

CASES = [(warehouse_dimensions, 'WarehouseDimensions', {'project_id':'fixture','size':'#8-32','across_flats_mm':10,'sides':6}, '/api/studio/libraries/cq_warehouse/dimensions')]
CASES += [(soccervision_homography,'SoccervisionHomography',{'project_id':'fixture','matrix':[[2,0,10],[0,3,20],[0,0,1]],'points':[[0,0],[3,4]],'source_units':'pixels','target_units':'metres'},'/api/studio/libraries/soccervision/homography')]
CASES += [(musetalk_batch_plan,'MusetalkBatchPlan',{'project_id':'fixture','audio_chunk_count':5,'latent_frame_count':2,'batch_size':2,'delay_frame':1},'/api/studio/libraries/musetalk/batch-plan')]
CASES += [(tvcalib_parameters,'TvcalibParameters',{'project_id':'fixture','loc':10,'scale':2,'values':[8,10,12],'mode':'normalize','feature_name':'synthetic_feature','feature_unit':'declared'},'/api/studio/libraries/tvcalib/parameters')]


@pytest.mark.parametrize('module,clsname,inputs,route', CASES)
def test_component_api_and_real_agent_bridge(module,clsname,inputs,route,tmp_path,monkeypatch):
    cls=getattr(module,clsname)
    monkeypatch.setattr(studio,'project_path',lambda pid:tmp_path)
    output=transport.ToolResult(success=True,data={'fixture':True},cost_usd=0)
    app=FastAPI();app.include_router(create_studio_router())
    with patch.object(cls,'execute',return_value=output),TestClient(app) as client:
        response=client.post(route,json=inputs)
        assert response.status_code==200,response.text
        assert client.post(route,json=inputs,headers={'Origin':'https://remote.example'}).status_code==403
    registry=ToolRegistry();registry.register_module(module)
    agent=LocalAgent.__new__(LocalAgent);agent.pid='fixture';agent.path=tmp_path;agent.registry=registry
    agent.request={'pipeline':'animation'};agent.manifest=load_pipeline_readonly('animation')
    agent.reads={'skills/'+agent.manifest['stages'][0]['skill']+'.md'};agent.event=Mock()
    with patch.object(cls,'execute',return_value=output),patch.object(cls,'get_status',return_value=transport.ToolStatus.AVAILABLE):
        assert agent.dispatch('execute_tool',{'name':cls.name,'inputs':inputs})['success']
        with pytest.raises(ValueError,match='otro proyecto'):
            agent.dispatch('execute_tool',{'name':cls.name,'inputs':{**inputs,'project_id':'outside'}})


@pytest.mark.parametrize('module,clsname,inputs,route', CASES)
def test_component_transport_and_error_contract(module,clsname,inputs,route,tmp_path,monkeypatch):
    cls=getattr(module,clsname);tool=cls()
    monkeypatch.setattr(studio,'project_path',lambda pid:tmp_path)
    monkeypatch.setattr(transport,'RUNTIME_ROOT',tmp_path)
    assert 'LIBRARY_RUNTIME_MISSING' in tool.execute(inputs).error
    python=tool.python();python.parent.mkdir(parents=True);python.touch()
    process=subprocess.CompletedProcess('worker',0,b'{"fixture":true}',b'')
    with patch.object(transport.subprocess,'run',return_value=process) as run:
        before=dict(os.environ);r=tool.execute(inputs)
        assert r.success,r.error
        assert dict(os.environ)==before
        assert run.call_args.args[0][1:3]==['-I','-B']
        assert run.call_args.args[0][-2:]==[tool.library,'--operate']
        assert run.call_args.kwargs['env']['HF_HUB_OFFLINE']=='1'
        assert run.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES']==''
        assert not tool.execute({**inputs,'script':'arbitrary'}).success
    with patch.object(transport.subprocess,'run',side_effect=subprocess.TimeoutExpired('worker',60)):
        assert 'LIBRARY_TIMEOUT' in tool.execute(inputs).error
    with patch.object(transport.subprocess,'run',return_value=subprocess.CompletedProcess('worker',1,b'not-json',b'')):
        assert 'LIBRARY_OUTPUT_INVALID' in tool.execute(inputs).error


@pytest.mark.parametrize('module,clsname,inputs,route', CASES)
def test_native_component_operation(module,clsname,inputs,route,tmp_path,monkeypatch):
    tool=getattr(module,clsname)()
    if not tool.python().is_file():pytest.skip('optional prepared isolated runtime')
    monkeypatch.setattr(studio,'project_path',lambda pid:tmp_path)
    registry=ToolRegistry();registry.register_module(module)
    agent=LocalAgent.__new__(LocalAgent);agent.pid='fixture';agent.path=tmp_path;agent.registry=registry
    agent.request={'pipeline':'animation'};agent.manifest=load_pipeline_readonly('animation')
    agent.reads={'skills/'+agent.manifest['stages'][0]['skill']+'.md'};agent.event=Mock()
    actual=agent.dispatch('execute_tool',{'name':tool.name,'inputs':inputs})
    assert actual['success'],actual['error']
    from types import SimpleNamespace
    r=SimpleNamespace(success=actual['success'],data=actual['data'],error=actual['error'])
    assert not r.data['geometry_generated']
    assert not r.data['model_inference_performed']
    assert not r.data['provenance']['network_accessed']
    assert len(r.data['provenance']['input_sha256'])==64
    if tool.library=='cq_warehouse':
        assert r.data['major_diameter_mm']==pytest.approx(4.1656)
        assert r.data['pitch_mm']==pytest.approx(0.79375)
        assert r.data['polygon_diagonal_mm']==pytest.approx(11.547005383792515)
        assert not tool.execute({**inputs,'size':"__import__('os')-32"}).success
    elif tool.library=='soccervision':
        assert r.data['points']==[[10,20],[16,32]]
        assert r.data['roundtrip_max_error_in_source_units']<1e-10
        assert not tool.execute({**inputs,'matrix':[[0,0,0],[0,0,0],[0,0,0]]}).success
        assert not tool.execute({**inputs,'matrix':[[1,0,0],[0,1,0],[1,0,1]],'points':[[-1,0]]}).success
    elif tool.library=='musetalk':
        assert [b['chunk_indices'] for b in r.data['batches']]==[[0,1],[2,3],[4]]
        assert [b['latent_indices'] for b in r.data['batches']]==[[1,0],[1,0],[1]]
        assert r.data['batches'][-1]['latent_shape']==[1,4,2,2]
        assert not r.data['weights_loaded'] and not r.data['avatar_generated']
        assert not tool.execute({**inputs,'latent_frame_count':0}).success
    elif tool.library=='tvcalib':
        assert r.data['values']==[-1,0,1]
        inverse=tool.execute({**inputs,'values':r.data['values'],'mode':'denormalize'})
        assert inverse.success,inverse.error
        assert inverse.data['values']==[8,10,12]
        assert r.data['roundtrip_max_error_in_input_units']<1e-12
        assert not r.data['camera_calibration_performed']
        assert not tool.execute({**inputs,'scale':0}).success
