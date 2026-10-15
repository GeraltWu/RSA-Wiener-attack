# 自己实现代码详细讲解

## 1. 文档范围

本文只详细讲解源码中标记为“自己实现”的 11 个函数：

1. `gcd`
2. `extended_gcd`
3. `mod_inverse`
4. `generate_normal_rsa`
5. `approximate_wiener_threshold`
6. `is_below_wiener_bound`
7. `_nearest_odd_coprime`
8. `generate_weak_rsa`
9. `continued_fraction`
10. `convergents`
11. `wiener_attack`

其他代码可能负责保存数据、调用函数、运行测试或展示结果，但不使用“自己实现”
标记。以下库功能也不属于我们的算法实现：

- PyCryptodome 的 `getPrime`：生成素数并完成内部素性检测。
- Python 的三参数 `pow`：完成高效模幂。
- `math.isqrt`：计算整数平方根。
- `Fraction`、`dataclass`、`perf_counter`、CSV、matplotlib 等通用功能。

## 2. 十一个函数之间的关系

正常 RSA 密钥生成流程：

```text
getPrime 生成 p、q
        ↓
计算 n 和 phi
        ↓
gcd 检查 e 与 phi 是否互素
        ↓
mod_inverse 求 d
        ↓
返回正常 RSA 密钥
```

弱 RSA 密钥生成流程：

```text
getPrime 生成 p、q
        ↓
计算 n 和 phi
        ↓
approximate_wiener_threshold 计算边界标尺 T
        ↓
_nearest_odd_coprime 选择较小且合法的 d
        ↓
mod_inverse 求 e
        ↓
is_below_wiener_bound 记录 d 是否低于理论边界
        ↓
返回弱 RSA 密钥
```

Wiener 攻击流程：

```text
攻击者只得到公开的 e 和 n
        ↓
continued_fraction 计算 e/n 的连分数
        ↓
convergents 依次产生候选 k/d
        ↓
wiener_attack 验证每个候选
        ↓
恢复正确的 d、p、q，或者返回 None
```

后文使用下面的小型弱密钥作为贯穿示例：

```text
p   = 379
q   = 239
n   = p*q = 90581
phi = (p-1)*(q-1) = 89964
d   = 5
e   = 17993
```

这组数字满足：

```text
e*d = 17993*5 = 89965 = 1 + 89964
```

所以 `e*d mod phi = 1`。它是一组数学上合法的 RSA 参数，只是 `d=5` 太小，
因此可以被 Wiener 攻击。

---

## 3. gcd：计算最大公约数

### 3.1 函数目标

`gcd(a, b)` 返回 `a` 和 `b` 的最大公约数。RSA 中主要用它判断两个数是否互素：

```text
gcd(a, b) == 1
```

就表示 `a` 和 `b` 互素。

### 3.2 核心原理

欧几里得算法使用下面的性质：

```text
gcd(a, b) = gcd(b, a mod b)
```

如果某个数能同时整除 `a` 和 `b`，它也一定能整除 `a-q*b`。而 `a mod b`
正是这种相减之后得到的余数。因此，把 `(a,b)` 换成 `(b,a mod b)` 不会改变
最大公约数。

### 3.3 对照代码

```python
while b != 0:
    a, b = b, a % b
return abs(a)
```

每轮循环做两件事：

1. 原来的 `b` 变成新的 `a`。
2. 原来的 `a % b` 变成新的 `b`。

当 `b` 变成 0 时，`gcd(a,0)` 就是 `a`。最后使用 `abs(a)`，只是因为最大
公约数按照定义写成非负数；这不是额外的算法步骤。

### 3.4 具体例子：gcd(54, 24)

| 当前 a | 当前 b | a % b | 下一组数 |
|---:|---:|---:|---:|
| 54 | 24 | 6 | (24, 6) |
| 24 | 6 | 0 | (6, 0) |

第二个数变成 0，所以结果是 6。

### 3.5 在项目中的用途

