"""AnubisCore pymodel — round-counting wrappers over the golden hash cores.

Specifies the cycle structure of the future RTL: SHA-256 = 64 rounds/block,
Keccak-f[1600] = 24 rounds/permutation. Digests are bit-identical to golden.
"""
import anubis_hash as g

SHA256_ROUNDS_PER_BLOCK = 64
KECCAK_ROUNDS_PER_PERM = 24


class Sha256Engine:
    def __init__(self):
        self.rounds = 0

    def run(self, data):
        self.rounds = 0
        return g.sha256(data, on_round=lambda *_: self._tick())

    def _tick(self):
        self.rounds += 1


class Sha3Engine:
    def __init__(self):
        self.rounds = 0

    def run(self, data):
        self.rounds = 0
        return g.sha3_256(data, on_round=lambda *_: self._tick())

    def _tick(self):
        self.rounds += 1
