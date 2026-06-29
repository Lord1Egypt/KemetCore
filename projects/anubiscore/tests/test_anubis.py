import hashlib
import os

import anubis_hash as g
from anubis_hash_model import (Sha256Engine, Sha3Engine,
                               SHA256_ROUNDS_PER_BLOCK, KECCAK_ROUNDS_PER_PERM)


def test_sha256_vs_hashlib():
    for n in [0, 1, 55, 56, 63, 64, 65, 119, 120, 200, 1000]:
        data = os.urandom(n)
        assert g.sha256(data).hex() == hashlib.sha256(data).hexdigest()


def test_sha3_256_vs_hashlib():
    for n in [0, 1, 135, 136, 137, 271, 272, 500, 1000]:
        data = os.urandom(n)
        assert g.sha3_256(data).hex() == hashlib.sha3_256(data).hexdigest()


def test_sha3_512_vs_hashlib():
    for n in [0, 1, 71, 72, 73, 143, 144, 500, 1000]:
        data = os.urandom(n)
        assert g.sha3_512(data).hex() == hashlib.sha3_512(data).hexdigest()


def test_known_vectors():
    assert g.sha256(b"").hex() == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    assert g.sha256(b"abc").hex() == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
    assert g.sha3_256(b"").hex() == (
        "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a")
    assert g.sha3_256(b"abc").hex() == (
        "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532")
    assert g.sha3_512(b"").hex() == (
        "a69f73cca23a9ac5c8b567dc185a756e97c982164fe25859e0d1dcc1475c80a6"
        "15b2123af1f5f94c11e3e9402c3ac558f500199d95b6d3e301758586281dcd26")
    assert g.sha3_512(b"abc").hex() == (
        "b751850b1a57168a5693cd924b6b096e08f621827444f70d884f5d0240d2712e"
        "10e116e9192af3c91a7ec57647e3934057340b4cf408d5a56592f8274eec53f0")


def test_pymodel_rounds():
    eng = Sha256Engine()
    d = os.urandom(200)  # 200 bytes -> padded to 4 blocks of 64 bytes
    assert eng.run(d) == g.sha256(d)
    assert eng.rounds % SHA256_ROUNDS_PER_BLOCK == 0
    assert eng.rounds == SHA256_ROUNDS_PER_BLOCK * 4

    k = Sha3Engine()
    assert k.run(b"abc") == g.sha3_256(b"abc")
    assert k.rounds % KECCAK_ROUNDS_PER_PERM == 0
