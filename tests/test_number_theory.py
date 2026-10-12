"""测试自行实现的数论算法。"""

import unittest

from src.number_theory import (
    extended_gcd,
    gcd,
    generate_prime,
    integer_sqrt,
    is_probable_prime,
    mod_inverse,
)


class NumberTheoryTests(unittest.TestCase):
    def test_gcd_accepts_signs_and_zero(self) -> None:
        self.assertEqual(gcd(54, 24), 6)
        self.assertEqual(gcd(-54, 24), 6)
        self.assertEqual(gcd(0, 0), 0)

    def test_extended_gcd_satisfies_bezout_identity(self) -> None:
        for a, b in ((240, 46), (-54, 24), (17, -31), (0, 7), (0, 0)):
            divisor, x, y = extended_gcd(a, b)
            self.assertEqual(a * x + b * y, divisor)
            self.assertEqual(divisor, gcd(a, b))

    def test_integer_sqrt_is_exact_for_large_integers(self) -> None:
        values = (0, 1, 2, 3, 4, 15, 16, 17, (1 << 2048) - 159)
        for value in values:
            root = integer_sqrt(value)
            self.assertLessEqual(root * root, value)
            self.assertGreater((root + 1) * (root + 1), value)

    def test_mod_inverse_known_value_and_failure(self) -> None:
        self.assertEqual(mod_inverse(17, 3120), 2753)
        with self.assertRaises(ValueError):
            mod_inverse(12, 18)

    def test_miller_rabin_known_values(self) -> None:
        for prime in (2, 3, 37, 101, 104729):
            self.assertTrue(is_probable_prime(prime))
        for composite in (-1, 0, 1, 4, 9, 341, 561, 1105):
            self.assertFalse(is_probable_prime(composite))

    def test_generated_prime_has_exact_length(self) -> None:
        prime = generate_prime(64)
        self.assertEqual(prime.bit_length(), 64)
        self.assertTrue(is_probable_prime(prime, rounds=50))


if __name__ == "__main__":
    unittest.main()
