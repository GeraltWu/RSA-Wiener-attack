# SC6104 Cryptography Mini Project 设计文档

> **项目**：Implementation and Experimental Analysis of Wiener's Attack on RSA with Small Private Exponents  
> **中文**：RSA 小私钥指数漏洞：Wiener 攻击实现与实验分析  
> **项目形式**：2 人小组；Python 3.11+；命令行 Demo；目标为可复现实验和 6 分钟展示  
> **版本**：v1.2 / 2026-10-11  
> **状态**：拟定实施方案（非已完成的实验报告）

## 0. 一页摘要：最终要做什么

**研究问题**：当 RSA 的私钥指数 $d$ 错误地选择得过小时，攻击者能否只凭公开的 $(n,e)$ 恢复私钥？这种攻击是否仍然适用于 **2048-bit 的弱 RSA 模数**？

最终交付一套可以运行的 Python 程序：

1. **自己实现 RSA 的核心数学流程**：素数生成/素性检测、扩展欧几里得、模逆、RSA 公私钥生成和测试消息的模幂加解密。
2. **自己构造故意有漏洞的 RSA 参数**：用大小相近的素数 $p,q$ 构造 $n=pq$，选取非常小而且与 $\varphi(n)$ 互素的 $d$，再令 $e=d^{-1}\pmod{\varphi(n)}$。
3. **自己实现 Wiener Attack**：计算 $\frac{e}{n}$ 的连分数及渐近分数 $(k,d)$，验证候选参数并恢复真正的私钥指数，不向攻击函数提供 $p,q,\varphi(n),d$。
4. **通过完整 Demo 验证漏洞**：仅输出 $(n,e)$ 给攻击端；恢复 $d$；用恢复私钥解密预先加密的测试整数；对正常参数给出“未恢复”的对照结果。
5. **做实验与分析**：比较不同 $n$ 位数（如 256/512/1024/2048）、不同 $d$ 与 Wiener 理论边界的比例、攻击成功率和耗时，并做必要的重复与图表。
6. **做 PPT 和答辩**：6 分钟介绍+现场 Demo，2 分钟 Q&A；如实陈述自己写的关键代码和 AI 辅助范围。

**不做**：不开发网页、GUI、数据库；不尝试破解正常配置的 2048-bit RSA；不承诺发明新攻击；不把现成 Wiener 攻击库直接作为项目核心实现。

---

## 1. 数学基础和关键术语

### 1.1 正常 RSA

选择两个不同且大小相近的大素数 $p,q$：

```text
n   = p * q
phi = (p - 1) * (q - 1)
choose e with gcd(e, phi) = 1
d   = inverse_mod(e, phi)
public key = (n, e)
private exponent = d
ciphertext = pow(message, e, n)
plaintext  = pow(ciphertext, d, n)
```

普通 RSA 的重要性质是 $ed\equiv1\pmod{\varphi(n)}$。对于本课程的数学演示，直接对整数做模幂即可；**这叫 textbook RSA，不是可以直接部署在产品里的安全加密方案**。实际 RSA 加密应使用经过标准化的安全填充方案（如 OAEP）。

### 1.2 Wiener 的切入点

因为 $ed\equiv1\pmod{\varphi(n)}$，存在整数 $k$，使得：

$$
ed-k\varphi(n)=1.
$$

故：

$$
\frac{k}{d}=\frac{e}{\varphi(n)}-\frac{1}{d\varphi(n)}.
$$

当 RSA 素数大小接近时，$\varphi(n)=n-(p+q)+1$ 接近 $n$。在经典 Wiener 定理的参数假设下，如果私钥指数特别小，$\frac{k}{d}$ 会是 $\frac{e}{n}$ 的某个 **convergent（渐近分数）**。课件给出的经典小指数阈值为：

$$
d<\frac{1}{3}n^{1/4}.
$$

