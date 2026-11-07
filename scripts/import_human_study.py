import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coursepilot.engine import Recommender
from coursepilot.study import import_human_benchmark

parser = argparse.ArgumentParser(description="Validate complete human judgments before evaluation")
parser.add_argument("--profiles", type=Path, required=True)
parser.add_argument("--ratings", type=Path, required=True)
parser.add_argument("--output", type=Path, default=Path("data/human/private/benchmark.json"))
args = parser.parse_args()
data = import_human_benchmark(args.profiles, args.ratings, Recommender())
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"Validated {len(data['profiles'])} human profiles: {args.output}")
