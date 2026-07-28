"""
Pure utility functions.
Kept separate from FastAPI routing so they can be unit tested
without spinning up the app or making HTTP calls.
"""

import re


def slugify(text: str) -> str:
    """'Hello World!' -> 'hello-world'"""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)   # drop punctuation
    text = re.sub(r"[\s-]+", "-", text)        # collapse spaces/dashes
    return text.strip("-")


def word_frequency(text: str) -> dict:
    """Return {word: count} for a block of text, case-insensitive."""
    words = re.findall(r"[a-zA-Z']+", text.lower())
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return freq



def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    return True

def fibonacci(n: int) -> list[int]:
    """First n Fibonacci numbers."""
    if n <= 0:
        return []
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq[:n]


def is_palindrome(text: str) -> bool:
    cleaned = re.sub(r"[^a-z0-9]", "", text.lower())
    return cleaned == cleaned[::-1]


def flatten_json(data: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten nested dict into dot-notation keys.
    {"a": {"b": 1}} -> {"a.b": 1}
    """
    items = {}
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_json(v, new_key, sep))
        else:
            items[new_key] = v
    return items