**边界解释（很重要）**：这是满足有关素数比例等条件下的理论保证，不是对任意形状的 RSA 模数都无条件成立；超出阈值时，Wiener 攻击**不保证**成功，并不等于必定失败。实验中必须记录事实结果，不要预先把超阈值样本标成“必定失败”。

### 1.3 连分数和渐近分数

对整数 `e,n` 做欧几里得除法，可以得到有理数 $\frac{e}{n}$ 的连分数系数：

$$
\frac en=[a_0;a_1,a_2,\ldots,a_t].
$$

用递推产生渐近分数 `P_i/Q_i`：

$$
P_i=a_iP_{i-1}+P_{i-2},\quad Q_i=a_iQ_{i-1}+Q_{i-2}
$$

初值：`P[-2]=0, P[-1]=1, Q[-2]=1, Q[-1]=0`。在攻击流程中，把每个 `P_i/Q_i` 当成候选 $\frac{k}{d}$，但**必须严格验证**，而不能只把分母直接当作已恢复的私钥。

### 1.4 私钥候选验证：不能省略的环节

给定候选 $(k,d)$：

1. 若 `k == 0`，跳过。
2. 检查 `(e*d - 1) % k == 0`；否则跳过。
3. 令 `phi_candidate = (e*d - 1) // k`。
4. 由 `p+q = n - phi_candidate + 1`，记 `s = n - phi_candidate + 1`。
5. 计算 `delta = s*s - 4*n`。
6. 要求 `delta >= 0` 且 `isqrt(delta)^2 == delta`。
7. 要求 `s ± isqrt(delta)` 均为偶数，令 `p = (s+sqrt_delta)//2, q = (s-sqrt_delta)//2`。
8. 要求 `p > 1, q > 1, p*q == n`；按需要检查素性及 `e*d % phi_candidate == 1`。
9. **全部检查通过**才返回 `(d,p,q)`；遍历完则返回 `None`。

用 `math.isqrt` 进行**精确整数**平方根检验。**不要**用浮点 `sqrt` 处理 2048-bit 整数，否则会产生精度错误。

### 1.5 规模定义

- **2048-bit RSA** 指的是 `n.bit_length() == 2048`，并非 $d$ 为 2048 bit。
- 应生成大小相近、独立的约 1024-bit $p,q$，然后检查 `n.bit_length()`；必要时重试。
- **2048-bit 且 weak $d$ 可以被 Wiener 攻击**，并不意味着正常 2048-bit RSA 被普遍破解。
- 真实规模指模数位数接近实际部署标准；“弱参数”是本项目人为构造的安全问题。

---

## 2. 代码架构与函数接口（学生需要亲自实现）

建议目录：

```text
rsa-wiener-project/
├── README.md
├── requirements.txt                 # matplotlib（如需绘图）、pytest（可选）
├── src/
│   ├── number_theory.py            #  gcd / extended_gcd / inverse / primality
│   ├── rsa.py                      #  RSA 数学模块、生成正常密钥
│   ├── weak_key_generator.py       #  小 d 的有效 RSA 密钥
│   ├── continued_fraction.py       #  CF 系数 / convergents
│   ├── wiener_attack.py            #  攻击及精确验证
│   └── experiment_utils.py         # 共同：统计/输出
├── scripts/
│   ├── demo.py                     # 共同：一键演示
│   └── run_experiments.py          # 共同：批量实验
├── tests/
│   ├── test_rsa.py
│   ├── test_fractions.py
│   └── test_attack.py
├── results/
│   ├── raw/                        # 各 trial 的 CSV
│   └── plots/                      # PNG 图表
└── slides/                          # presentation；不一定要提交源码之外的文件
```

以下是**实现规格、算法步骤和测试预期**，不是替你们生成所有最终代码。根据老师的要求，实际编写核心代码的学生应记录开发过程，并能现场逐行解释。

### 2.1 数论函数 `number_theory.py`

