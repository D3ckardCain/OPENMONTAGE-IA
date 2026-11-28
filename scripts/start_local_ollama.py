"""Start the prepared local-only service; does not download, import or run models."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.local_ollama import start


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', required=True)
    parser.add_argument('--models-dir', required=True)
    parser.add_argument('--port', type=int, default=11434)
    parser.add_argument('--log-dir', default=str(Path(__file__).resolve().parents[1] / '.backlot/ollama'))
    args = parser.parse_args()
    result = start(args.executable, args.models_dir, args.log_dir, args.port)
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
