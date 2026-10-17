# RSA Wiener Attack

本项目实现针对小私钥指数 RSA 的 Wiener 连分数攻击。攻击函数只接收公开的
e 和 n，并通过精确整数运算恢复和验证 d、p、q。

项目中的弱密钥是故意生成的教学样本。成功攻击 2048-bit 弱 RSA，并不表示
正常生成的 2048-bit RSA 可以被普遍破解。

## 目录

- `src/rsa.py`：RSA 密钥生成及整数加解密。
- `src/weak_key_generator.py`：生成私钥指数 d 很小但数学上合法的 RSA 密钥。
- `src/continued_fraction.py`：连分数与渐近分数。
- `src/wiener_attack.py`：只使用 e、n 的 Wiener 攻击。
- `src/experiment_utils.py`：实验记录、CSV 和统计。
- `scripts/demo.py`：现场演示。
- `scripts/run_experiments.py`：运行 E1、E2、E3 并生成 CSV、PNG。
- `tests/`：自动化测试。
- `docs/CODE_EXPLANATION.md`：代码讲解。
- `docs/DEMO_GUIDE.md`：演示步骤和讲稿。
- `docs/PRESENTATION_SCRIPT_CN.md`：8 分钟 Presentation 中文内容与讲解稿。
- `docs/PRESENTATION_SCRIPT_EN.md`：8 分钟 Presentation 英文内容与讲解稿。
- `docs/CODE_AUTHORSHIP_AND_AI_USE.md`：作者与 AI 使用声明模板。
- `docs/EXPERIMENT_RESULTS.md`：当前完整实验结果和限制。

## 环境与运行

项目使用 `common` 环境中的 Python 3.11。素数生成使用 PyCryptodome，测试可使用
标准库 unittest 或 pytest，绘图使用 matplotlib。

```powershell
conda activate common
python -m pip install -r requirements.txt
python -B -m unittest discover -s tests -v
python -m pytest -q
python -B scripts/demo.py
python -B scripts/run_experiments.py
```

如果不激活环境，也可使用：

```powershell
conda run --no-capture-output -n common python -B scripts/run_experiments.py
```

## 演示模式

默认现场随机生成一组弱 RSA 和一组普通 RSA：

```powershell
python -B scripts/demo.py
```

Demo 默认显示 RSA 参数位数与缩写值、连分数摘要、成功候选的恢复过程以及各阶段
用时。如需展开完整内容：

```powershell
# 显示 n、e、d、p、q、phi 等完整大整数
python -B scripts/demo.py --full-values

# 显示 e/n 的完整连分数系数列表
python -B scripts/demo.py --full-coefficients
```

完整模式会产生很长的终端输出，正式演示建议使用默认摘要模式。

## 实验输出

完整实验会生成：

- `results/raw/e1_d_ratio.csv`
- `results/raw/e2_modulus_bits.csv`
- `results/raw/weak_vs_normal.csv`
- `results/plots/wiener_success_vs_d_ratio.png`
- `results/plots/wiener_time_vs_modulus_bits.png`

实验参数集中在 `scripts/run_experiments.py` 顶部的“可调整实验参数”区域。可以直接
修改要运行的实验、每组次数、模数位数和 d/T。当前正式配置每组运行 30 次；如果
只想快速检查流程，可临时把 `TRIALS_PER_GROUP` 改为 2，并按需关闭 E1、E2 或 E3。
E3 与 Demo 均默认使用 2048-bit 模数；E2、E3 和 Demo 的弱密钥使用 d/T≈0.75。
提交或汇报时应恢复正式参数并重新运行，以最终生成的 CSV 和图片为准。

## 安全边界

- RSA 整数加解密函数没有实现 OAEP 等安全填充，只用于本项目的数学验证。
- 超出 Wiener 经典边界不代表密钥一定安全，只表示经典定理不再保证成功。
- Wiener 攻击返回 None 不构成完整的 RSA 安全证明。

## 作者与 AI 使用

代码中的“此部分为自己实现”标记用于区分项目编写的逻辑和直接调用的库功能；
“库功能”标记表示不能把库内部算法算作自己的实现。标记不等于独立原创证明。
当前版本使用了 Codex 辅助，最终声明应按照真实修改、测试和 Git 记录填写，详见
`docs/CODE_AUTHORSHIP_AND_AI_USE.md`。