| 函数签名建议 | 输入 | 输出 | 自己实现的算法 |
|---|---|---|---|
| `gcd(a: int,b: int)->int` | 任意整数 | 非负 GCD | Euclidean Algorithm，循环取余 |
| `extended_gcd(a,b)->tuple[g,x,y]` | 整数 | `a*x+b*y=g` | 扩展欧几里得 |
| `mod_inverse(a,m)->int` | `gcd(a,m)=1` | 规范化模逆 `[0,m-1]` | 从 `extended_gcd` 提取系数 |
| `is_probable_prime(n, rounds=...) -> bool` | 大整数 | bool | 建议亲自实现 Miller–Rabin；教学实现要说明概率性与轮数 |
| `generate_prime(bits, rng) -> int` | 指定位数 | 候选大素数 | 安全随机候选+素性检测 |

建议采用标准库 `secrets` 生成用于生成候选素数的随机比特；`random` 不适合作为真正密钥生成的 CSPRNG。此处虽然故意构造不安全 $d$，也不要将“弱 RNG”引入为第二个混杂漏洞。可用 `int.bit_length()` 检查位数，筛除偶数、小素数倍数以提高速度。

**验收测试**：`gcd(54,24)=6`；`mod_inverse(17,3120)=2753`；互素失败时抛异常；预期返回素数的长度正确且通过独立验证；`extended_gcd` 恒满足 Bézout 等式。

### 2.2 `rsa.py` 与 `weak_key_generator.py`

**普通密钥生成** `generate_normal_rsa(bits)`：

1. 生成不同的、大小接近的 $p$ 和 $q$；若 `n.bit_length()!=bits` 则重试。
2. `phi=(p-1)*(q-1)`。
3. 优先尝试 `e=65537`；若 `gcd(e,phi)!=1`，重采样 $p,q$。
4. 求 `d=mod_inverse(e,phi)`。
5. 返回结构化数据（公开字段 `n,e`；私有字段 `p,q,d,phi`），演示时不要把秘密字段泄露给 attack 函数。

**弱密钥生成** `generate_weak_rsa(bits, d_target_ratio)`：

1. 生成不同、约等长的素数 $p,q$；计算 `n,phi`。
2. 使用目标比例 `r` 设置 `target ≈ r * T`，其中 `T = n^(1/4)/3` 是课程使用的理论标尺。
3. 寻找**奇数**候选 `d>1`，满足 `gcd(d,phi)==1`、大小接近 target；为什么 d 需奇数？$\varphi(n)$ 对奇素数必为偶数。
4. 计算 `e = mod_inverse(d,phi)`；要求 `1<e<phi` 且 `e*d % phi == 1`。
5. 记录 `n.bit_length()`、`d.bit_length()`、`d/T`、公私钥、生成耗时；弱密钥只在本地教学环境使用。

**避免浮点溢出/失准**：2048-bit 的 $n$ 不能先转 `float` 再直接求 `n**0.25`。建议用整数方法判断阈值：比较 `81*d^4 < n`，等价于 `d < n^(1/4)/3`（$d$ 为正整数）；构造目标 $d$ 可以用 `math.isqrt(math.isqrt(n)) // 3` 作为近似标尺并报告近似误差。对精确条件采用整数四次幂比较。

**加密/解密函数**：`rsa_encrypt(m,e,n)` 与 `rsa_decrypt(c,d,n)` 使用 Python `pow(x, exponent, modulus)` 完成高效模幂；有效消息是 `0 <= m < n`。这只用于教学整数，不宣称是安全生产级 RSA 加密。

**验收测试**：

- 教学样例 `p=61,q=53,e=17 -> n=3233,phi=3120,d=2753`，`m=65 -> c=2790 -> m=65`。
- 普通和弱密钥都满足 $pq=n$、`gcd(e,phi)=1`、`(e*d)%phi==1`；正确生成时 `p != q`。
- `n.bit_length()` 满足请求（如 512/1024/2048）。
- 同一函数对多组随机测试消息满足 `decrypt(encrypt(m))==m`。

### 2.3 `continued_fraction.py`

函数 A：`continued_fraction(numerator, denominator) -> list[int]`

