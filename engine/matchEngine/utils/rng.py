# engine/matchEngine/utils/rng.py

import hashlib
import struct

class DeterministicRNG:
    """
    Deterministic RNG that produces the same number for the same
    (master_seed, tick, channel, key) combination, independent of call order.
    """

    def __init__(self, master_seed: int):
        self.master_seed = int(master_seed)

    def _hash_to_bytes(self, channel: str, tick: int, key: int | str = 0) -> bytes:
        """
        Creates a SHA256 hash of the deterministic RNG inputs.
        """
        # Normalize all parts to bytes
        seed_bytes = str(self.master_seed).encode("utf-8")
        tick_bytes = str(tick).encode("utf-8")
        channel_bytes = str(channel).encode("utf-8")
        key_bytes = str(key).encode("utf-8")

        m = hashlib.sha256()
        m.update(seed_bytes)
        m.update(b"|")
        m.update(tick_bytes)
        m.update(b"|")
        m.update(channel_bytes)
        m.update(b"|")
        m.update(key_bytes)
        return m.digest()

    def randf(self, channel: str, tick: int, key: int | str = 0) -> float:
        """
        Deterministic float in [0, 1) for given (channel, tick, key).
        """
        h = self._hash_to_bytes(channel, tick, key)
        # Take first 8 bytes as unsigned long long, normalize to [0,1)
        val_int = struct.unpack(">Q", h[:8])[0]
        return val_int / 2**64

    def randint(self, channel: str, tick: int, a: int, b: int, key: int | str = 0) -> int:
        """
        Deterministic int in [a, b] inclusive for given (channel, tick, key).
        """
        if a > b:
            raise ValueError("a must be <= b")
        rf = self.randf(channel, tick, key)
        return a + int(rf * (b - a + 1))
