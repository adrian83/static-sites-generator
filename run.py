#!/usr/bin/env python3
"""Entry point for the static site generator.

Usage:
  python run.py           # no scaling (100%)
  python run.py --scale 50   # scale event images to 50% of original
"""

import argparse
from ssg.generator import build


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Static site generator')
    p.add_argument('--scale', '-s', type=int, default=100,
                   help='Scale percentage for event images (e.g. 50). 100 means no scaling.')
    return p.parse_args()


if __name__ == '__main__':
    args = parse_args()
    scale = args.scale if args.scale and args.scale > 0 else 100
    build(scale)
