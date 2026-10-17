# 自己实现代码详细讲解

## 1. 文档范围

当前源码只把下面 8 个函数标记为“自己实现”：

1. generate_normal_rsa
2. approximate_wiener_threshold
3. is_below_wiener_bound
4. _nearest_odd_coprime
5. generate_weak_rsa
6. continued_fraction
7. convergents
8. wiener_attack

下面这些功能直接调用库，不属于我们自己实现的算法：

- math.gcd：计算最大公约数。
- pow(value, -1, modulus)：计算模逆。
- pow(value, exponent, modulus)：计算模幂。
- Crypto.Util.number.getPrime：生成素数。
- math.isqrt：计算整数平方根。
- Fraction、dataclass、perf_counter、CSV 和 matplotlib 等通用功能。

代码中的“自己实现”表示我们负责组织这些函数的流程、判断条件和候选验证。
它不是“完全没有使用 AI”的声明；AI 使用范围仍应按实际情况填写。

## 2. 整体关系

正常 RSA 密钥生成：

```text
getPrime 生成 p、q
        ↓
计算 n 和 phi
        ↓
math.gcd 检查 e 与 phi 是否互素
        ↓
pow(e, -1, phi) 求 d
        ↓
返回正常 RSA 密钥
```

弱 RSA 密钥生成：

```text
getPrime 生成 p、q
        ↓
计算 n 和 phi
        ↓
计算 Wiener 边界标尺 T
        ↓
寻找接近目标值且与 phi 互素的奇数 d
        ↓
pow(d, -1, phi) 求 e
        ↓
返回故意使用小 d 的 RSA 密钥
```

Wiener 攻击：

```text
公开输入 e、n
        ↓
continued_fraction 计算 e/n 的连分数
        ↓
convergents 产生候选 k/d
        ↓
wiener_attack 逐个验证候选
        ↓
恢复 d、p、q，或者返回 None
```

贯穿攻击讲解的小例子是：

```text
p   = 379
q   = 239
n   = 90581
phi = 89964
d   = 5
e   = 17993
```

因为 17993×5=89965=1+89964，所以 e×d mod phi=1。

---

## 3. generate_normal_rsa：生成正常 RSA 参数

### 3.1 函数目标

输入希望得到的模数位数 bits，返回 n、e、d、p、q 和 phi。公开密钥是
(n,e)，p、q、phi 和 d 应由密钥持有者保管。

### 3.2 为什么固定 e=65537

65537 是常用的公开指数。这个项目不研究怎样选择公开指数，所以直接固定它，把
重点放在正常参数和小 d 参数的区别上。

函数要求 bits 至少为 17，是因为 e=65537 本身是 17 位数。模数过小时，很难让
phi 大于 e，也就不能按当前流程生成密钥。

### 3.3 为什么 prime_bits=(bits+1)//2

p 和 q 大小接近时，它们的位数大约是 n 位数的一半。加 1 后整除 2，相当于在
bits 为奇数时向上取整。例如 bits=65 时，prime_bits=33。

这一步只确定 p、q 的候选位数，不能单独保证 p×q 恰好是 bits 位。因此代码生成
n 后还必须检查：

```python
if n.bit_length() != bits:
    continue
```

真正保证 n 位数正确的是这项检查。

### 3.4 循环流程

1. 使用 getPrime 生成 p、q。
2. 如果 p==q，就重新生成。
3. 计算 n=p×q。
4. 如果 n 的实际位数不等于 bits，就重新生成。
5. 计算 phi=(p-1)(q-1)。
6. 使用 math.gcd 检查 e 和 phi 是否互素。
7. 使用 pow(e,-1,phi) 得到 d。
8. 返回密钥。

只有 gcd(e,phi)=1 时模逆才存在。这里不自己实现最大公约数和模逆，只负责在
RSA 生成流程中正确调用。

### 3.5 为什么正常 RSA 是先选 e

正常生成流程先固定公开指数 e，再求私钥指数 d：

```text
d = e^(-1) mod phi
```

因此 d 通常不会被故意限制为很小。它与弱密钥生成函数最大的区别就在这里。

---

## 4. approximate_wiener_threshold：计算边界标尺

### 4.1 函数目标

课程使用的 Wiener 经典边界是：

```text
d < n^(1/4) / 3
```

生成弱密钥时需要一个接近这个边界的整数作为标尺 T。函数计算：

```python
isqrt(isqrt(n)) // 3
```

### 4.2 为什么连续使用两次 isqrt

第一次 isqrt(n) 近似得到 n 的平方根；第二次再开平方，近似得到 n 的四次方根。
整个过程只用整数，不会把 2048-bit 大整数转换为精度有限的浮点数。

### 4.3 为什么它只是近似值

每次 isqrt 都向下取整，最后除以 3 也向下取整。因此它适合用来构造目标 d 和显示
实验比例，但不负责严格判断不等式。严格判断由下一个函数完成。