- `denominator > 0`；执行欧几里得除法：每轮记录 `quotient = a // b`，然后 `(a,b)=(b,a%b)`，到 `b==0` 结束。
- 只用整数运算，不计算浮点 $\frac{e}{n}$。
- 示例 `43/19 -> [2,3,1,4]`。

函数 B：`convergents(coefficients) -> iterator[tuple[int,int]]`

- 初值：`p_prev2=0,p_prev1=1,q_prev2=1,q_prev1=0`。
- 遍历系数 `a`：`p=a*p_prev1+p_prev2`、`q=a*q_prev1+q_prev2`。
- 产生 `(p,q)` 并更新状态。
- 示例 `[2,3,1,4] -> (2,1),(7,3),(9,4),(43,19)`。
- 单元测试还应包括 `e<n`（首项为 0）、长度为 1 的连分数、输入分子/分母互素与不互素的情形。

### 2.4 `wiener_attack.py`

建议接口：

```text
wiener_attack(e: int, n: int) -> Optional[AttackResult]
AttackResult = {d, p, q, candidate_index, convergents_checked, elapsed_s}
```

**伪代码（作为实现依据，不是最终可提交的核心源码）**：

```text
assert 1 < e < n and n > 1
coefficients ← continued_fraction(e, n)
for (index, (k, d)) in enumerate(convergents(coefficients)):
    if k == 0 or (e*d - 1) mod k != 0:
        continue
    phi ← (e*d - 1) // k
    s ← n - phi + 1
    delta ← s*s - 4*n
    if delta < 0:
        continue
    root ← integer_sqrt(delta)
    if root*root != delta or (s+root) odd or (s-root) odd:
        continue
    p ← (s+root)//2
    q ← (s-root)//2
    if p>1 and q>1 and p*q==n and e*d mod phi==1:
        return recovered key + diagnostics
return None
```

**核心设计原则**：攻击只输入 $(e,n)$，不传入真实 `d,p,q,phi`；真实值只由测试模块留存，以验证“是否恢复正确”。

**重要边界测试**：

- 已知易攻击的小型 RSA 测试向量应成功，返回 $d$、$p$、$q$ 均正确。
- 课程示例的小 `d=37` 可以作为人工核验点（需从对应课件完整读取其 $(e,n)$，不可捏造）。
- 随机正常私钥、已知不满足攻击条件的 RSA 样本，大多返回 `None`；**不要**把“返回 None”解读为一般 RSA 的安全证明。
- 所有计算必须使用精确整数，避免 float。

### 2.5 测试与工程质量

- 用 `pytest` 或标准库 `unittest`；每个核心函数至少包括正常样例+异常或边界样例。
- 使用 type hints 和 docstrings 写清输入/输出/数学前提。
- 生成过程和攻击过程分离；攻击模块不得导入弱密钥生成器以读取秘密变量。
- 对实验数据使用 CSV，一行对应一次 trial，原始数据可复现。
- 把用于实验的参数、Python 版本、机器 CPU/系统、依赖版本写在 `README.md`。
- 如果使用 AI 辅助理解概念、找 bug 或画图，**必须如实记录**，不要对老师宣称 AI 写的函数是自己原创。

---

## 3. 实验设计（研究问题、变量、样本、统计、图表）

### 3.1 实验前统一约定

**因变量**：`attack_success`（准确恢复真实 $d$ 且 $pq=n$）、`elapsed_attack_ms`、`convergents_checked`、`keygen_time_ms`。**自变量**：`n_bits`、`d/T`（私钥大小相对于理论阈值）、密钥类型（weak / normal）。

记录每次 trial 的 CSV 列：

```text
trial_id, seed_or_trial_label, key_type, n_bits, actual_n_bits,
d_bits, d_to_threshold, below_wiener_bound, recovered,
convergents_checked, keygen_ms, attack_ms, verify_ok, notes
```

