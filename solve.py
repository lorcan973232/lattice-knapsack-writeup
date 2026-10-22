from fractions import Fraction
import json
import sys

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from sympy import Matrix


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def nearest_integer(x):
    if x >= 0:
        return (x.numerator + x.denominator // 2) // x.denominator
    return -((-x.numerator + x.denominator // 2) // x.denominator)


def exact_babai(reduced_basis, target):
    stars = []
    norms = []

    for row in reduced_basis:
        v = [Fraction(x) for x in row]
        for star, norm in zip(stars, norms):
            mu = Fraction(dot(row, star), norm)
            v = [x - mu * y for x, y in zip(v, star)]
        stars.append(v)
        norms.append(dot(v, v))

    diff = [Fraction(x) for x in target]
    coeffs = [0] * len(reduced_basis)

    for i in range(len(reduced_basis) - 1, -1, -1):
        coeffs[i] = nearest_integer(Fraction(dot(diff, stars[i]), norms[i]))
        diff = [x - coeffs[i] * y for x, y in zip(diff, reduced_basis[i])]

    answer = [0] * len(target)
    for coeff, row in zip(coeffs, reduced_basis):
        for i in range(len(target)):
            answer[i] += coeff * row[i]
    return answer


def recover_key(weights, wanted_hash, modulo=None, scale=1):
    rows = []
    for i, weight in enumerate(weights):
        row = [0] * 17
        row[i] = 1
        row[-1] = scale * weight
        rows.append(row)

    if modulo is not None:
        row = [0] * 17
        row[-1] = scale * modulo
        rows.append(row)

    reduced = Matrix(rows).lll(delta=0.99).tolist()

    for center in (127, 128):
        target = [center] * 16 + [scale * wanted_hash]
        point = exact_babai(reduced, target)
        key = point[:16]
        if point[-1] == scale * wanted_hash and all(0 <= x <= 255 for x in key):
            return bytes(key)

    raise RuntimeError("key was not recovered")


def decrypt(key, ciphertext_hex):
    return unpad(AES.new(key, AES.MODE_ECB).decrypt(bytes.fromhex(ciphertext_hex)), 16)


# Weight on the equation column. The original solve used 1 and 10; testing on
# fresh instances showed 1000 makes Babai's answer satisfy the equation far more
# often (see README).
ORIGINAL_SCALES = (1, 10)
DEFAULT_SCALES = (1000, 1000)


def solve(instance, scale1=DEFAULT_SCALES[0], scale2=DEFAULT_SCALES[1]):
    key1 = recover_key(instance["weights1"], instance["key1_hash"], scale=scale1)
    key2 = recover_key(instance["weights2"], instance["key2_hash"], modulo=instance["p"], scale=scale2)

    assert decrypt(key1, instance["enc1"]) == b"first key recovered"
    assert decrypt(key2, instance["enc2"]) == b"second key recovered"

    key3 = bytes(a ^ b for a, b in zip(key1, key2))
    return decrypt(key3, instance["enc3"]).decode()


if __name__ == "__main__":
    args = sys.argv[1:]
    scales = ORIGINAL_SCALES if "--original-scales" in args else DEFAULT_SCALES
    paths = [a for a in args if not a.startswith("--")]
    with open(paths[0] if paths else "instance.json", encoding="utf-8") as f:
        instance = json.load(f)
    try:
        print(solve(instance, *scales))
    except RuntimeError as exc:
        sys.exit(f"{exc} with equation weights {scales[0]}/{scales[1]} (see README, Reliability)")