---

## 5. is_below_wiener_bound：精确判断边界

要判断：

```text
d < n^(1/4)/3
```

对正数两边先乘 3，再取四次方：

```text
3d < n^(1/4)
(3d)^4 < n
81d^4 < n
```

所以函数直接返回：

```python
81 * d**4 < n
```

这个判断完全使用整数，因此没有浮点舍入误差。它和上一函数分工不同：

- approximate_wiener_threshold 用于得到一个方便选 d 的近似标尺。
- is_below_wiener_bound 用于判断最终 d 是否真的满足严格不等式。

---

## 6. _nearest_odd_coprime：寻找合法的小 d

### 6.1 函数目标

弱密钥生成器先算出目标值 target，但 target 不一定可以作为 RSA 私钥指数。
合法的 d 必须满足：

```text
1 < d < phi
gcd(d, phi) = 1
```

该函数从 target 附近寻找满足条件的奇数。

### 6.2 为什么只检查奇数

p、q 是奇素数时，p-1 和 q-1 都是偶数，所以 phi=(p-1)(q-1) 一定是偶数。
如果 d 也是偶数，那么 d 和 phi 至少有公因数 2，不可能互素。因此只检查奇数
可以省去肯定失败的候选。

### 6.3 搜索顺序

如果 target 是偶数，先把 center 调整成上方相邻的奇数。之后令 offset 从 0
开始，每轮增加 2：

```text
upper = center + offset
lower = center - offset
```

先检查 upper，再检查 lower。找到第一个与 phi 互素的候选就返回。

例如 target=9、phi=198：

1. 检查 9，gcd(9,198)=9，不合法。
2. offset 变为 2，检查 11，gcd(11,198)=11，不合法。
3. 再检查 7，gcd(7,198)=1，返回 7。

### 6.4 为什么检查 upper<phi

RSA 指数应小于 phi。如果上方候选已经达到 phi，就不能返回它；代码仍可继续
检查下方候选。若最初 center 已经不小于 phi，函数直接报告目标值不合法。

---

## 7. generate_weak_rsa：构造小 d 的 RSA

### 7.1 函数目标

该函数生成数学上有效、但私钥指数 d 被故意选得很小的 RSA 参数，用于 Wiener
攻击实验。它不是随机产生一个错误密钥，而是先选 d，再根据 d 计算 e。

### 7.2 d_target_ratio 的作用

ratio 控制目标 d 接近 Wiener 边界标尺 T 的程度：

```text
target_d ≈ ratio × T
```

例如：

- ratio=0.25：d 大约是 T 的四分之一。
- ratio=0.5：d 大约是 T 的一半。
- ratio=1.0：d 接近 T。
- ratio>1：用于观察超过经典边界后攻击是否仍偶尔成功。

没有这个参数也能生成一组弱密钥，但无法方便地完成“成功率随 d 大小变化”的实验。

### 7.3 为什么将比例转换成 Fraction

2048-bit 的 threshold 非常大。Fraction 让 ratio×threshold 保持精确的有理数
计算，最后才用 round 取最接近的整数：

```python
target_d = round(ratio * threshold)
```

这个整数只是搜索中心，_nearest_odd_coprime 还会把它调整为合法 d。

### 7.4 完整流程

1. 记录开始时间。
2. 生成 p、q，并保证两者不同。
3. 计算 n，检查实际位数。
4. 计算 phi。
5. 计算边界标尺 threshold。
6. 根据 ratio 得到 target_d。
7. 寻找接近目标且与 phi 互素的奇数 d。
8. 使用 pow(d,-1,phi) 求 e。
9. 记录生成时间以及 d 与边界的关系。
10. 返回弱密钥。

正常密钥是“固定 e，求 d”；弱密钥是“故意选小 d，求 e”。这是答辩时最应
强调的区别。

### 7.5 小例子

假设 p=379、q=239：

```text
n   = 90581
phi = 89964
T   = isqrt(isqrt(90581))//3 = 5
```

当 ratio=1 时，target_d=5。因为 gcd(5,89964)=1，所以 d=5。库调用
pow(5,-1,89964) 得到 e=17993，最终：

```text
17993×5 mod 89964 = 1
```

---

## 8. continued_fraction：计算连分数系数

### 8.1 函数目标

输入分子 numerator 和正分母 denominator，输出有理数的连分数系数。
计算 e/n 时始终使用整数除法，不先求小数。

### 8.2 算法

每轮执行：

```python
quotient, remainder = a // b, a % b
```

把 quotient 加入结果，然后令 a=b、b=remainder。余数为 0 时结束。

### 8.3 例子：43/19

```text
43 = 2×19 + 5
19 = 3×5  + 4
5  = 1×4  + 1
4  = 4×1  + 0
```

所以：

```text
43/19 = [2;3,1,4]
```

这段过程和欧几里得除法形式相同，但这里保存的是每轮商。