- `seed_or_trial_label` 只是标识；若用 `secrets`，不要假装能够完全确定性重现同一随机密钥，可将**用于教学复现的固定公钥测试向量**另存为本地 fixtures。
- 运行计时用 `time.perf_counter()`，**把密钥生成耗时和攻击耗时分开**。
- 对每组做多次 trial，最少先 10 次确认程序稳定，再视时间提高到 30–50 次；取平均值、median、范围，必要时给标准差。
- 关键检查：密钥生成程序是合法 RSA、只修改指定弱点；不要把生成失败计入攻击失败。
- 详细实验图标注 $n$ 位数、机器环境、样本数、单位、弱 $d$ 的条件。

### 3.2 实验 E1：私钥指数大小 vs 攻击成功率（最有解释力）

**问题**：$d$ 越接近/越超过经典 Wiener 边界，攻击表现如何变化？

固定 `n_bits=512` 或 `1024`（先便于快速迭代），令 `T ≈ n^(1/4)/3`；取几组目标 `d/T`，如 `0.25, 0.50, 0.75, 1.25, 2.0`。每组生成多套**有效** RSA 密钥，并记录实际 `d/T`、成功率、候选数量。

**注意**：小于边界的成功结论需要满足定理对 $p,q$ 比例的其他假设；大于边界未必失败。图表仅反映实验观测，不能把边界误说成“任何超出都安全”。

**输出**：柱形图 `Success Rate vs d/T`；一小段分析：理论保证区间、实际失败/成功区间与可能原因。

### 3.3 实验 E2：真实规模 RSA 模数 vs 攻击耗时（最符合老师偏好）

**问题**：针对特意选用弱 $d$ 的 RSA，$n$ 从 256 bit 增长到 2048 bit 时攻击是否仍然可行？

- `n_bits ∈ {256,512,1024,2048}`（如时间足够，可加 4096）。
- 维持 `d/T` 在很小的安全实验区间，例如约 `0.25`；选择大小相近的素数。
- 每组可先重复 10 次；本地快速确认后提升至 20–30 次，记录每次攻击耗时、候选渐近分数数目、成功率。
- 关键截图/视频：**2048-bit weak RSA 成功恢复 $d$，并完成解密验证**。

**输出**：折线图 `Attack Time (ms) vs RSA Modulus Size (bits)`；可加 `Convergents Checked vs Key Size`。测试结果要由本组实测填写，文档不预填任何假数字。

### 3.4 实验 E3：正常 RSA vs Wiener-weak RSA（防止夸大）

**问题**：攻击成功是否依赖“小私钥指数”，而非“RSA 是弱算法”？

- 对照组：按正常模式生成 RSA（如固定常见的 `e=65537`）。
- 弱组：相近位数、故意构造很小的 $d$。
- 对两组使用完全相同的攻击入口 `wiener_attack(e,n)`。
- 记录成功率、恢复 $d$ 的准确率、攻击耗时。

**输出**：两组结果对照表（不必做复杂图）。解释：无法恢复正常 $d$ 不等于完全证明其安全性，只说明本方法在这些样本上未成功。

### 3.5 加分项 E4：与小规模 brute force 比较（可选，不建议抢占核心时间）

在教学规模下比较暴力枚举小 $d$ 与 Wiener 方法的候选数量及耗时，说明连分数为何能加速。**不要**在 2048-bit 模数上做无限期 brute force；此项只用于小参数演示，并标注使用的不同条件。

### 3.6 图表最低标准

至少有 **两张图 + 一张对照表**：

1. `wiener_success_vs_d_ratio.png`：横轴 `d/T`，纵轴 `success rate (%)`。
2. `wiener_time_vs_modulus_bits.png`：横轴 bit length，纵轴攻击耗时（median ms，必要时误差线）。
3. `weak_vs_normal.csv` + PPT 对照表：正常/弱密钥的尝试数与恢复数。

各图明确注明 **真实实验数据**、机器环境与 trial 数；不能使用示意数据充当实验结论。

---

## 4. 现场 Demo：具体跑什么、展示什么

