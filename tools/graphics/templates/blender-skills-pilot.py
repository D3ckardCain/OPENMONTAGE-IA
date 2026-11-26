"""Own-resource scene authored for #117; no remote script/assets or user scene."""
import argparse
import importlib.util
import hashlib
import json
import math
import sys
from pathlib import Path
import bmesh
import bpy
from mathutils import Matrix,Vector


def write(root,name,data):
    (root/'artifacts'/name).write_text(json.dumps(data,indent=2),encoding='utf-8')


def adapter():
    path=Path(__file__).with_name('blender-world-runtime.py')
    spec=importlib.util.spec_from_file_location('openmontage_world_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def material(name,color,metal,roughness):
    mat=bpy.data.materials.new(name)
    bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value=(*color,1)
    bsdf.inputs['Metallic'].default_value=metal
    tex=mat.node_tree.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=6
    coordinates=mat.node_tree.nodes.new('ShaderNodeTexCoord')
    ramp=mat.node_tree.nodes.new('ShaderNodeMapRange')
    ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1
    ramp.inputs['To Min'].default_value=roughness[0];ramp.inputs['To Max'].default_value=roughness[1]
    mat.node_tree.links.new(coordinates.outputs['Generated'],tex.inputs['Vector'])
    mat.node_tree.links.new(tex.outputs['Fac'],ramp.inputs['Value'])
    mat.node_tree.links.new(ramp.outputs['Result'],bsdf.inputs['Roughness'])
    return mat


def mesh_object(name,bm,collection,mat):
    mesh=bpy.data.meshes.new(name+'_Mesh');bm.to_mesh(mesh);bm.free()
    obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj);mesh.materials.append(mat)
    return obj


def orient(obj,point):
    obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()


def mesh_qa(obj):
    graph=bpy.context.evaluated_depsgraph_get();evaluated=obj.evaluated_get(graph);mesh=evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles();bm=bmesh.new();bm.from_mesh(mesh)
        result={'object':obj.name,'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),
                'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_nonboundary':sum(not e.is_manifold and not e.is_boundary for e in bm.edges),
                'degenerate_faces':sum(f.calc_area()<1e-10 for f in bm.faces),
                'volume':bm.calc_volume(signed=True),'materials':len(mesh.materials),
                'scale':list(obj.scale),'dimensions':list(obj.dimensions),
                'min_world_z':min((obj.matrix_world@v.co).z for v in mesh.vertices),
                'finite':all(math.isfinite(c) for v in mesh.vertices for c in v.co)}
        bm.free()
        assert result['finite'] and result['nonmanifold_nonboundary']==0 and result['degenerate_faces']==0
        assert all(abs(s-1)<1e-6 for s in result['scale']) and result['materials']==1
        if obj.name!='SM_PilotFloor':assert result['boundary_edges']==0 and result['volume']>0 and abs(result['min_world_z'])<1e-5
        return result
    finally:evaluated.to_mesh_clear()


def inventory():
    scene=bpy.context.scene
    return {'version':bpy.app.version_string,'engine':scene.render.engine,'fps':scene.render.fps,
            'frame_range':[scene.frame_start,scene.frame_end],'resolution':[scene.render.resolution_x,scene.render.resolution_y],
            'objects':len(scene.objects),'meshes':len(bpy.data.meshes),'materials':len(bpy.data.materials),'actions':len(bpy.data.actions),
            'lights':[{'name':o.name,'type':o.data.type,'watts':o.data.energy} for o in scene.objects if o.type=='LIGHT'],
            'mesh_qa':[mesh_qa(o) for o in scene.objects if o.type=='MESH'],
            'external_images':[i.filepath for i in bpy.data.images if i.source=='FILE'],
            'accepted_limits':['Floor is intentionally open with four boundary edges','Procedural materials intentionally need no UV maps','Render-oriented pilot, not a game/print asset or28skills certification']}


