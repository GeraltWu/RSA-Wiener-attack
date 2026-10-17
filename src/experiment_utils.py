"""供后续实验共用的记录、CSV 输出和统计辅助函数。"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Iterable


@dataclass(frozen=True)
class TrialRecord:
    """按照设计文档规定的字段保存一次实验记录。"""

    trial_id: int
    seed_or_trial_label: str
    key_type: str
    n_bits: int
    actual_n_bits: int
    d_bits: int
    d_to_threshold: Decimal
    below_wiener_bound: bool
    recovered: bool
    convergents_checked: int
    keygen_ms: float
    attack_ms: float
    verify_ok: bool
    notes: str = ""


@dataclass(frozen=True)
class TrialSummary:
    """保存一组非空实验记录的基础汇总统计量。"""

    trials: int
    successes: int
    success_rate: float
    mean_attack_ms: float
    median_attack_ms: float
    min_attack_ms: float
    max_attack_ms: float


def write_trial_records(path: str | Path, records: Iterable[TrialRecord]) -> None:
    """把实验记录写入 CSV，每条记录占一行。

    父目录必须已经存在。要求调用者显式创建目录，可以防止此辅助函数在
    未经注意的情况下改变更多文件系统状态。
    """

    destination = Path(path)
    fieldnames = list(TrialRecord.__dataclass_fields__)

    with destination.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def summarize_trials(records: Iterable[TrialRecord]) -> TrialSummary:
    """计算实验记录的成功率和攻击耗时统计量。"""

    materialized = list(records)
    if not materialized:
        raise ValueError("至少需要一条实验记录")

    attack_times = [record.attack_ms for record in materialized]
    successes = sum(record.recovered and record.verify_ok for record in materialized)
    return TrialSummary(
        trials=len(materialized),
        successes=successes,
        success_rate=successes / len(materialized),
        mean_attack_ms=sum(attack_times) / len(attack_times),
        median_attack_ms=median(attack_times),
        min_attack_ms=min(attack_times),
        max_attack_ms=max(attack_times),
    )