- 正常密钥中检查 `gcd(e,phi)==1`。
- 弱密钥中检查候选 `d` 是否满足 `gcd(d,phi)==1`。
- 只有互素时，模逆才存在。

### 3.6 答辩时的一句话解释

> gcd 反复把两个数替换成“除数和余数”，最大公约数不会改变；余数变成 0
> 时，剩下的非零数就是最大公约数。

---

## 4. extended_gcd：求最大公约数以及回代系数

### 4.1 函数目标

普通 `gcd` 只返回最大公约数。`extended_gcd(a,b)` 还要返回两个系数 `x、y`，
使下面的等式成立：

```text
a*x + b*y = gcd(a,b)
```

函数返回 `(g,x,y)`，其中 `g` 是最大公约数。

### 4.2 为什么需要 x 和 y

如果 `gcd(a,m)=1`，扩展欧几里得可以找到：

```text
a*x + m*y = 1
```

等式两边对 `m` 取模，`m*y` 会被消掉：

```text
a*x mod m = 1
```

因此 `x` 就是 `a` 在模 `m` 下的逆元。

### 4.3 递归分成两个阶段

这个函数可以理解为两个方向：

1. 向下递归：和普通欧几里得算法一样，不断计算商和余数。
2. 向上返回：把余数表达式逐层代回，求出原始两个数的系数。

### 4.4 递归终点

```python
if b == 0:
    return a, 1, 0
```

因为 `a*1+0*0=a`，所以在 `b=0` 时可以直接返回 `(a,1,0)`。

### 4.5 每一层怎样回代

当前层先计算：

```python
quotient = a // b
remainder = a % b
g, x1, y1 = extended_gcd(b, remainder)
```

递归返回的等式是：

```text
b*x1 + remainder*y1 = g
```

当前层还知道：

```text
remainder = a - quotient*b
```

代入递归返回的等式：

```text
b*x1 + (a - quotient*b)*y1 = g
a*y1 + b*(x1 - quotient*y1) = g
```

与目标形式 `a*x+b*y=g` 对比，就得到：

```python
x = y1
y = x1 - quotient * y1
```

这两行不是背出来的公式，而是把余数表达式代回后自然得到的。

### 4.6 完整例子：extended_gcd(43, 19)

先向下做普通欧几里得除法：

```text
43 = 2*19 + 5
19 = 3*5  + 4
5  = 1*4  + 1
4  = 4*1  + 0
```

递归调用顺序是：

```text
extended_gcd(43,19)
extended_gcd(19,5)
extended_gcd(5,4)
extended_gcd(4,1)
extended_gcd(1,0)
```

到达终点后，再逐层返回：

| 当前调用 | quotient | 下一层返回 (g,x1,y1) | 当前 x | 当前 y | 当前返回 |
|---|---:|---|---:|---:|---|
| `egcd(1,0)` | - | - | 1 | 0 | `(1,1,0)` |
| `egcd(4,1)` | 4 | `(1,1,0)` | 0 | 1 | `(1,0,1)` |
| `egcd(5,4)` | 1 | `(1,0,1)` | 1 | -1 | `(1,1,-1)` |
| `egcd(19,5)` | 3 | `(1,1,-1)` | -1 | 4 | `(1,-1,4)` |
| `egcd(43,19)` | 2 | `(1,-1,4)` | 4 | -9 | `(1,4,-9)` |

最终结果是 `(1,4,-9)`。代回检查：

```text
43*4 + 19*(-9) = 172 - 171 = 1
```

### 4.7 答辩时的一句话解释

> 先用普通欧几里得算法递归到余数为 0，再利用
> remainder=a-quotient*b 逐层回代，得到原始 a、b 的系数。

---

## 5. mod_inverse：计算模逆

### 5.1 什么是模逆

如果存在整数 `x` 满足：

```text
a*x mod modulus = 1
```

那么 `x` 就是 `a` 在模 `modulus` 下的乘法逆元。模逆存在的充要条件是：

```text
gcd(a,modulus) = 1
```

### 5.2 函数执行步骤

第一步，把 `a` 化到非负剩余范围：

```python
normalized_a = a % modulus
```

