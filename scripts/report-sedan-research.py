import argparse
from pathlib import Path
from zephyr.research.report import make_report

parser = argparse.ArgumentParser(description='Produce standalone research evidence; frontend unchanged.')
parser.add_argument('--directory', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--speed-kmh', type=float, default=120.)
args = parser.parse_args()
result = make_report(args.directory, args.output, args.speed_kmh)
print(result['status'], result['counts'])
