# Recovering AES keys hidden in knapsack sums with LLL and Babai's nearest-plane algorithm

My write-up and solver for a CTF lattice cryptography challenge that hides two
AES keys behind knapsack-style sums. The repository reproduces the method on
freshly generated instances with the same structure; it contains none of the
original challenge values.

## The challenge

Two random 16-byte AES keys, `key1` and `key2`, are hidden behind public
knapsack-style sums:

```text
key1_hash = w1[0]*key1[0] + ... + w1[15]*key1[15]              (plain integer sum)
key2_hash = (w2[0]*key2[0] + ... + w2[15]*key2[15]) mod p       (sum modulo a prime)
```

The weights `w1`, `w2` and the prime `p` are public and about 140 bits long.
Each key encrypts a known test message with AES-ECB, and the flag is encrypted
under `key1 XOR key2`. Recovering both keys recovers the flag.

## Why this is a lattice problem

Each unknown is a byte, between 0 and 255, while every weight is around 2^140.
Among all integer vectors that satisfy one of these equations, the real key is
extraordinarily short once it is centred on the middle of the byte range. Finding
it is a closest-vector problem in a small lattice.

For the 16 unknowns, build a basis with one row per weight, plus one row for the
modulus in the modular case:

```text
b_i     = (e_i | s * w_i)      for i = 0..15     (e_i is the i-th unit vector)
b_p     = (0   | s * p)        modular case only
```

Any integer combination of these rows has the form
`(k_0, ..., k_15 | s * (sum of k_i * w_i, minus a multiple of p))`. The target is

```text
T = (c, c, ..., c | s * hash)
```

with `c` = 127 or 128, the centre of the byte range. The lattice point that
corresponds to the real key matches the last coordinate exactly and differs from
`T` by at most 128 in each of the 16 byte coordinates, so it is within distance
512 of `T`. A point that misses the equation by `d` is at least `s * |d|` away in
the last coordinate alone, so the weight `s` decides how strongly the search is
held to the equation.

The solver:

1. Builds the basis and reduces it with LLL (delta 0.99).
2. Runs Babai's nearest-plane algorithm on the reduced basis with exact rational
   Gram-Schmidt, so 140-bit entries cause no floating-point error.
3. Accepts the point only if its last coordinate equals `s * hash` and every byte
   is in 0–255, trying both centres.
4. Confirms each key by decrypting its test message, then XORs the keys and
   decrypts the flag.

## How I got there

While working on the challenge I found the write-up for DownUnderCTF 2021's
[yadlp](https://ctftime.org/writeup/30584), which has a similar shape: bounded
unknowns in a modular knapsack-style relation. It links the solver it used,
[`solvelinmod.py`](https://github.com/nneonneo/pwn-stuff/blob/master/math/solvelinmod.py)
by Robert Xiao, which solves bounded systems of modular linear equations with
lattice reduction. That gave me the general idea. I then used my notes from
CryptoHack's [post-quantum lattice challenges](https://cryptohack.org/challenges/post-quantum/)
to adapt the construction to sixteen byte-sized unknowns, and wrote the solver
myself with sympy's LLL and an exact-arithmetic Babai step. It shares no code
with `solvelinmod.py`, which runs on Sage and uses Kannan's embedding rather
than Babai, but two ideas are common to both: centring each unknown on the
middle of its range, and weighting the equation columns so that short vectors
satisfy the equations.

## Reliability

My original solve used equation weights of 1 for `key1` and 10 for `key2`, which
recovered both keys of the challenge instance. Testing afterwards on 100 fresh
instances (seeds 1–100, `check_reliability.py`) showed the method is less
reliable than that single success suggests, and that a heavier weight fixes most
of the failures:

| Weight for key1 | Weight for key2 | key1 recovered | key2 recovered | Both |
| --- | --- | --- | --- | --- |
| 1 | 10 (original solve) | 95/100 | 79/100 | 75/100 |
| 10 | 100 | 100/100 | 94/100 | 94/100 |
| 100 | 1000 | 100/100 | 96/100 | 96/100 |
| 1000 | 1000 (default) | 100/100 | 96/100 | 96/100 |
| 2^20 | 2^20 | 100/100 | 96/100 | 96/100 |

Logging why each point was rejected explains the difference. At the original
weights, 25 of the 26 rejected points broke both the equation and the byte
bounds. With a weight of 1, missing the equation by 1 costs only 1 in distance,
so lattice points that trade a small equation error for closer byte coordinates
compete with the key, and Babai's rounding drifts on every coordinate. At a
weight of 1000, every point Babai returned satisfied the equation. This matches
`solvelinmod.py`, which scales its equation columns far above the variable range.

The 4 remaining failures, all on the modular key, satisfy the equation but fall
outside 0–255. Babai's nearest-plane algorithm only approximates the closest
vector, so it sometimes lands on another solution of the equation near the
target instead of the key. Kannan's embedding with a short enumeration, or BKZ
reduction, would be the next step for those.

## Running it

```bash
python -m pip install -r requirements.txt
python solve.py                                     # solves the bundled instance.json
python make_instance.py --seed 7 --out seed7.json   # generate another instance
python solve.py seed7.json
python solve.py instance.json --original-scales     # original weights: fails on seed 1, one of its misses
python check_reliability.py --instances 100         # reproduce the table
```

`python-flint` is required: with it installed, sympy uses FLINT's LLL. Without
it, current sympy falls back to a pure-Python LLL that fails an internal
assertion on these 140-bit inputs. Solving an instance takes about 0.1–0.2
seconds.

## Files

| File | Purpose |
| --- | --- |
| `solve.py` | Lattice construction, LLL, exact Babai, key checks and flag decryption. |
| `make_instance.py` | Generates a fresh instance with the challenge's structure from a seed. |
| `instance.json` | A bundled instance (seed 1). |
| `check_reliability.py` | Success rates over many instances for chosen weights. |

## Licence

MIT; see [`LICENSE`](LICENSE).