### 4.1 Demo 要传达的三个信息

1. **攻击者只有公钥**：不传 `p,q,d,phi`，这是项目可信度的核心。
2. **大模数不自动保证安全**：成功攻击一组合法的 **2048-bit weak RSA**。
3. **不是“所有 RSA 都能被破”**：在正常 RSA 对照上返回未发现 Wiener 弱点。

### 4.2 推荐脚本流程 `python scripts/demo.py`

```text
====================================================
RSA WIENER ATTACK: LIVE DEMONSTRATION
====================================================
1) Generate intentionally vulnerable 2048-bit RSA
   n.bit_length() = 2048
   public key: (n,e) [show first/last digits or full via file]
   chosen d is kept PRIVATE from the attacker

2) Prepare sample plaintext m and ciphertext c=pow(m,e,n)
   attacker receives ONLY: n, e, c

3) Run wiener_attack(e,n)
   continued fraction candidates checked: XX
   recovered private exponent d': [abbreviated]
   mathematical validation: p*q == n : TRUE

4) Decrypt using recovered d'
   plaintext recovered: [same as original]
   key recovery successful: TRUE
   elapsed: XX ms

5) Normal RSA control
   generate normal RSA / load verified normal fixture
   run identical attack
   no valid Wiener key recovered (in this run)

6) Show experiment figure(s): success vs ratio; timing vs bits
====================================================
```

`XX` 等数字必须在运行后由程序生成，绝不硬编码成功输出。

### 4.3 演示可靠性

- **先预生成合法测试样本**（保存公钥和仅用于检验的秘密参考），保证 6 分钟展示不会因为现场生成素数而拖延；如果现场生成耗时短，也可以演示一键生成，但要有备份。
- 至少准备一份通过测试的 2048-bit 弱密钥样例（fixture），在没有网络的机器上也能运行。
- Demo 脚本用 `--fixture` 和 `--generate` 两种模式，先跑稳定模式；**不伪装 fixture 为现场随机生成**。
- 使用简短的输出格式，2048-bit 整数只展示位长、前后若干位或保存到文件；讲解时强调内部使用完整整数。
- 如果 live run 意外失败：直接切换到另一个**先前真实验证通过**的 fixture，再现场跑攻击；最后展示保留的真实实验 CSV 和图片。不要把事前录制结果冒充实时运行。
- 现场前：确认 Python 版本、依赖安装、路径、显示分辨率、终端字体、运行时间，练习至少 3 次。

### 4.4 Demo 检验标准

- `recovered_d == true_d`（仅测试端比较）。
- `p_recovered*q_recovered == n`。
- `pow(pow(m,e,n),recovered_d,n) == m`。
- 攻击函数输入确实只有 $(e,n)$。
- 正常密钥对照结果如实报告。

---

## 5. Presentation：建议 7 页 / 6 分钟

> **注意**：按 `Intro-Crypto.pdf` 的 6+2 分钟安排。若老师确认 8+2，则延长数学解释和实验分析，不要临时塞入未经验证的新内容。

| 页码 | 标题 | 时间 | 必须讲清楚 / 视觉内容 |
|---|---|---:|---|---|
| 1 | Title & Research Question | 0:20 | 为什么“2048-bit 仍可能因小 d 而不安全”；一句话研究目标 |
| 2 | RSA and the Vulnerability | 0:45 | $(n,e)$、$d$、`ed≡1(mod φ)`；什么是弱参数 |
| 3 | Mathematical Idea of Wiener | 1:05 | `ed-kφ=1`；为什么 $\frac{k}{d}$ 在 $\frac{e}{n}$ convergents 中；理论假设与边界 |
| 4 | Self-written Implementation | 0:55 | 代码模块和算法流程；展示一小段**真的由该同学写的**关键函数，不展示整页代码 |
| 5 | Live Demo (2048-bit weak RSA) | 1:20 | `public (n,e)` → 求候选 → 恢复 $d$ → 解密；有正常对照 |
| 6 | Experiments and Findings | 1:00 | 两张图/一张表；真实数据、边界、局限 |
| 7 | Code Authorship / AI Use & Conclusion | 0:35 | 谁写了哪些关键算法、AI 用在哪里、一个安全结论 |
| | **合计** | **6:00** | **另留 2:00 Q&A** |

