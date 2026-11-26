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
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', required=True)
    parser.add_argument('--project', required=True)
    parser.add_argument('--stage', required=True)
    parser.add_argument('--tool', required=True)
    parser.add_argument('--inputs', required=True)
    args = parser.parse_args()
    project = (ROOT / 'projects' / args.project).resolve()
    project.relative_to((ROOT / 'projects').resolve())
    if not (project / 'artifacts').is_dir():
        raise ValueError('Initialize the pipeline project before invoking this transport')
    profile = json.loads(Path(args.profile).read_text(encoding='utf-8-sig'))
    os.environ.update(environment(profile, project / 'artifacts/network.jsonl'))
    sys.argv = ['run_pipeline_tool.py', '--project', args.project, '--stage', args.stage,
                '--tool', args.tool, '--inputs', args.inputs]
    runpy.run_path(str(ROOT / 'scripts/run_pipeline_tool.py'), run_name='__main__')


if __name__ == '__main__':
    main()