第二步，调用扩展欧几里得：

```python
divisor, coefficient, _ = extended_gcd(normalized_a, modulus)
```

这里得到：

```text
normalized_a*coefficient + modulus*y = divisor
```

第三步，检查 `divisor` 是否为 1。如果不是 1，说明两数不互素，逆元不存在。

第四步返回 `coefficient % modulus`。扩展欧几里得得到的系数可能为负数，取模会
把它转换到常用的非负范围。

### 5.3 具体例子：17 在模 3120 下的逆元

扩展欧几里得可以得到：

```text
17*(-367) + 3120*2 = 1
```

所以 `-367` 是一个逆元表示。转换为非负结果：

```text
-367 mod 3120 = 2753
```

验证：

```text
17*2753 = 46801 = 15*3120 + 1
```

因此函数返回 2753。

### 5.4 逆元不存在的例子

`mod_inverse(12,18)` 不存在，因为 `gcd(12,18)=6`。最大公约数不是 1，
因此函数抛出 `ValueError`，而不是返回一个错误数字。

### 5.5 在 RSA 中的两个方向

正常 RSA 先确定 `e`，再计算：

```text
d = e^(-1) mod phi
```

弱 RSA 为了控制 `d` 的大小，会先选择较小的 `d`，再计算：

```text
e = d^(-1) mod phi
```

两者最终都满足 `e*d mod phi=1`。

---

## 6. generate_normal_rsa：生成正常 RSA 参数

### 6.1 函数目标

`generate_normal_rsa(bits)` 生成一组模数 `n` 恰好为指定二进制位数的 RSA 参数，
返回 `n、e、d、p、q、phi`。公开信息是 `n、e`，其余字段由生成端保存。

### 6.2 输入检查

函数要求 `bits>=17`。因为代码固定使用 `e=65537`，必须让 `phi` 有可能大于
65537；位数太小时无法满足这个条件。

### 6.3 为什么这样计算 prime_bits

```python
prime_bits = (bits + 1) // 2
```

因为 `n=p*q`，如果希望 `n` 大约为 `bits` 位，`p、q` 各取大约一半位数。对
奇数位请求，`(bits+1)//2` 相当于向上取整。

### 6.4 循环中的每一步

1. 调用 `getPrime(prime_bits)` 生成 `p、q`。素数生成属于库功能。
2. 如果 `p==q`，重新生成，因为 RSA 要使用两个不同素数。
3. 计算 `n=p*q`。
4. 若 `n.bit_length()!=bits`，重新生成。两个相同位数的数相乘，结果位数仍可能相差 1。
5. 计算 `phi=(p-1)*(q-1)`。
6. 固定 `e=65537`。
7. 检查 `e<phi` 且 `gcd(e,phi)==1`，否则重新生成。
8. 计算 `d=mod_inverse(e,phi)`。
9. 返回完整密钥字段。

`while True` 不是无条件死循环：候选不合格时 `continue`，找到满足全部条件的参数
以后通过 `return` 结束。

### 6.5 最终保证

因为 `d` 是 `e` 的模逆，所以：

```text
e*d mod phi = 1
```

这正是 RSA 公钥指数和私钥指数之间的核心关系。

### 6.6 实现边界

我们实现的是 RSA 参数组织、条件检查、失败重试和模逆调用流程。`getPrime` 内部
怎样生成和检测素数不属于我们的实现。

### 6.7 答辩时的一句话解释

> 先用库生成两个不同且大小接近的素数，再检查乘积位数，计算 n 和 phi，固定
> e=65537，确认 e 与 phi 互素，最后通过模逆得到 d。

---

## 7. approximate_wiener_threshold：计算小 d 的近似标尺

### 7.1 函数目标

Wiener 定理中常用的小私钥指数条件是：

```text
d < n^(1/4) / 3
```

函数计算用于生成实验密钥的整数近似标尺：

```python
return isqrt(isqrt(n)) // 3
```

### 7.2 为什么调用两次 isqrt

