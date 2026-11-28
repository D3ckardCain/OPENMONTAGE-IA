"""Single-call registry transport; stage decisions remain with the agent."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True);parser.add_argument('--stage',required=True)
    parser.add_argument('--tool',required=True);parser.add_argument('--inputs',required=True)
    args=parser.parse_args()
    from lib import checkpoint
    from lib.pipeline_loader import load_pipeline
    from tools.tool_registry import registry
    root=checkpoint.PROJECTS_DIR/args.project
    root.resolve().relative_to(checkpoint.PROJECTS_DIR.resolve())
    marker=json.loads((root/'project.json').read_text(encoding='utf-8'))
    manifest=load_pipeline(marker['pipeline_type'])
    stage=next(s for s in manifest['stages'] if s['name']==args.stage)
    if args.tool not in stage.get('tools_available',[]):raise ValueError('Tool not allowed by this pipeline stage')
    current=checkpoint.read_checkpoint(checkpoint.PROJECTS_DIR,args.project,args.stage)
    if not current or current['status']!='in_progress':raise ValueError('Enter the pipeline stage before invoking a tool')
    inputs_path=Path(args.inputs).resolve();inputs_path.relative_to(root.resolve())
    inputs=json.loads(inputs_path.read_text(encoding='utf-8'))
    if inputs.get('project_id')!=args.project:raise ValueError('Project binding differs from stage')
    registry.discover()
    tool=registry.get(args.tool)
    if tool is None:raise ValueError('Tool unavailable in registry')
    result=tool.execute(inputs)
    print(json.dumps({'success':result.success,'data':result.data,'error':result.error},ensure_ascii=True),flush=True)
    return 0 if result.success else 1


if __name__=='__main__':raise SystemExit(main())
