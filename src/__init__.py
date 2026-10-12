"""RSA Wiener 攻击的教学实现。

本包有意将密钥生成、连分数计算和攻击过程放在相互独立的模块中。
尤其需要注意，src.wiener_attack 不会接收或导入密钥生成器产生的
任何私钥信息。
"""

from .rsa import RSAKeyPair, rsa_decrypt, rsa_encrypt
from .wiener_attack import AttackResult, wiener_attack

__all__ = [
    "AttackResult",
    "RSAKeyPair",
    "rsa_decrypt",
    "rsa_encrypt",
    "wiener_attack",
]
