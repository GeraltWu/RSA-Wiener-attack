# 演示操作流程与讲解内容

## 1. 演示前准备

在项目根目录打开终端：

```powershell
conda activate common
python -B -m unittest discover -s tests -v
python -B scripts/demo.py
```

Demo 每次运行都会现场随机生成一组 2048-bit 弱 RSA 和一组 2048-bit 普通
RSA。生成过程不依赖网络，开始后的等待时间取决于本机随机素数生成速度。

完整实验应在演示前运行：

```powershell
python -B scripts/run_experiments.py
```

运行前在 `scripts/run_experiments.py` 顶部确认 `TRIALS_PER_GROUP=30`，并确认
`RUN_E1`、`RUN_E2`、`RUN_E3` 均为 `True`。

确认以下文件存在：

- `results/raw/e1_d_ratio.csv`
- `results/raw/e2_modulus_bits.csv`
- `results/raw/weak_vs_normal.csv`
- `results/plots/wiener_success_vs_d_ratio.png`
- `results/plots/wiener_time_vs_modulus_bits.png`

## 2. 默认演示命令

```powershell
python -B scripts/demo.py
```

默认输出已经包含：

- 弱 RSA 和普通 RSA 的 n、e、d、p、q、phi 位数及缩写值。
- `p*q==n` 和 `e*d mod phi==1` 验证。
- Wiener 边界、d/T 和严格边界判断。
- 连分数系数总数，以及用省略号连接首尾系数的一行摘要。
- 成功候选附近的系数、候选 k/d、候选 phi、p+q、判别式和平方根。
- 恢复出的 d、p、q、phi 与参考值的比较。
- 密钥生成、加密、攻击和解密耗时。
- 普通 RSA 的参数、连分数摘要和攻击失败结果。

如需在答疑时展开完整值：

```powershell
python -B scripts/demo.py --full-values
python -B scripts/demo.py --full-coefficients
python -B scripts/demo.py --full-values --full-coefficients
```

完整系数列表和完整 2048-bit 十进制整数会产生大量输出，正式演示建议使用默认
摘要模式。

运行命令后先等待两组密钥生成完成，再开始讲解输出。程序会单独显示密钥生成
时间，不会把它混入 Wiener 攻击时间。

## 3. 约 100 秒演示流程

### 0–15 秒：说明数据分层

建议讲稿：

> 我们演示的是一组故意把私钥指数 d 选得过小的 2048-bit RSA。攻击者只拥有
> 公钥 n、e，不会把真实 d、p、q 或 phi 传给攻击函数。

屏幕上指出：

- n.bit_length() 等于 2048。
- n、e、d、p、q、phi 都显示位数和缩写值，但程序内部使用完整整数。
- d、p、q、phi 属于生成端参考值，只用于最后验证，攻击函数实际只接收 e、n。
- 弱密钥的 d/T 约为 0.75，并且严格边界判断为 True。

### 15–28 秒：准备密文和连分数

建议讲稿：

> 我们先把一条短消息转换成整数，然后计算 c=m^e mod n。现在攻击方拥有 n、e
> 和密文 c。程序同时显示 e/n 的连分数系数数量和部分系数，完整列表默认省略，
> 避免 1200 多项内容淹没关键结果。

### 28–55 秒：展示攻击恢复链条

建议讲稿：

> 这里调用 wiener_attack(e,n)。程序计算 e/n 的连分数，逐个把渐近分数看作
> 候选 k/d，再从候选 phi 的二次方程检查是否能得到精确整数因数 p、q。

屏幕上指出：

- 成功候选的编号。
- 成功渐近分数对应的 k 和候选 d。
- `phi=(e*d-1)/k`、`p+q=n-phi+1` 和判别式。
- 恢复出的 d、p、q、phi 均与参考值一致。
- `p*q==n` 为 True。
- 攻击耗时由程序实时测量，不是硬编码。

### 55–67 秒：解密验证

建议讲稿：

> 使用恢复出的 d 解密后，明文与原消息一致。测试端再与本次现场生成时保留的
> 参考 d 比较，确认恢复的是同一个私钥指数。

### 67–90 秒：普通 RSA 对照

建议讲稿：

> 接着对一组 2048-bit 普通 RSA 调用完全相同的 wiener_attack(e,n)。本次返回
> None，说明 Wiener 方法没有找到有效候选。它不是完整安全证明，但说明攻击成功
> 依赖小 d 弱点，而不是因为所有 RSA 都能这样破解。

同时指出普通 RSA 的 d 接近模数位数，严格 Wiener 边界判断为 False；程序将
参数构造和攻击尝试分开展示，并使用相同的攻击入口。

## 4. 演示时展示的关键代码

只展示三处，不要滚动整页代码：

1. `scripts/demo.py` 中的 `wiener_attack(weak_key.e, weak_key.n)`，证明攻击入口只有公钥。
2. `src/continued_fraction.py` 中从右向左计算渐近分数的过程。
3. `src/wiener_attack.py` 中判别式、整数平方根和 p*q==n 检查。

## 5. 图表讲解

成功率图：

- 红色虚线表示经典课程边界 d/T=1 的位置。
- 边界左侧在满足其他假设时有理论保证。
- 边界右侧可能成功也可能失败，不能说“超过边界就安全”。
- 将 `TRIALS_PER_GROUP` 临时改为 2 只能用于检查程序，不能作为最终统计结论。

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

如果现场生成比平时慢，应提前说明当前正在生成两个 1024-bit 素数构成的
2048-bit 模数。演示前至少完整练习三次，并保留已经生成的真实实验 CSV 和 PNG
作为结果说明；不要把 CSV 中的批量实验数据说成当前 Demo 的密钥。

如果图片尚未生成：

```powershell
python -B scripts/run_experiments.py
```

运行前可以临时把 `TRIALS_PER_GROUP` 改为 2，并只启用需要重新生成的实验。快速
结果只用于恢复演示流程；正式报告仍使用完整实验结果。

## 7. 常见提问的简短回答

为什么 d 必须是奇数？

> p、q 为奇素数时 phi=(p-1)(q-1) 是偶数。偶数 d 与 phi 至少有公因数 2，
> 不可能存在模逆。

为什么使用整数平方根？

> 2048-bit 整数转成 float 会丢失精度。候选判别式必须确认是完全平方数，所以
> 使用 Python 标准库的 math.isqrt 做精确整数平方根计算，不使用浮点 sqrt。

为什么可以从 phi 得到 p、q？

> phi=n-(p+q)+1，所以候选 phi 给出 p+q；再结合 pq=n，p、q 就是一个二次
> 方程的两个整数根。

超过边界为什么仍可能成功？

> d<n^(1/4)/3 是经典条件下的充分保证，不是“超过就一定失败”的充要条件。

2048-bit 为什么仍然能被攻击？

> 模数长度只是一项参数。这里故意把 d 选得太小，暴露了连分数结构；这不代表
> 正常 2048-bit RSA 被普遍破解。