### 5.1 每页推荐讲稿要点

**Slide 1**（20 秒）：`We investigated whether Wiener's continued-fraction attack can recover the private exponent of a 2048-bit RSA modulus when d is insecurely small. Our focus is the vulnerability and an independently implemented attack.`

**Slide 2**（45 秒）：定义 $n=pq$、$\varphi(n)$、`ed≡1`，强调标准 RSA 不是普遍可破解；风险来自私钥指数选择。

**Slide 3**（65 秒）：说明 `ed-kφ(n)=1`，$\frac{k}{d}$ 可借助 $\frac{e}{n}$ 的连分数得到；展示 **系数 → convergents → candidate test** 的三个小步骤；说清适用条件，不需要讲完证明。

**Slide 4**（55 秒）：代码模块与可验证的亲自实现部分；`math.isqrt` 验证候选 $p,q$，不使用浮点；攻击只输入 $(n,e)$。

**Slide 5**（80 秒）：运行准备好的 weak-2048 fixture；指出模数实际位数，恢复 $d$ 的一致性与解密结果；再显示 normal control。

**Slide 6**（60 秒）：显示真实 success-rate 图和 timing 图。先讲“观察结果”，再讲“为何符合/不完全符合理论边界”，不要把关联讲成绝对因果或把小样本结论泛化。

**Slide 7**（35 秒）：如实列出核心函数作者和 AI 参与范围；结论：**correct parameter generation matters as much as modulus length**。

### 5.2 Code Authorship Declaration 示例格式（实际必须如实改写）

| Key Function / Component | Actual Author(s) | AI Assistance (what and how) | Able to explain/test? |
|---|---|---|---|
| `extended_gcd`, `mod_inverse` | 如实填写 | 填写真实情况 | Yes/No |
| `generate_weak_rsa` | 如实填写 | 填写真实情况 | Yes/No |
| `continued_fraction`, `convergents` | 如实填写 | 填写真实情况 | Yes/No |
| `wiener_attack`, `recover_factors` | 如实填写 | 填写真实情况 | Yes/No |
| experiment plots / slides | 如实填写 | 填写真实情况 | Yes/No |

不要为了看起来“原创”而隐瞒使用 AI，也不要把完全由 AI 生成且自己不理解的代码作为核心成果。

---

## 6. Q&A：老师可能问什么，怎么准备

| 可能问题 | 答题核心 |
|---|---|
| 为什么私钥指数 $d$ 不能太小？ | 它可能满足 Wiener 条件，泄露特殊有理逼近结构，使 $\frac{e}{n}$ 的渐近分数暴露 $d$。 |
| 为什么攻击者只要 $(n,e)$？ | 这两个是公钥；算法枚举 $\frac{e}{n}$ 的 convergents，从候选 $(k,d)$ 反求 $\varphi(n),p,q$，无需秘密输入。 |
| 为什么用 Continued Fractions？ | Wiener 定理保证在其假设下真实 $\frac{k}{d}$ 是某个 convergent；不必穷举所有 $d$。 |
| 为什么要算判别式？ | 候选 `φ` 给出 `p+q`，与 `pq=n` 组成二次方程；整数根和乘积验证候选是否真实。 |
| 经典条件是什么？ | 课件给出 $d<n^{1/4}/3$，需要相关 RSA 参数假设，通常要求两个素数大小相近。 |
| 超过边界就绝对安全吗？ | 不。超过经典保证区间后，该定理不保证 Wiener 成功；仍可能有其他漏洞。 |
| 2048-bit 的正常 RSA 也可以这样破解吗？ | 不可以据此得出结论；成功样本是**故意生成的小 d 弱密钥**。 |
| 为什么不直接调用现成攻击库？ | 项目侧重独立数学实现与解释，调用库不体现老师要求的 own coding/technical merit。 |
| `math.sqrt` 与 `math.isqrt` 有什么区别？ | 大整数精度需要精确整数平方根；float 会失准。 |
| 两人的贡献是什么？ | 如实指向函数、测试和 git commits，并能独立解释本人代码及对方模块原理。 |
| 为什么使用 `secrets` 而不是 `random`？ | `secrets` 提供更适合密钥生成的安全随机接口；普通伪随机数产生器不应作为生产密钥材料来源。 |
| 为什么正常组攻击失败？ | 在测试样本中未找到有效 Wiener 候选，不代表数学上证明了完整 RSA 安全。 |

