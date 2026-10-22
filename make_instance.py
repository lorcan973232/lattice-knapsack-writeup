"""Generate a fresh instance with the same structure as the original challenge.

Two random 16-byte AES keys are hidden behind knapsack-style sums: the first as
a plain integer sum over 140-bit weights, the second as the same kind of sum
reduced modulo a 140-bit prime. Each key encrypts a known test message, and the
flag is encrypted under key1 XOR key2. None of the values come from the
original challenge.

    python make_instance.py --seed 1 --out instance.json
"""

from __future__ import annotations

import argparse
import json
import random

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from sympy import nextprime

BITS = 140
KEY_BYTES = 16


def encrypt(key: bytes, message: bytes) -> str:
    return AES.new(key, AES.MODE_ECB).encrypt(pad(message, 16)).hex()


def make_instance(seed: int) -> dict:
    # Every value comes from this seeded generator, so a seed always gives the same instance.
    rng = random.Random(seed)
    p = nextprime(rng.randrange(2 ** (BITS - 1), 2 ** BITS - 2 ** 32))
    key1 = bytes(rng.randrange(256) for _ in range(KEY_BYTES))
    key2 = bytes(rng.randrange(256) for _ in range(KEY_BYTES))
    weights1 = [rng.randrange(2 ** (BITS - 1), 2 ** BITS) for _ in range(KEY_BYTES)]
    weights2 = [rng.randrange(1, p) for _ in range(KEY_BYTES)]
    key3 = bytes(a ^ b for a, b in zip(key1, key2))
    return {
        "seed": seed,
        "p": p,
        "weights1": weights1,
        "weights2": weights2,
        "key1_hash": sum(w * k for w, k in zip(weights1, key1)),
        "key2_hash": sum(w * k for w, k in zip(weights2, key2)) % p,
        "enc1": encrypt(key1, b"first key recovered"),
        "enc2": encrypt(key2, b"second key recovered"),
        "enc3": encrypt(key3, f"flag{{fresh_instance_seed_{seed}}}".encode()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", default="instance.json")
    args = parser.parse_args()
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(make_instance(args.seed), f, indent=2)
    print(f"wrote {args.out} (seed {args.seed})")


if __name__ == "__main__":
    main()
