# Code Authorship 与 AI 使用声明

## 重要说明

源码中的“自己实现”标记只用于指定的 8 个函数，表示这些函数是项目需要负责
实现和讲解的部分。该标记不代表代码已经可以被声明为学生独立原创。

当前仓库版本由 Codex 协助生成和修改，包括核心函数初稿、中文注释、测试、演示
脚本、实验脚本和文档。因此最终提交时不能写成“完全没有使用 AI”。两位成员应
根据真实的修改过程、Git commits、测试工作和讲解能力填写实际贡献。

## 需要填写实际作者的部分

| 函数或组件 | 为什么属于核心 | 实际学生作者 | AI 辅助方式 | 能否独立解释与测试 |
|---|---|---|---|---|
| `generate_normal_rsa` | 普通密钥生成 | 待如实填写 | Codex 提供当前初稿和测试 | Yes / No |
| `generate_weak_rsa` | 弱参数构造 | 待如实填写 | Codex 提供当前初稿和整数边界判断 | Yes / No |
| `_nearest_odd_coprime` | 寻找合法的小私钥指数 | 待如实填写 | Codex 提供当前初稿和注释 | Yes / No |
| `approximate_wiener_threshold` | 计算 Wiener 边界近似值 | 待如实填写 | Codex 提供当前初稿和注释 | Yes / No |
| `is_below_wiener_bound` | 判断是否低于 Wiener 边界 | 待如实填写 | Codex 提供当前初稿和测试 | Yes / No |
| `continued_fraction` | 计算连分数系数 | 待如实填写 | Codex 提供当前初稿和样例测试 | Yes / No |
| `convergents` | 计算渐近分数 | 待如实填写 | Codex 提供当前初稿和样例测试 | Yes / No |
| `wiener_attack` | 项目核心攻击 | 待如实填写 | Codex 提供当前初稿、验证逻辑和测试 | Yes / No |

## 不应声明为自行实现的库功能

- math.gcd 的最大公约数实现。
- Python pow 的模幂和模逆实现，包括 `pow(value, -1, modulus)`。
- math.isqrt 的精确整数平方根实现。
- PyCryptodome 的 getPrime 素数生成与内部素性检测。
- CSV、argparse、dataclass、计时等标准库功能。
- matplotlib 的绘图功能。

可以说明“我们调用了这些库”，但不能把库内部算法列为自己的实现贡献。

## 推荐的真实声明措辞

> We implemented and tested the RSA key-generation flow, continued-fraction
> candidate construction, and Wiener candidate validation in Python. Codex was
> used to assist with initial code drafting, Chinese comments, test cases,
> experiment scripting, and documentation. We reviewed the mathematical steps,
> reran the tests and experiments, and can explain the submitted implementation.

只有在两位成员确实完成审阅、测试并能解释时，才能使用最后一句。若成员重新实现
了某些函数，应在表格中按真实情况写明，并用 Git commits 支撑。

## 提交前检查

- 每个核心函数是否有明确的实际负责人？
- 负责人能否不用看稿解释输入、输出、循环和失败分支？
- 是否保留了测试记录和 Git commits？
- 是否如实说明 Codex 参与了哪些工作？
- 是否避免使用“完全独立原创”之类与事实不符的表述？
