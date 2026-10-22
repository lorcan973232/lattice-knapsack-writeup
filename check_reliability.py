"""Solve many fresh instances and report how often each key is recovered.

    python check_reliability.py --instances 100
    python check_reliability.py --instances 100 --scale1 1 --scale2 10   # original solve's weights
"""

from __future__ import annotations

import argparse
import time

from make_instance import make_instance
from solve import DEFAULT_SCALES, recover_key


def check(instance, which, scale) -> bool:
    """True when the recovered key satisfies its knapsack equation."""
    weights, wanted = instance[f"weights{which}"], instance[f"key{which}_hash"]
    modulo = instance["p"] if which == 2 else None
    try:
        key = recover_key(weights, wanted, modulo=modulo, scale=scale)
    except RuntimeError:
        return False
    total = sum(w * k for w, k in zip(weights, key))
    return (total % modulo if modulo else total) == wanted


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--instances", type=int, default=100)
    parser.add_argument("--first-seed", type=int, default=1)
    parser.add_argument("--scale1", type=int, default=DEFAULT_SCALES[0], help="Weight for the plain-sum key.")
    parser.add_argument("--scale2", type=int, default=DEFAULT_SCALES[1], help="Weight for the modular key.")
    args = parser.parse_args()

    start = time.perf_counter()
    counts = {1: 0, 2: 0, "both": 0}
    for seed in range(args.first_seed, args.first_seed + args.instances):
        instance = make_instance(seed)
        ok1, ok2 = check(instance, 1, args.scale1), check(instance, 2, args.scale2)
        counts[1] += ok1
        counts[2] += ok2
        counts["both"] += ok1 and ok2
    n, elapsed = args.instances, time.perf_counter() - start
    print(f"scales {args.scale1}/{args.scale2} over {n} instances: key1 {counts[1]}/{n}, "
          f"key2 {counts[2]}/{n}, both {counts['both']}/{n} ({elapsed / n:.2f} s per instance)")


if __name__ == "__main__":
    main()
