"""测试自行实现的数论算法。"""

import unittest

from src.number_theory import (
    extended_gcd,
    gcd,
    mod_inverse,
)


class NumberTheoryTests(unittest.TestCase):
    def test_gcd_accepts_signs_and_zero(self) -> None:
        self.assertEqual(gcd(54, 24), 6)
        self.assertEqual(gcd(-54, 24), 6)
        self.assertEqual(gcd(0, 0), 0)

    def test_extended_gcd_satisfies_bezout_identity(self) -> None:
        for a, b in ((240, 46), (43, 19), (17, 3120), (0, 7), (0, 0)):
            divisor, x, y = extended_gcd(a, b)
            self.assertEqual(a * x + b * y, divisor)
            self.assertEqual(divisor, gcd(a, b))

        self.assertEqual(extended_gcd(43, 19), (1, 4, -9))

    def test_mod_inverse_known_value_and_failure(self) -> None:
        self.assertEqual(mod_inverse(17, 3120), 2753)
        self.assertEqual(mod_inverse(-3, 11), 7)
        with self.assertRaises(ValueError):
            mod_inverse(12, 18)

if __name__ == "__main__":
    unittest.main()
