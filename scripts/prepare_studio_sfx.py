"""Prepare a completed local MotionGraphics ZIP once; never downloads/executes it."""
import argparse
import json
from pathlib import Path
from lib import production_studio as studio
from lib.studio_sfx_catalog import prepare


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',required=True)
    parser.add_argument('--config-dir',type=Path,default=studio.CONFIG_DIR)
    args=parser.parse_args()
    print(json.dumps(prepare(args.archive,args.config_dir/'sfx-catalog.json'),ensure_ascii=False))


if __name__=='__main__':main()
