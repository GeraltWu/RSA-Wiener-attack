"""运行设计文档中的 E1、E2、E3 实验并保存真实结果。"""

from __future__ import annotations

import platform
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from statistics import median
from time import perf_counter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.continued_fraction import continued_fraction
from src.experiment_utils import TrialRecord, write_trial_records
from src.rsa import RSAKeyPair, generate_normal_rsa, rsa_decrypt, rsa_encrypt
from src.weak_key_generator import (
    WeakRSAKeyPair,
    approximate_wiener_threshold,
    generate_weak_rsa,
    is_below_wiener_bound,
)
from src.wiener_attack import wiener_attack


RAW_DIR = PROJECT_ROOT / "results" / "raw"
PLOT_DIR = PROJECT_ROOT / "results" / "plots"

# ======================== 可调整实验参数 ========================
# 选择要运行的实验。把不需要运行的实验改为 False。
RUN_E1 = True
RUN_E2 = False
RUN_E3 = False

# 每一个参数组重复运行的次数。正式结果使用 30，快速检查时可以临时改为 2。
TRIALS_PER_GROUP = 30

# E1：固定模数位数，观察不同 d/T 对攻击成功率的影响。
E1_BITS = 512
E1_RATIOS = [
    0.25,
    0.5,
    0.75,
    1.0,
    1.25,
    1.5,
    2.0,
    2.5,
    3.0,
    4.0,
    5.0,
    8.0,
]

# E2：固定 d/T，观察模数位数对攻击时间的影响。
E2_BITS = [256, 512, 1024, 2048]
E2_RATIO = 0.75

# E3：在相同模数位数下比较弱 RSA 和普通 RSA。
E3_BITS = 2048
E3_RATIO = 0.75
# ================================================================


def prepare_output_directories() -> None:
    """创建实验结果目录。"""

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)


def run_attack_trial(
    trial_id: int,
    label: str,
    key_type: str,
    requested_bits: int,
    key: RSAKeyPair,
    keygen_ms: float,
    d_to_threshold: Decimal,
) -> TrialRecord:
    """对一组已经生成的密钥运行攻击并构造统一实验记录。"""

    attack_started = perf_counter()
    # 【关键实验约束】攻击函数只接收公开的 e 和 n。
    result = wiener_attack(key.e, key.n)
    attack_ms = (perf_counter() - attack_started) * 1000

    recovered = result is not None
    if result is None:
        convergents_checked = len(continued_fraction(key.e, key.n))
        verify_ok = key_type == "normal"
    else:
        convergents_checked = result.convergents_checked
        test_message = 42
        decrypted = rsa_decrypt(
            rsa_encrypt(test_message, key.e, key.n),
            result.d,
            key.n,
        )
        verify_ok = (
            result.d == key.d
            and result.p * result.q == key.n
            and decrypted == test_message
        )

    return TrialRecord(
        trial_id=trial_id,
        seed_or_trial_label=label,
        key_type=key_type,
        n_bits=requested_bits,
        actual_n_bits=key.n.bit_length(),
        d_bits=key.d.bit_length(),
        d_to_threshold=d_to_threshold,
        below_wiener_bound=is_below_wiener_bound(key.d, key.n),
        recovered=recovered,
        convergents_checked=convergents_checked,
        keygen_ms=keygen_ms,
        attack_ms=attack_ms,
        verify_ok=verify_ok,
        notes="",
    )


def generate_weak_trial(
    trial_id: int,
    bits: int,
    ratio: float,
    label: str,
) -> TrialRecord:
    """生成弱密钥并运行一次攻击。"""

    generated: WeakRSAKeyPair = generate_weak_rsa(bits, ratio)
    return run_attack_trial(
        trial_id=trial_id,
        label=label,
        key_type="weak",
        requested_bits=bits,
        key=generated.key_pair,
        keygen_ms=generated.generation_elapsed_s * 1000,
        d_to_threshold=(
            Decimal(generated.d) / Decimal(generated.approximate_threshold)
        ),
    )


def generate_normal_trial(trial_id: int, bits: int, label: str) -> TrialRecord:
    """生成普通 RSA 密钥并运行一次相同的攻击。"""

    started = perf_counter()
    key = generate_normal_rsa(bits)
    keygen_ms = (perf_counter() - started) * 1000
    threshold = approximate_wiener_threshold(key.n)
    return run_attack_trial(
        trial_id=trial_id,
        label=label,
        key_type="normal",
        requested_bits=bits,
        key=key,
        keygen_ms=keygen_ms,
        # 2048-bit 普通 RSA 的 d/T 会超过 float 能表示的最大值，
        # 因此使用 Decimal 保存这个实验统计值。
        d_to_threshold=Decimal(key.d) / Decimal(threshold),
    )


def load_plotter():
    """按需加载 matplotlib，并使用不弹出窗口的绘图后端。"""

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def environment_label() -> str:
    """返回适合写入图表的简短运行环境说明。"""

    return f"Python {platform.python_version()}, {platform.system()} {platform.machine()}"


