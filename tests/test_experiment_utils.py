"""测试可写入 CSV 的实验记录和汇总统计。"""

import unittest
from pathlib import Path

from src.experiment_utils import TrialRecord, summarize_trials, write_trial_records


class ExperimentUtilsTests(unittest.TestCase):
    def test_summary_and_csv_header(self) -> None:
        records = [
            TrialRecord(1, "a", "weak", 64, 64, 7, 0.5, True, True, 6, 1.0, 0.2, True),
            TrialRecord(2, "b", "normal", 64, 64, 60, 100.0, False, False, 20, 1.2, 0.4, True),
        ]
        summary = summarize_trials(records)
        self.assertEqual(summary.successes, 1)
        self.assertEqual(summary.success_rate, 0.5)
        self.assertAlmostEqual(summary.mean_attack_ms, 0.3)

        # 使用已经可写的 tests 目录。某些 Windows/OneDrive 组合会给新建的
        # 临时目录设置过于严格的访问权限。
        path = Path(__file__).with_name("_temporary_trials.csv")
        self.addCleanup(lambda: path.exists() and path.unlink())
        write_trial_records(path, records)
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].startswith("trial_id,seed_or_trial_label,key_type"))

    def test_empty_summary_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            summarize_trials([])


if __name__ == "__main__":
    unittest.main()