**答辩要求**：两位成员都应理解 RSA 密钥生成、连分数算法、攻击验证及相关代码，能够解释输入、输出、失败分支和数学理由。

---

## 7. 交付物与最终验收清单

### 7.1 交付物

1. 可运行的 Python 源代码（需要时可提交）。
2. 一条命令的 Demo + 至少一套已验证的 2048-bit **弱 RSA** fixture。
3. 自动化测试和测试结果。
4. 实验原始 CSV、真实生成的图表和文字解释。
5. 6 分钟 Presentation（以老师最终时间通知为准）+ 2 分钟 Q&A 准备。
6. Code Authorship & AI Use 声明。
7. `README.md`：环境安装、运行命令、数学假设、实验复现流程、明确的安全边界。

### 7.2 完工门槛（逐项打勾）

- [x] 小组注册邮件发给老师、CC 队友（若尚未完成）。
- [ ] 两名成员均能手算小型 RSA，并解释 $ed\equiv1\pmod{\varphi(n)}$。
- [ ] 完成 RSA 核心函数和测试；`n.bit_length()` 达到要求。
- [ ] 能够构造**有效**的弱 $d$ RSA，而非随意改动私钥。
- [ ] 完成 Continued Fractions 和 Convergents，并通过已知分数测试。
- [ ] 攻击函数只输入 $(e,n)$，并使用严格整数因子验证。
- [ ] 2048-bit **弱参数**案例可以正确恢复 $d$、$p,q$ 并解密。
- [ ] 一组正常 RSA 公钥对照实验如实报告。
- [ ] 实验 E1/E2/E3 可复现，并有真实 CSV、至少两张图和一张对照表。
- [ ] Demo 可以离线运行、可在 80 秒内讲清，备用 fixture 可用。
- [ ] PPT 有数学原理、代码实现、实验结果、局限性、AI/作者声明。
- [ ] 能回答“为何得到候选 $d$、如何验证 $d$、攻击假设是什么”。

---

## 附录 A：项目声明的推荐措辞（可放 PPT）

> This project implements Wiener's continued-fraction attack on RSA keys with intentionally small private exponents. The attack uses only the public key $(n,e)$ and validates recovered factors and the private exponent. We evaluate attack success and runtime on deliberately vulnerable RSA moduli, including 2048-bit examples. This does **not** imply that properly generated 2048-bit RSA keys are generally breakable by Wiener's attack.

## 附录 B：提交前的自查提问

- 为什么 $d$ 小会产生连分数逼近？
- 为什么 $\frac{k}{d}$ 不只是一个普通分数，而可以从 $\frac{e}{n}$ 的 convergent 中找到？
- 你们验证候选 $d$ 的数学过程是否足够严格？
- 整数平方根是否保证准确，尤其是 2048-bit？
- 实验图中的每个点对应多少次运行？是否把密钥生成时间误算为攻击时间？
- 是否明确了 Wiener 理论边界的假设？
- Demo 中攻击函数是否偷偷读取了真实私钥？
- 是否夸大“真实规模弱 RSA”成“任何 2048-bit RSA 都可破解”？
- 对老师的代码作者及 AI 使用声明，是否真实、有 Git / 测试记录支撑？
