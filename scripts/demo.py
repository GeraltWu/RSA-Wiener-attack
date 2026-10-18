"""一条命令完成 Wiener 攻击现场演示。"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from math import isqrt
from pathlib import Path
from time import perf_counter


# 直接运行 python scripts/demo.py 时，需要把项目根目录加入模块搜索路径。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.continued_fraction import continued_fraction, convergents
from src.rsa import RSAKeyPair, generate_normal_rsa, rsa_decrypt, rsa_encrypt
from src.weak_key_generator import (
    approximate_wiener_threshold,
    generate_weak_rsa,
    is_below_wiener_bound,
)
from src.wiener_attack import wiener_attack


def abbreviate(value: int, digits: int = 16) -> str:
    """缩写大整数，只展示十进制开头和结尾。"""

    text = str(value)
    if len(text) <= digits * 2:
        return text
    return f"{text[:digits]}...{text[-digits:]}"


def display_integer(value: int, full_values: bool) -> str:
    """根据演示选项返回完整整数或缩写整数。"""

    return str(value) if full_values else abbreviate(value)


def display_coefficients(values: list[int], full_values: bool) -> str:
    """格式化连分数系数，避免单个巨大系数撑满终端。"""

    if full_values:
        return str(values)
    displayed = [abbreviate(value, digits=8) for value in values]
    return f"[{', '.join(displayed)}]"


def print_key_parameters(
    title: str,
    key: RSAKeyPair,
    full_values: bool,
    show_validation: bool = True,
) -> None:
    """按统一格式打印 RSA 参数，方便比较弱密钥和普通密钥。"""

    print(title)
    print(f"   n   ({key.n.bit_length():4d} bit) = {display_integer(key.n, full_values)}")
    print(f"   e   ({key.e.bit_length():4d} bit) = {display_integer(key.e, full_values)}")
    print(f"   d   ({key.d.bit_length():4d} bit) = {display_integer(key.d, full_values)}")
    print(f"   p   ({key.p.bit_length():4d} bit) = {display_integer(key.p, full_values)}")
    print(f"   q   ({key.q.bit_length():4d} bit) = {display_integer(key.q, full_values)}")
    print(f"   phi ({key.phi.bit_length():4d} bit) = {display_integer(key.phi, full_values)}")
    if show_validation:
        print(f"   p*q == n               = {key.p * key.q == key.n}")
        print(f"   e*d mod phi == 1       = {(key.e * key.d) % key.phi == 1}")


def calculate_continued_fraction(
    label: str,
    e: int,
    n: int,
    full_coefficients: bool,
) -> list[int]:
    """计算连分数并打印适合现场展示的系数摘要。"""

    coefficients = continued_fraction(e, n)

    print(f"   {label} coefficient count = {len(coefficients)}")
    if full_coefficients or len(coefficients) <= 20:
        print(
            f"   {label} coefficients = "
            f"{display_coefficients(coefficients, full_coefficients)}"
        )
    else:
        first_values = [abbreviate(value, digits=8) for value in coefficients[:12]]
        last_values = [abbreviate(value, digits=8) for value in coefficients[-5:]]
        summary = ", ".join(first_values + ["..."] + last_values)
        print(f"   {label} coefficients = [{summary}]")
    return coefficients


def run_demo(
    weak_key: RSAKeyPair,
    normal_key: RSAKeyPair,
    source: str,
    preparation_ms: float,
    full_values: bool,
    full_coefficients: bool,
) -> bool:
    """执行弱密钥攻击、逐步恢复展示和普通 RSA 对照。"""

    print("=" * 76)
    print("RSA WIENER ATTACK: LIVE DEMONSTRATION")
    print("=" * 76)
    print(f"Data source: {source}")
    print(f"Key generation time: {preparation_ms:.3f} ms")
    # print("Large integers are abbreviated; all calculations use full values.")
    print()

    print("1) Weak RSA parameters (reference values)")
    print_key_parameters("   RSA with intentionally small d:", weak_key, full_values)
    weak_threshold = approximate_wiener_threshold(weak_key.n)
    print(f"   Wiener threshold T = {display_integer(weak_threshold, full_values)}")
    print(f"   d/T                 = {weak_key.d / weak_threshold:.6f}")
    print(
        "   d < n^(1/4)/3       = "
        f"{is_below_wiener_bound(weak_key.d, weak_key.n)}"
    )
    print("   Reference values d, p, q, and phi are not passed to the attack.")
    print("   The attack receives only the public e and n.")
    print()

    print("2) Encrypt a test message with the weak RSA key")
    message_text = "Wiener attack demo"
    message = int.from_bytes(message_text.encode("utf-8"), "big")
    encrypt_started = perf_counter()
    ciphertext = rsa_encrypt(message, weak_key.e, weak_key.n)
    weak_encrypt_ms = (perf_counter() - encrypt_started) * 1000
    print(f"   plaintext text    = {message_text!r}")
    print(f"   plaintext integer = {message}")
    print(f"   ciphertext        = {display_integer(ciphertext, full_values)}")
    print(f"   encryption time   = {weak_encrypt_ms:.3f} ms")
    print()

    print("3) Attacker view: compute the continued fraction of e/n")
    weak_coefficients = calculate_continued_fraction(
        "weak RSA",
        weak_key.e,
        weak_key.n,
        full_coefficients,
    )
    print()

    print("4) Test convergents and recover the private parameters")
    attack_started = perf_counter()
    # 【关键演示点】攻击调用只传入公开的 e 和 n。
    result = wiener_attack(weak_key.e, weak_key.n)
    weak_attack_ms = (perf_counter() - attack_started) * 1000
    if result is None:
        print("   No valid Wiener candidate was found.")
        return False

    # 找到攻击成功时所对应的渐近分数 k/d，展示候选验证链条。
    successful_k, successful_d = next(
        candidate
        for index, candidate in enumerate(convergents(weak_coefficients))
        if index == result.candidate_index
    )
    recovered_phi = (weak_key.e * successful_d - 1) // successful_k
    factor_sum = weak_key.n - recovered_phi + 1
    discriminant = factor_sum * factor_sum - 4 * weak_key.n
    discriminant_root = isqrt(discriminant)

    nearby_start = max(0, result.candidate_index - 4)
    nearby_coefficients = weak_coefficients[
        nearby_start : result.candidate_index + 1
    ]
    print(
        "   successful candidate       = "
        f"No. {result.convergents_checked} (zero-based index {result.candidate_index})"
    )
    print(
        f"   coefficients a[{nearby_start}:{result.candidate_index + 1}] "
        f"= {display_coefficients(nearby_coefficients, full_coefficients)}"
    )
    print(f"   successful k               = {display_integer(successful_k, full_values)}")
    print(f"   successful candidate d     = {display_integer(successful_d, full_values)}")
    print(f"   e*d-1 divisible by k       = {(weak_key.e * successful_d - 1) % successful_k == 0}")
    print(f"   recovered phi=(e*d-1)/k    = {display_integer(recovered_phi, full_values)}")
    print(f"   recovered p+q=n-phi+1      = {display_integer(factor_sum, full_values)}")
    print(f"   discriminant=(p+q)^2-4n    = {display_integer(discriminant, full_values)}")
    print(f"   sqrt(discriminant)=|p-q|   = {display_integer(discriminant_root, full_values)}")
    print(f"   recovered p                = {display_integer(result.p, full_values)}")
    print(f"   recovered q                = {display_integer(result.q, full_values)}")
    print(f"   recovered d                = {display_integer(result.d, full_values)}")
    print(f"   recovered phi == reference = {recovered_phi == weak_key.phi}")
    print(f"   recovered p*q == n         = {result.p * result.q == weak_key.n}")
    print(f"   recovered d == reference   = {result.d == weak_key.d}")
    print(f"   attack time                 = {weak_attack_ms:.3f} ms")
    print()

    print("5) Decrypt using the recovered d")
    decrypt_started = perf_counter()
    recovered_message = rsa_decrypt(ciphertext, result.d, weak_key.n)
    weak_decrypt_ms = (perf_counter() - decrypt_started) * 1000
    recovered_text = recovered_message.to_bytes(
        (recovered_message.bit_length() + 7) // 8,
        "big",
    ).decode("utf-8")
    decrypt_ok = recovered_message == message
    print(f"   recovered integer   = {recovered_message}")
    print(f"   recovered plaintext = {recovered_text!r}")
    print(f"   decryption successful = {decrypt_ok}")
    print(f"   decryption time       = {weak_decrypt_ms:.3f} ms")
    print()

    print("6) Normal RSA control")
    print("   6.1 Normal RSA parameter generation")
    print_key_parameters(
        "   Generated normal RSA parameters:",
        normal_key,
        full_values,
        show_validation=False,
    )
    normal_threshold = approximate_wiener_threshold(normal_key.n)
    normal_ratio = Decimal(normal_key.d) / Decimal(normal_threshold)
    print(f"   d/T                     = {normal_ratio:.3E}")
    print(
        "   d < n^(1/4)/3           = "
        f"{is_below_wiener_bound(normal_key.d, normal_key.n)}"
    )

    print()
    print("   6.2 Run the same wiener_attack(e, n)")
    calculate_continued_fraction(
        "normal RSA",
        normal_key.e,
        normal_key.n,
        full_coefficients,
    )
    print("   (With the 17-bit e=65537, e/n usually has a short continued fraction.)")
    normal_attack_started = perf_counter()
    normal_result = wiener_attack(normal_key.e, normal_key.n)
    normal_attack_ms = (perf_counter() - normal_attack_started) * 1000
    print(f"   wiener_attack returned None = {normal_result is None}")
    print(f"   attack time               = {normal_attack_ms:.3f} ms")
    #print("   None means this attack did not recover the key; it is not a complete security proof.")
    print()

    print("=" * 76)
    return (
        result.p * result.q == weak_key.n
        and result.d == weak_key.d
        and recovered_phi == weak_key.phi
        and decrypt_ok
        and normal_result is None
    )


def parse_args() -> argparse.Namespace:
    """解析控制大整数和连分数显示长度的参数。"""

    parser = argparse.ArgumentParser(description="Demonstrate the RSA Wiener attack")
    parser.add_argument(
        "--full-values",
        action="store_true",
        help="print the complete decimal values of n, e, d, p, q, and phi",
    )
    parser.add_argument(
        "--full-coefficients",
        action="store_true",
        help="print the complete continued-fraction coefficient list for e/n",
    )
    return parser.parse_args()


def main() -> int:
    """命令行入口；成功返回 0，演示验证失败返回 1。"""

    args = parse_args()
    preparation_started = perf_counter()
    weak_key = generate_weak_rsa(2048, 0.75).key_pair
    normal_key = generate_normal_rsa(2048)
    source = "two 2048-bit RSA keys generated randomly during this run"

    preparation_ms = (perf_counter() - preparation_started) * 1000
    success = run_demo(
        weak_key,
        normal_key,
        source,
        preparation_ms,
        args.full_values,
        args.full_coefficients,
    )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
