# 演示操作流程与讲解内容

## 1. 演示前准备

在项目根目录打开终端：

```powershell
conda activate common
python -B -m unittest discover -s tests -v
python -B scripts/demo.py
```

正式演示优先使用默认 fixture 模式。它读取事先真实生成并验证过的 2048-bit
弱密钥，不依赖网络，也不会把现场时间浪费在随机素数生成上。

完整实验应在演示前运行：

```powershell
python -B scripts/run_experiments.py --trials 10
```

确认以下文件存在：

- `fixtures/weak_rsa_2048.json`
- `fixtures/normal_rsa_2048.json`
- `results/raw/e1_d_ratio.csv`
- `results/raw/e2_modulus_bits.csv`
- `results/raw/weak_vs_normal.csv`
- `results/plots/wiener_success_vs_d_ratio.png`
- `results/plots/wiener_time_vs_modulus_bits.png`

## 2. 默认演示命令

```powershell
python -B scripts/demo.py
```

可选的现场生成模式：

```powershell
python -B scripts/demo.py --generate
```

现场生成模式得到的是新的随机密钥，运行时间不固定。它适合作为备用说明，不建议
在只有 80 秒的正式 Demo 中优先使用。

## 3. 80 秒演示流程

### 0–10 秒：说明目标

建议讲稿：

> 我们演示的是一组故意把私钥指数 d 选得过小的 2048-bit RSA。攻击者只拥有
> 公钥 n、e，不会把真实 d、p、q 或 phi 传给攻击函数。

屏幕上指出：

- n.bit_length() 等于 2048。
- n、e 只缩写显示，但程序内部使用完整整数。
- 输出明确写着 d、p、q、phi 不传给攻击函数。

### 10–22 秒：准备密文

建议讲稿：

> 我们先把一条短消息转换成整数，然后计算 c=m^e mod n。现在攻击方拥有 n、e
> 和密文 c。

### 22–48 秒：运行攻击

建议讲稿：

> 这里调用 wiener_attack(e,n)。程序计算 e/n 的连分数，逐个把渐近分数看作
> 候选 k/d，再从候选 phi 的二次方程检查是否能得到精确整数因数 p、q。

屏幕上指出：

- 实际检查的 convergents 数量。
- 恢复出的 d 只显示首尾数字。
- p*q == n 为 True。
- 攻击耗时由程序实时测量，不是硬编码。

### 48–60 秒：解密验证

建议讲稿：

> 使用恢复出的 d 解密后，明文与原消息一致。测试端再比较 recovered d 和 fixture
> 中的参考 d，确认我们恢复的是同一个私钥指数。

### 60–72 秒：普通 RSA 对照

建议讲稿：

> 接着对一组 2048-bit 普通 RSA 调用完全相同的 wiener_attack(e,n)。本次返回
> None，说明 Wiener 方法没有找到有效候选。它不是完整安全证明，但说明攻击成功
> 依赖小 d 弱点，而不是因为所有 RSA 都能这样破解。

### 72–80 秒：实验文件

建议讲稿：

> 最后两张图来自批量真实实验：第一张比较 d/T 与成功率，第二张比较模数位数与
> 攻击耗时。每次 trial 的原始结果都保存在 CSV 中。

## 4. 演示时展示的关键代码

只展示三处，不要滚动整页代码：

1. `scripts/demo.py` 中的 `wiener_attack(weak_key.e, weak_key.n)`，证明攻击入口只有公钥。
2. `src/continued_fraction.py` 中的 convergents 递推。
3. `src/wiener_attack.py` 中判别式、整数平方根和 p*q==n 检查。

## 5. 图表讲解

成功率图：

- 红色虚线表示经典课程边界 d/T=1 的位置。
- 边界左侧在满足其他假设时有理论保证。
- 边界右侧可能成功也可能失败，不能说“超过边界就安全”。
- `--quick` 的两次样本只用于检查程序，不能作为最终统计结论。

耗时图：

- 横轴是实际 RSA 模数位数。
- 纵轴是多次 trial 的攻击耗时中位数。
- 误差线表示该组实测最小值到最大值。
- 密钥生成时间没有混入攻击时间。

普通与弱密钥表：

- 两组调用完全相同的攻击函数。
- 弱组应记录恢复 d 的正确次数。
- 普通组返回 None 只表示此攻击没有成功。

## 6. 失败时的备用操作

如果现场生成过慢或随机运行不符合预期：

1. 按 Ctrl+C 停止现场生成。
2. 运行 `python -B scripts/demo.py` 切回默认 fixture。
3. 展示已经保存的真实 CSV 和 PNG。
4. 明确说明当前使用的是预生成并验证过的 fixture，不要说成刚刚随机生成。

如果图片尚未生成：

```powershell
python -B scripts/run_experiments.py --quick
```

快速结果只用于恢复演示流程；正式报告仍使用完整实验结果。

## 7. 常见提问的简短回答

为什么 d 必须是奇数？

> p、q 为奇素数时 phi=(p-1)(q-1) 是偶数。偶数 d 与 phi 至少有公因数 2，
> 不可能存在模逆。

为什么使用整数平方根？

> 2048-bit 整数转成 float 会丢失精度。候选判别式必须确认是完全平方数，所以
> 全程使用整数平方根。

为什么可以从 phi 得到 p、q？

> phi=n-(p+q)+1，所以候选 phi 给出 p+q；再结合 pq=n，p、q 就是一个二次
> 方程的两个整数根。

超过边界为什么仍可能成功？

> d<n^(1/4)/3 是经典条件下的充分保证，不是“超过就一定失败”的充要条件。

2048-bit 为什么仍然能被攻击？

> 模数长度只是一项参数。这里故意把 d 选得太小，暴露了连分数结构；这不代表
> 正常 2048-bit RSA 被普遍破解。
