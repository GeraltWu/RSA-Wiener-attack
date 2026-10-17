"""测试 RSA 变换和密钥生成。"""

import unittest
from math import gcd

from src.rsa import generate_normal_rsa, rsa_decrypt, rsa_encrypt
from src.weak_key_generator import (
    approximate_wiener_threshold,
    generate_weak_rsa,
    is_below_wiener_bound,
)


class RSATests(unittest.TestCase):
    def test_rsa_example(self) -> None:
        n, e, d = 3233, 17, 2753
        ciphertext = rsa_encrypt(65, e, n)
        self.assertEqual(ciphertext, 2790)
        self.assertEqual(rsa_decrypt(ciphertext, d, n), 65)

    def test_transform_rejects_out_of_range_integer(self) -> None:
        with self.assertRaises(ValueError):
            rsa_encrypt(3233, 17, 3233)
        with self.assertRaises(ValueError):
            rsa_decrypt(-1, 2753, 3233)

    def test_normal_key_invariants_and_round_trip(self) -> None:
        key = generate_normal_rsa(64)
        self.assertEqual(key.n.bit_length(), 64)
        self.assertNotEqual(key.p, key.q)
        self.assertEqual(key.p * key.q, key.n)
        self.assertEqual(gcd(key.e, key.phi), 1)
        self.assertEqual((key.e * key.d) % key.phi, 1)

        for message in (0, 1, 2, 42, key.n - 1):
            encrypted = rsa_encrypt(message, key.e, key.n)
            self.assertEqual(rsa_decrypt(encrypted, key.d, key.n), message)

    def test_weak_key_is_valid_and_below_requested_scale(self) -> None:
        key = generate_weak_rsa(64, 0.5)
        self.assertEqual(key.modulus_bits, 64)
        self.assertEqual(key.p * key.q, key.n)
        self.assertEqual((key.e * key.d) % key.phi, 1)
        self.assertTrue(key.d % 2 == 1)
        self.assertTrue(key.below_wiener_bound)
        self.assertEqual(key.below_wiener_bound, is_below_wiener_bound(key.d, key.n))

    def test_wiener_bound_helpers_use_integer_arithmetic(self) -> None:
        # 使用一个 2048-bit 规模的整数，确保辅助函数能处理无法安全地将 n
        # 本身转换成浮点数的范围。
        large_n = (1 << 2048) - 159
        threshold = approximate_wiener_threshold(large_n)
        self.assertIsInstance(threshold, int)
        self.assertGreater(threshold, 0)
        self.assertEqual(
            is_below_wiener_bound(threshold - 1, large_n),
            81 * (threshold - 1) ** 4 < large_n,
        )


if __name__ == "__main__":
    unittest.main()
