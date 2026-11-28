"""Registry transport with an explicit private profile; never installs anything."""
import argparse
import json
import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from lib.hyperframes_offline_profile import environment
    from lib import hyperframes_profile_store as profiles
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', help='Optional explicit child override; defaults to the selected Studio profile')
    parser.add_argument('--inspect-profile', action='store_true', help='Read selected runtime; never execute a pipeline tool')
    parser.add_argument('--project')
    parser.add_argument('--stage')
    parser.add_argument('--tool')
    parser.add_argument('--inputs')
    args = parser.parse_args()
    if args.profile:
        profile = json.loads(Path(args.profile).read_text(encoding='utf-8-sig'))
        profile.setdefault('gsap_package_dir', str(Path(profile['package_dir']).parent/'gsap'))
    else:
        profile = profiles.read()['profile']
        if profile is None:raise ValueError('Select an offline HyperFrames profile in Studio first')
    profile = profiles.validate(profile)
    if args.inspect_profile:
        from lib import hyperframes_runtime
        profiles.use_child_profile(profile, Path(profile['scratch'])/'network.jsonl')
        print(json.dumps({'contract':'hf-profile-v1', 'selection_source':'explicit_child' if args.profile else 'studio_selected',
                          'availability':hyperframes_runtime.check(), 'generation_executed':False}))
        return
    if any(getattr(args,key) is None for key in ('project','stage','tool','inputs')):
        parser.error('production transport requires --project --stage --tool --inputs')
    project = (ROOT / 'projects' / args.project).resolve()
    project.relative_to((ROOT / 'projects').resolve())
    if not (project / 'artifacts').is_dir():
        raise ValueError('Initialize the pipeline project before invoking this transport')
    profiles.use_child_profile(profile, project / 'artifacts/network.jsonl')
    os.environ.update(environment(profile, project / 'artifacts/network.jsonl'))
    sys.argv = ['run_pipeline_tool.py', '--project', args.project, '--stage', args.stage,
                '--tool', args.tool, '--inputs', args.inputs]
    runpy.run_path(str(ROOT / 'scripts/run_pipeline_tool.py'), run_name='__main__')


if __name__ == '__main__':
    main()