def run_e1(bits: int, ratios: list[float], trials: int) -> list[TrialRecord]:
    """E1：测量不同 d/T 下的 Wiener 攻击成功率。"""

    print(f"\nE1: d/T 与成功率，n={bits} bit，每组 {trials} 次")
    records: list[TrialRecord] = []
    grouped: dict[float, list[TrialRecord]] = defaultdict(list)
    trial_id = 1

    for ratio in ratios:
        for repeat in range(1, trials + 1):
            label = f"E1-ratio-{ratio:g}-trial-{repeat}"
            record = generate_weak_trial(trial_id, bits, ratio, label)
            records.append(record)
            grouped[ratio].append(record)
            trial_id += 1
        successes = sum(item.recovered and item.verify_ok for item in grouped[ratio])
        print(f"  target d/T={ratio:g}: {successes}/{trials} recovered")

    write_trial_records(RAW_DIR / "e1_d_ratio.csv", records)

    rates = [
        100 * sum(item.recovered and item.verify_ok for item in grouped[ratio]) / trials
        for ratio in ratios
    ]
    plt = load_plotter()
    fig, axis = plt.subplots(figsize=(8, 5))
    axis.bar([str(value) for value in ratios], rates, color="#4472C4")
    below_positions = [index for index, value in enumerate(ratios) if value <= 1]
    above_positions = [index for index, value in enumerate(ratios) if value > 1]
    if below_positions and above_positions:
        boundary = (max(below_positions) + min(above_positions)) / 2
        axis.axvline(boundary, color="#C00000", linestyle="--", linewidth=1)
    axis.set_xlabel("Target d/T")
    axis.set_ylabel("Success rate (%)")
    axis.set_ylim(0, 105)
    axis.set_title(f"Wiener Attack Success vs d/T\nMeasured data: {trials} trials/group, {bits}-bit n")
    axis.text(0.01, -0.18, environment_label(), transform=axis.transAxes, fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "wiener_success_vs_d_ratio.png", dpi=180)
    plt.close(fig)
    return records


def run_e2(bit_sizes: list[int], ratio: float, trials: int) -> list[TrialRecord]:
    """E2：测量弱 RSA 模数位数与攻击耗时的关系。"""

    print(f"\nE2: 模数位数与攻击耗时，target d/T={ratio:g}，每组 {trials} 次")
    records: list[TrialRecord] = []
    grouped: dict[int, list[TrialRecord]] = defaultdict(list)
    trial_id = 1

    for bits in bit_sizes:
        for repeat in range(1, trials + 1):
            label = f"E2-{bits}-bit-trial-{repeat}"
            record = generate_weak_trial(trial_id, bits, ratio, label)
            records.append(record)
            grouped[bits].append(record)
            trial_id += 1
        times = [item.attack_ms for item in grouped[bits]]
        successes = sum(item.recovered and item.verify_ok for item in grouped[bits])
        print(f"  {bits} bit: median={median(times):.3f} ms, recovered={successes}/{trials}")

    write_trial_records(RAW_DIR / "e2_modulus_bits.csv", records)

    medians = [median(item.attack_ms for item in grouped[bits]) for bits in bit_sizes]
    minimums = [min(item.attack_ms for item in grouped[bits]) for bits in bit_sizes]
    maximums = [max(item.attack_ms for item in grouped[bits]) for bits in bit_sizes]
    lower_errors = [center - low for center, low in zip(medians, minimums)]
    upper_errors = [high - center for center, high in zip(medians, maximums)]

    plt = load_plotter()
    fig, axis = plt.subplots(figsize=(8, 5))
    axis.errorbar(
        bit_sizes,
        medians,
        yerr=[lower_errors, upper_errors],
        marker="o",
        capsize=4,
        color="#4472C4",
    )
    axis.set_xlabel("RSA modulus size (bits)")
    axis.set_ylabel("Median attack time (ms)")
    axis.set_title(f"Wiener Attack Time vs Modulus Size\nMeasured data: {trials} trials/group")
    axis.grid(alpha=0.3)
    axis.text(0.01, -0.18, environment_label(), transform=axis.transAxes, fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "wiener_time_vs_modulus_bits.png", dpi=180)
    plt.close(fig)
    return records


def run_e3(bits: int, ratio: float, trials: int) -> list[TrialRecord]:
    """E3：比较普通 RSA 与 Wiener 弱 RSA 的攻击结果。"""

    print(f"\nE3: 普通 RSA 与弱 RSA 对照，n={bits} bit，每组 {trials} 次")
    records: list[TrialRecord] = []
    trial_id = 1

    for key_type in ("weak", "normal"):
        for repeat in range(1, trials + 1):
            label = f"E3-{key_type}-trial-{repeat}"
            if key_type == "weak":
                record = generate_weak_trial(trial_id, bits, ratio, label)
            else:
                record = generate_normal_trial(trial_id, bits, label)
            records.append(record)
            trial_id += 1

        group = [item for item in records if item.key_type == key_type]
        successes = sum(item.recovered and item.verify_ok for item in group)
        median_ms = median(item.attack_ms for item in group)
        median_ratio = median(item.d_to_threshold for item in group)
        print(
            f"  {key_type:6s}: recovered={successes}/{trials}, "
            f"median d/T={median_ratio:.3e}, median={median_ms:.3f} ms"
        )

    write_trial_records(RAW_DIR / "weak_vs_normal.csv", records)
    return records


def main() -> int:
    """运行所选实验并把 CSV、PNG 写入 results 目录。"""

    prepare_output_directories()

    started = perf_counter()
    if RUN_E1:
        run_e1(E1_BITS, E1_RATIOS, TRIALS_PER_GROUP)
    if RUN_E2:
        run_e2(E2_BITS, E2_RATIO, TRIALS_PER_GROUP)
    if RUN_E3:
        run_e3(E3_BITS, E3_RATIO, TRIALS_PER_GROUP)

    print(f"\n全部所选实验完成，总耗时 {perf_counter() - started:.2f} s")
    print(f"CSV: {RAW_DIR}")
    print(f"Plots: {PLOT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
