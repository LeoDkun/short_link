"""Base62 短码编解码。

用自增主键 id 做 base62 编码，天然唯一、无需冲突重试。加一个偏移量，
让最短的码也有 5 位、且不会暴露成 0/1/2 这种可遍历的连续序列。
"""

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(ALPHABET)
ID_OFFSET = 100_000_000


def encode(number: int) -> str:
    number += ID_OFFSET
    chars: list[str] = []
    while number > 0:
        number, rem = divmod(number, BASE)
        chars.append(ALPHABET[rem])
    return "".join(reversed(chars))


def decode(code: str) -> int:
    number = 0
    for ch in code:
        number = number * BASE + ALPHABET.index(ch)
    return number - ID_OFFSET