```text
isqrt(n)             ≈ sqrt(n)
isqrt(isqrt(n))      ≈ sqrt(sqrt(n)) = n^(1/4)
isqrt(isqrt(n)) // 3 ≈ n^(1/4)/3
```

### 7.3 为什么不直接使用 n**0.25

2048-bit 的 `n` 很大。转换成普通浮点数后再计算四次方根，可能造成溢出或精度
损失。`isqrt` 始终使用整数，因此结果稳定。

### 7.4 贯穿示例

对 `n=90581`：

```text
isqrt(90581) = 300
isqrt(300)   = 17
17 // 3      = 5
```

所以近似标尺 `T=5`。

### 7.5 近似标尺与精确判断的区别

这个函数用于构造目标 `d`。是否真正满足严格不等式，交给下面的
`is_below_wiener_bound` 判断。

---

## 8. is_below_wiener_bound：精确判断 d 是否低于边界

### 8.1 等价变形

要判断：

```text
d < n^(1/4)/3
```

因为 `d、n` 都是正数，可以等价变形：

```text
d < n^(1/4)/3
3d < n^(1/4)
(3d)^4 < n
81*d^4 < n
```

所以代码是：

```python
return 81 * d**4 < n
```

整个判断只有整数运算，没有浮点误差。

### 8.2 贯穿示例

当 `d=5、n=90581`：

```text
81*5^4 = 50625 < 90581
```

函数返回 `True`。如果改成 `d=6`：

```text
81*6^4 = 104976 > 90581
```

函数返回 `False`。

### 8.3 为什么输入必须为正

上面的四次方变形建立在两边为正的前提下。RSA 的 `d、n` 本来也必须为正，所以
函数对非正输入抛出 `ValueError`。

---

## 9. _nearest_odd_coprime：寻找合法的小 d

### 9.1 函数目标

输入目标值 `target` 和 `phi`，寻找一个尽量接近 `target` 的 `d`，并满足：

```text
d > 1
d < phi
d 是奇数
gcd(d,phi) = 1
```

最后一个条件保证 `d` 在模 `phi` 下存在逆元，可以计算对应的 `e`。

### 9.2 为什么只检查奇数

`p、q` 是奇素数，所以 `p-1、q-1` 都是偶数，`phi=(p-1)(q-1)` 一定是偶数。
如果 `d` 也是偶数，那么 `gcd(d,phi)>=2`，不可能互素，所以不用检查偶数候选。

### 9.3 选择起点

```python
center = max(3, target)
if center % 2 == 0:
    center += 1
```

- `max(3,target)` 保证从大于 1 的值开始。
- 如果目标是偶数，就加 1 移动到上方奇数。

### 9.4 搜索顺序

`offset` 从 0 开始，每轮增加 2：

```text
center
center+2, center-2
center+4, center-4
center+6, center-6
...
```

代码先检查上方候选，再检查下方候选。发现位于合法范围且与 `phi` 互素的候选
以后立即返回。

### 9.5 具体例子

假设 `target=9、phi=198`：

1. `center=9`，但 `gcd(9,198)=9`，不合法。
2. `offset=2`，先检查 `upper=11`，但 `gcd(11,198)=11`，不合法。
3. 再检查 `lower=7`，`gcd(7,198)=1`，所以返回 7。

这说明函数不是随便找一个小奇数，而是在目标附近寻找能够求逆的候选。

### 9.6 为什么 center >= phi 要报错

RSA 指数必须小于 `phi`。如果目标本身达到或超过 `phi`，继续搜索会偏离函数的
设计目的，所以直接抛出 `ValueError`，让调用者知道输入比例不合理。

---

## 10. generate_weak_rsa：生成存在 Wiener 弱点的 RSA 密钥

### 10.1 与正常密钥生成的关键区别

正常 RSA：

```text
先固定 e=65537，再求 d=e^(-1) mod phi
```

弱 RSA：

```text
先故意选择较小的 d，再求 e=d^(-1) mod phi
```

弱密钥仍满足 RSA 的数学关系，只是私钥指数太小。

### 10.2 参数含义