def build(root):
    scene=bpy.context.scene
    for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
    for group in (bpy.data.meshes,bpy.data.materials,bpy.data.cameras,bpy.data.lights,bpy.data.actions):
        for block in list(group):
            if block.users==0:group.remove(block)
    for col in list(bpy.data.collections):bpy.data.collections.remove(col)
    assets=bpy.data.collections.new('PILOT_ASSETS');rig=bpy.data.collections.new('PILOT_RIG')
    scene.collection.children.link(assets);scene.collection.children.link(rig)
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    scene.render.resolution_x=640;scene.render.resolution_y=360;scene.render.resolution_percentage=100
    scene.render.fps=24;scene.frame_start=1;scene.frame_end=72
    adapter().configure_engine(scene,16)
    scene.view_settings.view_transform='AgX'
    scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.film_transparent=False
    red=material('M_PilotPaint',(0.42,0.055,0.018),0,(0.28,0.42))
    silver=material('M_PilotMetal',(0.65,0.70,0.75),1,(0.16,0.26))
    ground=material('M_PilotFloor',(0.075,0.095,0.13),0,(0.50,0.62))
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=2);bmesh.ops.transform(bm,matrix=Matrix.Translation((0,0,1)),verts=list(bm.verts))
    cube=mesh_object('SM_PilotCube',bm,assets,red)
    bevel=cube.modifiers.new('PilotBevel','BEVEL');bevel.width=.10;bevel.segments=3
    bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=32,v_segments=16,radius=.7)
    bmesh.ops.transform(bm,matrix=Matrix.Translation((0,0,.7)),verts=list(bm.verts))
    sphere=mesh_object('SM_PilotSphere',bm,assets,silver);sphere.location.x=2.2
    for polygon in sphere.data.polygons:polygon.use_smooth=True
    bm=bmesh.new();verts=[bm.verts.new(v) for v in [(-12,-12,0),(12,-12,0),(12,12,0),(-12,12,0)]];bm.faces.new(verts)
    mesh_object('SM_PilotFloor',bm,assets,ground)
    for frame,angle in [(1,0),(8,0),(36,.8),(64,1.8),(72,1.8)]:
        cube.rotation_euler.z=angle;cube.keyframe_insert(data_path='rotation_euler',frame=frame)
    cube.animation_data.action.name='SM_PilotCube_Rotate'
    curves=list(adapter().action_curves(cube));assert len(curves)==3
    for curve in curves:
        for key in curve.keyframe_points:key.interpolation='BEZIER';key.handle_left_type='AUTO_CLAMPED';key.handle_right_type='AUTO_CLAMPED'
    camera_data=bpy.data.cameras.new('CAM_Pilot');camera=bpy.data.objects.new('CAM_Pilot',camera_data);rig.objects.link(camera)
    camera.location=(7,-10,6);camera_data.lens=50;orient(camera,(.7,0,.85));scene.camera=camera
    for name,position,energy,size in [('Key',(-3,-4,6),900,4),('Fill',(4,-2,3),300,3),('Rim',(1,4,5),1100,3)]:
        data=bpy.data.lights.new('L_Pilot'+name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
        obj=bpy.data.objects.new(data.name,data);rig.objects.link(obj);obj.location=position;orient(obj,(.5,0,1))
    world=scene.world or bpy.data.worlds.new('W_Pilot');scene.world=world
    background=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
    background.inputs['Color'].default_value=(.11,.13,.17,1);background.inputs['Strength'].default_value=.35
    scene.frame_set(1);bpy.context.view_layer.update()
    report=inventory();report.update(contract='blender-skills-pilot-v1',source='Own procedural geometry/materials, no remote assets',skills_revision='1a1cc6c49312f9f370aae86f52b7b907f29c94f6',animation_curves=len(curves))
    assert not report['external_images'] and len(scene.collection.objects)==0
    folder=root/'assets/scene';folder.mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/'pilot.blend'))
    write(root,'pilot-build.json',report)


def render(root):
    frames=root/'assets/video/frames';frames.mkdir(exist_ok=True)
    scene=bpy.context.scene;scene.render.filepath=str(frames/'frame_');scene.render.use_file_extension=True;scene.render.use_overwrite=False
    assert (scene.frame_start,scene.frame_end,scene.render.fps)==(1,72,24)
    bpy.ops.render.render(animation=True)
    write(root,'pilot-render.json',{'contract':'blender-skills-pilot-v1','frames':72,'engine':scene.render.engine,'version':bpy.app.version_string,'output_size':[640,360],'audio':'none by design'})


def inspect(root):
    scene=bpy.context.scene;cube=bpy.data.objects['SM_PilotCube'];poses=[]
    for frame in (1,36,72):
        scene.frame_set(frame);bpy.context.view_layer.update();poses.append({'frame':frame,'rotation_z':cube.rotation_euler.z})
    report=inventory();report.update(contract='blender-skills-pilot-v1',reopened=True,poses=poses,blend_saved=False)
    assert poses[0]['rotation_z']!=poses[1]['rotation_z']!=poses[2]['rotation_z']
    write(root,'pilot-inspect.json',report)


def skills_qa(root):
    folder=root/'references/blender-skills'
    expected={'qa_check.py':'a4f94b4e8b96dfe3ecf820aa841bcde4dc788994','_bpyx.py':'201c7fc7ac3706e46f79ec69a0f41372882e92a3'}
    for name,blob in expected.items():
        data=(folder/name).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob,'Candidate code identity changed'
    sys.path.insert(0,str(folder));sys.modules.pop('_bpyx',None)
    spec=importlib.util.spec_from_file_location('pilot_pinned_upstream_qa',folder/'qa_check.py')
    qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
    reports={name:qa.run(objects=[name],profile='render') for name in ('SM_PilotCube','SM_PilotSphere','SM_PilotFloor')}
    assert all(r['pass'] for r in reports.values()),reports
    write(root,'pilot-skills_qa.json',{'contract':'blender-skills-pilot-v1','revision':'1a1cc6c49312f9f370aae86f52b7b907f29c94f6','source_blobs':expected,'reports':reports,'accepted_warnings':'UV maps absent intentionally for procedural materials; open floor is environmental, not a printable asset','blend_saved':False,'scope':'Pinned upstream checker run locally per independent mesh; no other candidate scripts executed'})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['build','render','inspect','skills_qa'],required=True);parser.add_argument('--project',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);root=Path(args.project).resolve()
    assert bpy.app.version[:3]==(5,3,0) and root.is_dir()
    {'build':build,'render':render,'inspect':inspect,'skills_qa':skills_qa}[args.phase](root)
