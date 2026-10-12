"""一条命令完成 Wiener 攻击现场演示。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# 直接运行 python scripts/demo.py 时，需要把项目根目录加入模块搜索路径。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rsa import RSAKeyPair, generate_normal_rsa, rsa_decrypt, rsa_encrypt
from src.weak_key_generator import generate_weak_rsa
from src.wiener_attack import wiener_attack


DEFAULT_WEAK_FIXTURE = PROJECT_ROOT / "fixtures" / "weak_rsa_2048.json"
DEFAULT_NORMAL_FIXTURE = PROJECT_ROOT / "fixtures" / "normal_rsa_2048.json"


def abbreviate(value: int, digits: int = 16) -> str:
    """缩写大整数，只展示十进制开头和结尾。"""

    text = str(value)
    if len(text) <= digits * 2:
        return text
    return f"{text[:digits]}...{text[-digits:]}"


def load_key_fixture(path: Path) -> RSAKeyPair:
    """读取并验证一份 RSA JSON fixture。"""

    if not path.exists():
        raise FileNotFoundError(f"找不到 fixture：{path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    required = ("n", "e", "d", "p", "q", "phi")
    missing = [name for name in required if name not in data]
    if missing:
        raise ValueError(f"fixture 缺少字段：{', '.join(missing)}")

    key = RSAKeyPair(**{name: int(data[name]) for name in required})
    if key.p * key.q != key.n:
        raise ValueError("fixture 不满足 p*q == n")
    if (key.p - 1) * (key.q - 1) != key.phi:
        raise ValueError("fixture 中的 phi 不正确")
    if (key.e * key.d) % key.phi != 1:
        raise ValueError("fixture 不满足 e*d mod phi == 1")
    return key


def show_experiment_files() -> None:
    """列出已经生成的实验图，不自动打开图形窗口。"""

    plot_dir = PROJECT_ROOT / "results" / "plots"
    expected = (
        plot_dir / "wiener_success_vs_d_ratio.png",
        plot_dir / "wiener_time_vs_modulus_bits.png",
    )
    existing = [path for path in expected if path.exists()]
    if existing:
        print("6) 已生成的实验图：")
        for path in existing:
            print(f"   {path.relative_to(PROJECT_ROOT)}")
    else:
        print("6) 尚未生成实验图；可运行 python scripts/run_experiments.py --quick")


def run_demo(weak_key: RSAKeyPair, normal_key: RSAKeyPair, source: str) -> bool:
    """执行弱密钥攻击、解密验证和普通 RSA 对照。"""

    print("=" * 62)
    print("RSA WIENER ATTACK: LIVE DEMONSTRATION")
    print("=" * 62)
    print(f"数据来源：{source}")
    print()

    print("1) 准备故意使用小私钥指数的 RSA")
    print(f"   n.bit_length() = {weak_key.n.bit_length()}")
    print(f"   public n = {abbreviate(weak_key.n)}")
    print(f"   public e = {abbreviate(weak_key.e)}")
    print("   d、p、q、phi 不传给攻击函数")
    print()

    message_text = "Wiener attack demo"
    message = int.from_bytes(message_text.encode("utf-8"), "big")
    ciphertext = rsa_encrypt(message, weak_key.e, weak_key.n)
    print("2) 生成测试密文")
    print(f"   plaintext = {message_text!r}")
    print(f"   ciphertext = {abbreviate(ciphertext)}")
    print("   攻击者获得的公开数据只有 n、e 和密文")
    print()

    # 【关键演示点】攻击调用只传入公开的 e 和 n。
    result = wiener_attack(weak_key.e, weak_key.n)
    if result is None:
        print("3) 攻击未找到有效 Wiener 候选")
        return False

    factors_ok = result.p * result.q == weak_key.n
    recovered_message = rsa_decrypt(ciphertext, result.d, weak_key.n)
    recovered_text = recovered_message.to_bytes(
        (recovered_message.bit_length() + 7) // 8,
        "big",
    ).decode("utf-8")
    key_ok = result.d == weak_key.d
    decrypt_ok = recovered_message == message

    print("3) 运行 wiener_attack(e, n)")
    print(f"   checked convergents = {result.convergents_checked}")
    print(f"   recovered d = {abbreviate(result.d)}")
    print(f"   p*q == n = {factors_ok}")
    print(f"   attack time = {result.elapsed_s * 1000:.3f} ms")
    print()

    print("4) 使用恢复出的 d 解密")
    print(f"   recovered plaintext = {recovered_text!r}")
    print(f"   recovered d == reference d = {key_ok}")
    print(f"   decryption successful = {decrypt_ok}")
    print()

    print("5) 普通 RSA 对照：使用完全相同的攻击入口")
    normal_result = wiener_attack(normal_key.e, normal_key.n)
    print(f"   normal n.bit_length() = {normal_key.n.bit_length()}")
    print(f"   wiener_attack(e, n) returned None = {normal_result is None}")
    print("   该结果只说明本次 Wiener 攻击未恢复密钥，不是完整安全证明")
    print()

    show_experiment_files()
    print("=" * 62)
    return factors_ok and key_ok and decrypt_ok and normal_result is None


def parse_args() -> argparse.Namespace:
    """解析 fixture 模式和现场生成模式参数。"""

    parser = argparse.ArgumentParser(description="演示 RSA Wiener 攻击")
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--fixture",
        type=Path,
        help="读取指定弱 RSA fixture；不指定参数时使用项目默认 fixture",
    )
    source.add_argument(
        "--generate",
        action="store_true",
        help="现场随机生成 2048-bit 弱密钥和普通密钥",
    )
    return parser.parse_args()


def main() -> int:
    """命令行入口；成功返回 0，演示验证失败返回 1。"""

    args = parse_args()
    if args.generate:
        print("正在现场生成两组 2048-bit RSA 密钥，请稍候……")
        weak_key = generate_weak_rsa(2048, 0.25).key_pair
        normal_key = generate_normal_rsa(2048)
        source = "现场随机生成"
    else:
        weak_path = args.fixture or DEFAULT_WEAK_FIXTURE
        weak_key = load_key_fixture(weak_path)
        normal_key = load_key_fixture(DEFAULT_NORMAL_FIXTURE)
        source = f"已验证 fixture：{weak_path.name}"

    return 0 if run_demo(weak_key, normal_key, source) else 1


if __name__ == "__main__":
    raise SystemExit(main())