```text
bits            希望 n 具有的二进制位数
d_target_ratio  希望 d 大约是边界标尺 T 的多少倍
```

例如 `d_target_ratio=0.5` 表示希望 `d≈0.5*T`。

### 10.3 生成基础参数

函数先使用 `getPrime` 生成两个大约一半位数的素数，并检查：

```text
p != q
n.bit_length() == bits
```

然后计算：

```text
n = p*q
phi = (p-1)(q-1)
```

不满足条件时重新生成。

### 10.4 计算目标 d

先计算 `threshold=approximate_wiener_threshold(n)`。然后把比例转换为精确分数。
例如 `0.5` 转成 `1/2`，避免把巨大整数与普通浮点数直接相乘。

若比例是 `numerator/denominator`，代码计算：

```python
scaled = ratio.numerator * threshold
target_d = (scaled + ratio.denominator // 2) // ratio.denominator
```

加上“分母的一半”再整除，相当于四舍五入到最近的整数。

### 10.5 选择合法 d 并计算 e

目标值不一定与 `phi` 互素，因此调用：

```python
d = _nearest_odd_coprime(target_d, phi)
e = mod_inverse(d, phi)
```

因为 `e` 是 `d` 的模逆，所以一定满足 `d*e mod phi=1`。

### 10.6 最后的合法性检查

```python
if not (1 < e < phi and (e * d) % phi == 1):
    raise AssertionError(...)
```

这个检查保证 `e` 位于合法范围，并且 `e、d` 确实互为模逆。如果失败，说明前面
的核心逻辑存在错误，因此不能返回错误密钥。

### 10.7 贯穿示例

假设库已经生成 `p=379、q=239`：

```text
n   = 379*239 = 90581
phi = 378*238 = 89964
T   = isqrt(isqrt(90581))//3 = 5
```

若目标比例为 1：

```text
target_d = 1*T = 5
gcd(5,89964) = 1
```

因此 `_nearest_odd_coprime` 返回 5。然后：

```text
e = mod_inverse(5,89964) = 17993
17993*5 = 89965 = 1 mod 89964
```

最终得到合法但脆弱的 RSA 密钥。

### 10.8 返回的诊断字段

除了 RSA 参数，函数还记录：

- 实际 `n` 位数。
- `d` 位数。
- 请求的目标比例。
- 边界近似值 `T`。
- 实际的 `d/T`。
- `d` 是否低于严格边界。
- 密钥生成耗时。

这些字段用于实验，不会传给攻击函数。

---

## 11. continued_fraction：计算连分数系数

### 11.1 什么是连分数

有理数可以写成：

```text
a0 + 1/(a1 + 1/(a2 + 1/(...)))
```

其中 `a0、a1、a2...` 是连分数系数。

### 11.2 函数怎样计算

函数维护两个整数 `a、b`，每轮执行：

```python
quotient, remainder = divmod(a, b)
coefficients.append(quotient)
a, b = b, remainder
```

也就是保存当前除法的商，再把除数和余数作为下一轮输入。余数变成 0 时结束。
这与欧几里得算法的除法过程相同，只是这里还保存了每轮的商。

### 11.3 具体例子：43/19

```text
43 = 2*19 + 5
19 = 3*5  + 4
5  = 1*4  + 1
4  = 4*1  + 0
```

把商依次保存，得到 `[2,3,1,4]`。

### 11.4 Wiener 示例中的 e/n

对贯穿示例：

```text
17993/90581 → [0,5,29,4,1,3,2,4,3]
```

第一个系数为 0，是因为 `e<n`，整数部分是 0。

### 11.5 为什么不用浮点数

RSA 的 `e、n` 可能有 2048 bit。浮点数无法精确保存这些整数的全部有效位。
连分数计算只使用整数除法和余数，因此不会丢失精度。

---

## 12. convergents：由连分数产生渐近分数

### 12.1 什么是渐近分数

依次截取连分数的前 1 项、前 2 项、前 3 项，每个前缀都对应一个分数。这些分数
叫渐近分数，它们会越来越接近原来的有理数。函数返回 `(分子,分母)`。

