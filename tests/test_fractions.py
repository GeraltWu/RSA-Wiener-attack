"""测试连分数的精确构造过程。"""

import unittest

from src.continued_fraction import continued_fraction, convergents


class ContinuedFractionTests(unittest.TestCase):
    def test_design_example(self) -> None:
        coefficients = continued_fraction(43, 19)
        self.assertEqual(coefficients, [2, 3, 1, 4])
        self.assertEqual(
            list(convergents(coefficients)),
            [(2, 1), (7, 3), (9, 4), (43, 19)],
        )

    def test_fraction_below_one_starts_with_zero(self) -> None:
        coefficients = continued_fraction(3, 7)
        self.assertEqual(coefficients[0], 0)
        self.assertEqual(list(convergents(coefficients))[-1], (3, 7))

    def test_non_coprime_input_reduces_in_final_convergent(self) -> None:
        coefficients = continued_fraction(42, 18)
        self.assertEqual(list(convergents(coefficients))[-1], (7, 3))

    def test_single_coefficient_and_invalid_denominator(self) -> None:
        self.assertEqual(list(convergents(continued_fraction(5, 1))), [(5, 1)])
        with self.assertRaises(ValueError):
            continued_fraction(1, 0)


if __name__ == "__main__":
    unittest.main()
