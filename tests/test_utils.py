"""
    1. pytest finds this function because its name starts with test_.
    2. assert means "this must be true, or fail the test."
    3. We call slugify("Hello World!") and check it returns exactly "hello-world".
    4. If it returns anything else — test fails, and pytest tells you exactly what it got instead.
    
    
    
"""



from app.utils import (
    slugify,
    word_frequency,
    is_prime,
    fibonacci,
    is_palindrome,
    flatten_json,
)

def test_slugify_basic():
    assert slugify("Hello World!") == "hello-world"
    
def test_slugify_extra_spaces():
    assert slugify("  Multiple   Spaces  ") == "multiple-spaces"
    
def test_word_frequency():
    result = word_frequency("the cat sat on the mat the cat ran")
    assert result["the"] == 3
    assert result["cat"] == 2
    assert result["mat"] == 1
    
def test_is_prime_true_cases():
    assert is_prime(2) is True
    assert is_prime(17) is True


def test_is_prime_false_cases():
    assert is_prime(1) is False
    assert is_prime(0) is False
    assert is_prime(-5) is False
    assert is_prime(9) is False
    


def test_fibonacci():
    assert fibonacci(6) == [0, 1, 1, 2, 3, 5]


def test_fibonacci_zero():
    assert fibonacci(0) == []
    
    
def test_is_palindrome_true():
    assert is_palindrome("A man a plan a canal Panama") is True


def test_is_palindrome_false():
    assert is_palindrome("Hello World") is False


def test_flatten_json():
    nested = {"a": {"b": 1, "c": {"d": 2}}, "e": 3}
    flat = flatten_json(nested)
    assert flat == {"a.b": 1, "a.c.d": 2, "e": 3}
