"""测试攻击只使用公开参数，并且会验证精确因数。"""

import json
import unittest
from pathlib import Path

from src.wiener_attack import wiener_attack
from src.weak_key_generator import generate_weak_rsa


class WienerAttackTests(unittest.TestCase):
    def test_known_vulnerable_vector(self) -> None:
        # n=379*239，phi=89964，并且 17993*5 = 1 + 89964。
        # 这里特意只把公开的 e、n 传给攻击函数。
        result = wiener_attack(e=17993, n=90581)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.d, 5)
        self.assertEqual({result.p, result.q}, {379, 239})
        self.assertEqual(result.p * result.q, 90581)

    def test_generated_weak_key_is_recovered(self) -> None:
        key = generate_weak_rsa(64, 0.5)
        result = wiener_attack(key.e, key.n)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.d, key.d)
        self.assertEqual(result.p * result.q, key.n)

    def test_2048_bit_fixture_is_recovered(self) -> None:
        fixture_path = Path(__file__).parents[1] / "fixtures" / "weak_rsa_2048.json"
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        n, e, expected_d = int(data["n"]), int(data["e"]), int(data["d"])

        result = wiener_attack(e, n)
        self.assertEqual(n.bit_length(), 2048)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.d, expected_d)
        self.assertEqual(result.p * result.q, n)

    def test_non_vulnerable_public_key_returns_none(self) -> None:
        # d=2753 的 RSA 示例不是小 d 的 Wiener 弱密钥。
        self.assertIsNone(wiener_attack(e=17, n=3233))

    def test_invalid_public_key_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            wiener_attack(e=1, n=3233)
        with self.assertRaises(ValueError):
            wiener_attack(e=4000, n=3233)


if __name__ == "__main__":
    unittest.main()