在 Wiener 攻击中，分子被解释为候选 `k`，分母被解释为候选 `d`。

### 12.2 递推公式

对当前系数 `a`：

```text
p = a*p_prev1 + p_prev2
q = a*q_prev1 + q_prev2
```

初始化为：

```text
p_prev2=0, p_prev1=1
q_prev2=1, q_prev1=0
```

这组初值能让第一个系数自然产生 `a/1`，不需要额外特殊分支。

### 12.3 具体例子：[2,3,1,4]

| 当前系数 a | 新分子 p | 新分母 q | 产生的分数 |
|---:|---:|---:|---:|
| 2 | 2 | 1 | 2/1 |
| 3 | 7 | 3 | 7/3 |
| 1 | 9 | 4 | 9/4 |
| 4 | 43 | 19 | 43/19 |

最后一个渐近分数就是原分数，因为输入本身是有理数。

### 12.4 为什么使用 yield

代码不是先把所有渐近分数存入列表，而是每得到一个就用 `yield` 交给调用者。
Wiener 攻击可以立即检查候选；如果已经成功，就不必继续生成后面的候选。

### 12.5 贯穿示例中的候选

`17993/90581` 的前几个渐近分数是：

```text
0/1, 1/5, 29/146, 117/589, ...
```

第二个渐近分数 `1/5` 正好对应 `k=1、d=5`。

---

## 13. wiener_attack：从公开密钥恢复小 d

### 13.1 攻击函数能看到什么

函数只有两个输入：

```text
e, n
```

它没有接收真实的 `d、p、q、phi`。这些秘密值只在生成端和测试端保存。

### 13.2 数学出发点

RSA 满足 `e*d mod phi=1`，因此存在某个整数 `k`，使：

```text
e*d - k*phi = 1
```

整理可得：

```text
k/d = e/phi - 1/(d*phi)
```

当 `d` 很小且 `p、q` 大小接近时，`phi` 与 `n` 很接近，所以：

```text
k/d ≈ e/n
```

Wiener 定理说明，在满足条件时，正确的 `k/d` 会出现在 `e/n` 的渐近分数中。

### 13.3 生成候选

```python
coefficients = continued_fraction(e, n)
for index, (k, candidate_d) in enumerate(convergents(coefficients)):
```

每个渐近分数的分子作为 `k`，分母作为候选 `d`。

### 13.4 检查一：k 不能为 0

因为 `e<n`，第一个渐近分数通常是 `0/1`。后面要用 `k` 作除数，所以 `k=0`
时直接跳过。

### 13.5 检查二：能否得到整数 phi

由 `e*d-k*phi=1` 可得：

```text
phi = (e*d-1)/k
```

代码先计算 `ed_minus_one=e*candidate_d-1`。如果它不能被 `k` 整除，候选必定
错误。能整除时才计算 `candidate_phi`，并要求它为正数。

### 13.6 检查三：能否恢复整数 p、q

RSA 中：

```text
phi = (p-1)(q-1)
     = pq-p-q+1
     = n-(p+q)+1
```

因此：

```text
p+q = n-phi+1
```

代码把它记为 `factor_sum`。因为 `p+q=factor_sum` 且 `p*q=n`，所以 `p、q`
是下面二次方程的两个根：

```text
x^2 - factor_sum*x + n = 0
```

判别式是 `delta=factor_sum^2-4n`。如果小于 0，就不可能得到所需整数根。

### 13.7 检查四：判别式必须是完全平方数

二次方程的根是：

```text
p = (factor_sum + sqrt(delta))/2
q = (factor_sum - sqrt(delta))/2
```

代码使用：

```python
root = isqrt(discriminant)
if root * root != discriminant:
    continue
```

`isqrt` 返回向下取整的整数平方根，所以还要用 `root*root` 检查它是否真的等于
判别式。接着检查两个分子是否为偶数，保证除以 2 后仍是整数。

### 13.8 最终决定性验证

