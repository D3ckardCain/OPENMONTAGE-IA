"""Synthetic container fixtures only; no 3D resource/pilot generation or Blender launch."""
import json
import struct
from unittest.mock import patch
import pytest
from lib.glb_inspection import inspect
from tools.graphics.blender_world import BlenderWorld


def fixture(tmp_path,document):
    raw=json.dumps(document).encode();raw+=b' '*((-len(raw))%4)
    data=struct.pack('<4sII',b'glTF',2,20+len(raw))+struct.pack('<II',len(raw),0x4e4f534a)+raw
    p=tmp_path/'fixture.glb';p.write_bytes(data);return p


def test_node_material_and_external_resource_metadata_only(tmp_path):
    p=fixture(tmp_path,{'asset':{'version':'2.0'},'nodes':[{'scale':[1,2,-1]}],
        'materials':[{'name':'Own fixture','pbrMetallicRoughness':{'metallicFactor':0,'roughnessFactor':.5}}],
        'images':[{'uri':'https://example.invalid/texture.png'}]})
    with patch('subprocess.Popen') as spawn:
        r=BlenderWorld().execute({'operation':'inspect_glb','asset_path':str(p)})
    assert r.success and r.data['nodes'][0]['non_uniform_scale']
    assert r.data['nodes'][0]['negative_or_zero_scale']
    assert r.data['external_resources_not_read']==1 and not r.data['import_validated']
    assert not r.data['mesh_payload_decoded'] and not r.data['blender_started'];spawn.assert_not_called()


@pytest.mark.parametrize('case',['cycle','nan','matrix_trs','child_index','header_length'])
def test_invalid_container_or_transform_rejected(tmp_path,case):
    data={'asset':{'version':'2.0'},'nodes':[{}]}
    if case=='cycle':data['nodes'][0]['children']=[0]
    if case=='nan':data['nodes'][0]['scale']=[1,float('nan'),1]
    if case=='matrix_trs':data['nodes'][0].update(matrix=[0]*16,translation=[0]*3)
    if case=='child_index':data['nodes'][0]['children']=[2]
    p=fixture(tmp_path,data)
    if case=='header_length':p.write_bytes(p.read_bytes()+b'extra')
    with pytest.raises(ValueError):inspect(p)


@pytest.mark.parametrize("document", [{"nodes":[None]}, {"materials":[None]}, {"materials":[{"pbrMetallicRoughness":{"roughnessFactor":float("nan")}}]}])
def test_malformed_node_or_pbr_reports_value_error(tmp_path,document):
    p=fixture(tmp_path,{"asset":{"version":"2.0"},**document})
    with pytest.raises(ValueError):inspect(p)