---

## 9. convergents：计算渐近分数

### 9.1 函数目标

对连分数的每个前缀求值。例如 [2;3,1,4] 的前缀依次是：

```text
[2]
[2;3]
[2;3,1]
[2;3,1,4]
```

对应渐近分数：

```text
2/1, 7/3, 9/4, 43/19
```

### 9.2 为什么从右向左算

连分数定义本身是嵌套结构：

```text
[a0;a1,a2] = a0 + 1/(a1 + 1/a2)
```

最里面的 a2 最先确定，所以对一个前缀求值时，从最右边向左计算最直观。

假设右侧已经算成 numerator/denominator，左边再加入 coefficient：

```text
coefficient + 1/(numerator/denominator)
= coefficient + denominator/numerator
= (coefficient×numerator + denominator)/numerator
```

因此更新公式是：

```python
numerator, denominator = (
    coefficient * numerator + denominator,
    numerator,
)
```

### 9.3 例子：[2;3,1]

从最右边开始：

```text
1       = 1/1
3+1/1   = 4/1
2+1/4   = 9/4
```

所以第三个渐近分数是 9/4。函数依次对每个前缀执行这一过程并产出结果。

在 Wiener 攻击中，渐近分数的分子作为候选 k，分母作为候选 d。

---

## 10. wiener_attack：生成并验证候选

### 10.1 函数目标

函数只接收公钥 e、n，不接收真实 d、p、q 或 phi。它尝试返回恢复结果
(d,p,q)，遍历完所有候选仍未成功则返回 None。

### 10.2 第一步：得到候选 k/d

函数先计算 e/n 的连分数，再遍历其渐近分数。Wiener 定理说明，在相应条件下，
真实的 k/d 会出现在这些渐近分数中。

当 e<n 时，第一个连分数系数是 0，所以第一个渐近分数通常是 0/1。k=0 不能
作为除数，因此跳过。

### 10.3 第二步：候选必须能给出整数 phi

RSA 中存在整数 k，使：

```text
e×d - k×phi = 1
```

整理得到：

```text
phi = (e×d-1)/k
```

所以代码先判断 (e×d-1) 是否能被 k 整除。不能整除就不是正确候选。

### 10.4 第三步：从候选 phi 推出 p+q

因为：

```text
phi = (p-1)(q-1)
    = pq-p-q+1
    = n-(p+q)+1
```

所以：

```text
p+q = n-phi+1
```

代码把这个和记为 factor_sum。

### 10.5 第四步：建立二次方程

已知 p+q=factor_sum 且 pq=n。以 p、q 为两个根，可以写出：

```text
(x-p)(x-q)=0
x²-(p+q)x+pq=0
x²-factor_sum×x+n=0
```

判别式是：

```text
delta = factor_sum²-4n
```

把 p+q 和 pq 代入还能得到：

```text
delta = (p+q)²-4pq = (p-q)²
```

因此正确候选的 delta 必须是非负完全平方数。

### 10.6 什么是完全平方数

完全平方数是某个整数的平方，例如 0、1、4、9、16。代码计算：

```python
sqrt_delta = isqrt(delta)
```

再检查 sqrt_delta² 是否等于 delta。相等说明平方根是整数；不相等说明无法得到
整数 p、q。

### 10.7 第五步：恢复并验证 p、q

二次方程的两个根为：

```text
p = (factor_sum + sqrt_delta)/2
q = (factor_sum - sqrt_delta)/2
```

代码检查两个分子是偶数，避免除以 2 后出现非整数。最后还要检查：

```text
p > 1
q > 1
p×q = n
e×d mod phi = 1
```

全部通过才返回结果。仅仅找到一个小 d，或仅仅让 e×d-1 能被 k 整除，都不足以
证明候选正确。

### 10.8 是否必须恢复 p、q

如果攻击目标只是解密，找到正确 d 后可以直接计算 c^d mod n。但是算法在搜索时
并不知道某个候选 d 是否正确。恢复 p、q 并检查 p×q=n，提供了不依赖真实私钥的
严格验证。因此本项目的攻击函数会恢复 p、q。

---

## 11. 建议的答辩讲解顺序

1. 先声明 gcd、模逆、模幂、素数生成和整数平方根使用库，不列为自己实现。
2. 对比 generate_normal_rsa 和 generate_weak_rsa：正常流程先定 e，弱流程先选小 d。
3. 解释边界近似函数、严格边界判断和寻找合法 d 的辅助函数。
4. 用 43/19 讲 continued_fraction 和 convergents。
5. 用 e=17993、n=90581 走一遍 wiener_attack 的候选验证。
6. 强调攻击函数只接收公开的 e、n。

必须理解的三条关系：

```text
e×d mod phi = 1
e×d-k×phi = 1
phi = n-(p+q)+1
```

它们分别连接了 RSA 密钥生成、Wiener 候选和因数恢复。