得到候选 `p、q` 后，代码仍要检查：

```text
p > 1
q > 1
p*q == n
(p-1)*(q-1) == candidate_phi
e*candidate_d mod candidate_phi == 1
```

全部成立才返回结果，避免把偶然通过部分条件的候选误判成私钥。

### 13.9 完整攻击示例

攻击者拿到：

```text
e = 17993
n = 90581
```

连分数和渐近分数为：

```text
17993/90581
→ [0,5,29,4,1,3,2,4,3]
→ 0/1, 1/5, 29/146, 117/589, ...
```

第一个候选 `0/1` 中 `k=0`，跳过。第二个候选是：

```text
k = 1
candidate_d = 5
```

计算候选 `phi`：

```text
e*d - 1 = 17993*5 - 1 = 89964
candidate_phi = 89964/1 = 89964
```

计算候选因数和：

```text
factor_sum = n-phi+1
           = 90581-89964+1
           = 618
```

计算判别式：

```text
delta = 618^2 - 4*90581
      = 19600
      = 140^2
```

恢复两个根：

```text
p = (618+140)/2 = 379
q = (618-140)/2 = 239
```

最终验证：

```text
379*239 = 90581
(379-1)*(239-1) = 89964
17993*5 mod 89964 = 1
```

全部成立，因此攻击返回 `d=5、p=379、q=239`。

### 13.10 为什么普通 RSA 通常返回 None

正常 RSA 的 `d` 通常很大，不满足 Wiener 攻击的小私钥指数条件，因此正确的
`k/d` 通常不会作为所需渐近分数出现。检查完所有候选仍未成功时返回 `None`。

`None` 只表示这次 Wiener 攻击没有恢复私钥，不能证明密钥不存在其他问题。

### 13.11 答辩时的一句话解释

> 我们对 e/n 做连分数展开，把每个渐近分数看作候选 k/d，再由
> phi=(ed-1)/k 推回 phi，最后通过二次方程恢复并严格验证 p、q。

---

## 14. 最容易混淆的四个问题

### 14.1 为什么正常 RSA 求 d，弱 RSA 却先选 d？

正常 RSA 的目标是安全，所以固定常用的 `e=65537`，再求对应的 `d`。弱 RSA 的
目标是制造 Wiener 漏洞，所以必须控制 `d` 很小，再反过来求合法的 `e`。

### 14.2 为什么 d 小，但密钥仍然合法？

因为它仍满足：

```text
n=pq
phi=(p-1)(q-1)
e*d mod phi=1
```

“合法”表示数学关系成立，不表示安全。

### 14.3 为什么渐近分数是 k/d，而不是 d/k？

从 `ed-k*phi=1` 出发可以得到 `k/d≈e/phi≈e/n`，所以 `e/n` 的渐近分数
分子对应 `k`，分母对应 `d`。

### 14.4 为什么找到能整除的 phi 还不能直接认为成功？

错误候选也可能偶然满足整除条件。只有候选 `phi` 能恢复出整数 `p、q`，并且满足
`p*q=n` 等全部 RSA 关系，才能确定候选正确。

---

## 15. 答辩讲解顺序建议

如果时间有限，可以按下面顺序讲：

1. `gcd → extended_gcd → mod_inverse`：说明怎样得到合法的模逆关系。
2. 对比 `generate_normal_rsa` 和 `generate_weak_rsa`：突出“正常密钥先定 e，弱密钥先选小 d”。
3. 说明 `approximate_wiener_threshold` 和 `is_below_wiener_bound`：一个用于构造，一个用于精确判断。
4. 用 `43/19` 解释 `continued_fraction` 和 `convergents`。
5. 用 `e=17993、n=90581` 完整走一遍 `wiener_attack`。
6. 最后说明攻击函数只接收 `e、n`，并强调库函数边界。

必须能够现场写出的三条关系是：

```text
e*d mod phi = 1
e*d - k*phi = 1
phi = n - (p+q) + 1
```

它们分别连接了 RSA 密钥生成、Wiener 候选和因数恢复，是整个项目的主线。
