# 代码讲解

## 1. 总体流程

程序分成四层：

1. 数论层：计算最大公约数、模逆、整数平方根和生成素数。
2. RSA 层：生成普通密钥或故意选择小 d 的弱密钥。
3. 攻击层：计算 e/n 的连分数，逐个验证渐近分数给出的候选 d。
4. 演示与实验层：验证解密、记录 CSV、统计成功率和绘图。

攻击模块只接收 e 和 n。真实 d、p、q 只保留在生成器、fixture 和测试端，用来
判断恢复结果是否正确。

## 2. 课程要求自行实现并讲解的部分

源码中使用以下统一标记：

```text
# 【课程核心代码】……
```

被标记的内容是答辩需要重点说明的部分，也是作者声明必须逐项填写的部分：

| 模块 | 核心函数 | 需要讲清楚的内容 |
|---|---|---|
| `number_theory.py` | `gcd` | 欧几里得循环为什么保持 GCD 不变 |
| `number_theory.py` | `integer_sqrt` | 牛顿迭代及为何不使用浮点数 |
| `number_theory.py` | `extended_gcd` | Bézout 系数如何随余数更新 |
| `number_theory.py` | `mod_inverse` | 逆元存在条件和系数规范化 |
| `number_theory.py` | `is_probable_prime` | n-1 的分解、见证和概率性 |
| `number_theory.py` | `generate_prime` | 如何保证准确位数、奇数和安全随机性 |
| `rsa.py` | `rsa_encrypt`、`rsa_decrypt` | 模幂和输入范围 |
| `rsa.py` | `generate_normal_rsa` | p、q、phi、e、d 的关系和重试条件 |
| `weak_key_generator.py` | `generate_weak_rsa` | 如何选小 d，同时保持 RSA 等式成立 |
| `continued_fraction.py` | `continued_fraction` | 欧几里得商如何形成连分数系数 |
| `continued_fraction.py` | `convergents` | 分子、分母递推公式 |
| `wiener_attack.py` | `wiener_attack` | 从候选 k/d 恢复 phi，并用判别式验证 p、q |

实验脚本、测试和绘图也要填写实际贡献者，但它们不应代替上述核心数学实现。

## 3. number_theory.py

### gcd

每轮把 (a, b) 更新为 (b, a mod b)。因为能同时整除 a、b 的整数，也能同时
整除 b、a mod b，所以最大公约数不变。当 b 变成 0 时，a 就是结果。

### integer_sqrt

2048-bit 整数不能先转成 float 再求平方根。函数从真实平方根上方开始，用

```text
next_x = (x + n // x) // 2
```

做牛顿迭代。所有除法均为整数除法，最终返回 floor(sqrt(n))。

### extended_gcd 与 mod_inverse

扩展欧几里得除了保存余数，还保存每个余数相对于原始 a、b 的系数。因此最终
得到 a*x + b*y = gcd(a,b)。当 GCD 为 1 时，对等式取模 m，可知 x 是 a 的
模逆；返回 x % m，把结果放入标准剩余区间。

### Miller–Rabin

先把 n-1 写成 2^s*d，其中 d 为奇数。每轮随机选择一个底数 a，先算
a^d mod n，再反复平方。若既没有得到 1，也没有在规定位置得到 -1，就能确认
n 是合数。通过所有轮次只表示大概率素数。

generate_prime 强制最高位为 1 来保证准确位数，强制最低位为 1 来保证奇数，
并使用 secrets.SystemRandom 采样候选。

## 4. rsa.py

普通密钥生成步骤：

1. 生成两个不同且等位数的素数 p、q。
2. 计算 n=pq 和 phi=(p-1)(q-1)。
3. 使用 e=65537，并检查 gcd(e,phi)=1。
4. 计算 d=e 在模 phi 下的逆元。
5. 检查 n.bit_length() 与请求值完全相同。

加密计算 c=m^e mod n，解密计算 m=c^d mod n。Python 的三参数 pow 只负责
高效模幂，密钥生成和攻击数学过程仍由项目代码实现。

## 5. weak_key_generator.py

弱密钥不是随便修改 d。程序先生成合法 p、q、n、phi，再计算近似标尺

```text
T = floor(sqrt(sqrt(n))) // 3
```

然后在 ratio*T 附近寻找大于 1、为奇数且与 phi 互素的 d，最后计算
e=d^(-1) mod phi。这样仍满足 e*d mod phi = 1，只是 d 被故意选得很小。

精确边界判断使用 81*d^4 < n，与 d < n^(1/4)/3 等价，没有浮点误差。

## 6. continued_fraction.py

continued_fraction 对分子、分母执行欧几里得除法，每轮保存商。例如：

```text
43/19 -> [2, 3, 1, 4]
```

convergents 对每个系数 a 使用：

```text
p = a*p_prev1 + p_prev2
q = a*q_prev1 + q_prev2
```

得到 (2,1)、(7,3)、(9,4)、(43,19)。

## 7. wiener_attack.py

RSA 满足 e*d-k*phi=1。当 d 足够小且 p、q 大小接近时，k/d 会出现在 e/n 的
渐近分数中。对每个候选 k、d：

1. k 不能为 0。
2. e*d-1 必须能被 k 整除，否则 phi 不是整数。
3. 计算候选 phi=(e*d-1)/k。
4. 由 phi=n-(p+q)+1 得到 s=p+q=n-phi+1。
5. p、q 是 x^2-s*x+n=0 的根，判别式为 delta=s^2-4n。
6. delta 必须是完全平方数，两个根必须是整数。
7. 最后严格检查 p*q=n、phi=(p-1)(q-1) 和 e*d mod phi=1。

只有全部检查通过才返回 AttackResult，否则继续检查下一个渐近分数。

## 8. 实验代码

run_experiments.py 实现：

- E1：固定 n 位数，改变目标 d/T，画成功率柱状图。
- E2：固定小 d 比例，改变 n 位数，画攻击时间折线图。
- E3：对普通 RSA 和弱 RSA 调用完全相同的攻击入口，输出对照 CSV。

密钥生成时间和攻击时间分别测量。每行 CSV 对应一次真实 trial，不使用硬编码
结果。`--quick` 仅用于检查流程，最终汇报应使用至少 10 次完整实验。

## 9. 标准库和第三方库负责什么

以下内容不应声称为自行实现：

- secrets.SystemRandom：提供随机比特。
- pow(x, exponent, modulus)：高效模幂。
- dataclass：保存结构化结果。
- time.perf_counter：计时。
- csv：写入 CSV。
- matplotlib：绘图。
- argparse：解析命令行参数。

项目自行实现的是这些工具之上的 RSA 数学流程、弱密钥构造、连分数和候选验证。
