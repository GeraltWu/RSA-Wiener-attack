"""生成现场演示使用的两份 2048-bit RSA fixture。"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rsa import RSAKeyPair, generate_normal_rsa
from src.weak_key_generator import generate_weak_rsa
from src.wiener_attack import wiener_attack


FIXTURE_DIR = PROJECT_ROOT / "fixtures"


def save_fixture(path: Path, kind: str, key: RSAKeyPair) -> None:
    """把 RSA 密钥保存为便于检查的十进制 JSON。"""

    data = {name: str(value) for name, value in asdict(key).items()}
    data["kind"] = kind
    data["warning"] = "仅供本课程本地演示，不得用于保护真实数据"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    """生成、验证并保存弱密钥和普通密钥 fixture。"""

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    print("正在生成 2048-bit Wiener 弱密钥……")
    weak_key = generate_weak_rsa(2048, 0.25).key_pair
    # 验证 fixture 在保存前确实能被只接收 e、n 的攻击函数恢复。
    weak_result = wiener_attack(weak_key.e, weak_key.n)
    if weak_result is None or weak_result.d != weak_key.d:
        raise RuntimeError("生成的弱密钥未通过 Wiener 攻击验证")

    print("正在生成 2048-bit 普通 RSA 对照密钥……")
    normal_key = generate_normal_rsa(2048)
    normal_result = wiener_attack(normal_key.e, normal_key.n)
    if normal_result is not None:
        raise RuntimeError("普通 RSA fixture 意外被 Wiener 攻击恢复")

    save_fixture(FIXTURE_DIR / "weak_rsa_2048.json", "wiener_weak", weak_key)
    save_fixture(FIXTURE_DIR / "normal_rsa_2048.json", "normal_control", normal_key)
    print(f"fixture 已保存到：{FIXTURE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
