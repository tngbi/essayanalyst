from analyst.input_validation import count_words, validate_essay


def test_count_words():
    assert count_words("") == 0
    assert count_words("   \n  ") == 0
    assert count_words("one two three") == 3


def test_validate_empty():
    valid, msg = validate_essay("   ")
    assert not valid
    assert "empty" in msg


def test_validate_min_words():
    valid, msg = validate_essay("word " * 10, min_words=50)
    assert not valid
    assert "at least" in msg


def test_validate_max_words():
    valid, msg = validate_essay("word " * 6000, max_words=5000)
    assert not valid
    assert "exceeds" in msg


def test_validate_good():
    valid, msg = validate_essay("word " * 200)
    assert valid
    assert msg == ""
