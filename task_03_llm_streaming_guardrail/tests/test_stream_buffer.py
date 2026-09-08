import pytest

from app.pii_detector import redact as direct_redact
from app.stream_buffer import StreamingRedactor


def _run(chunks):
    r = StreamingRedactor()
    out = "".join(r.feed(c) for c in chunks)
    out += r.flush()
    return out


def test_email_split_across_chunks():
    out = _run(["Hello, my email is ali", "ce@example.com and bye"])
    assert "[REDACTED]" in out
    assert "alice@example.com" not in out


def test_card_split_across_many_small_chunks():
    text = "Card: 4111 1111 1111 1111 thanks"
    chunks = [text[i:i + 3] for i in range(0, len(text), 3)]
    out = _run(chunks)
    assert "[REDACTED]" in out
    assert "4111" not in out


def test_ssn_split_across_chunks():
    out = _run(["SSN is 123-", "45-6789 done"])
    assert "[REDACTED]" in out
    assert "123-45-6789" not in out


def test_non_pii_text_passes_through_unchanged():
    out = _run(["Just a normal ", "sentence with no secrets in it at all."])
    assert out == "Just a normal sentence with no secrets in it at all."


def test_order_number_is_not_falsely_redacted():
    out = _run(["Order number 1234567890123 was placed"])
    assert "[REDACTED]" not in out
    assert "1234567890123" in out


def test_buffer_stays_bounded():
    r = StreamingRedactor()
    for _ in range(1000):
        r.feed("x" * 50)
    assert len(r.buffer) <= r.tail_size


# Realistic LLM streams send a handful of characters per delta - much smaller than
# any of the PII patterns being matched. Redacting only each newly-exposed sliver in
# isolation (rather than a proper lookahead window) would tear these apart across
# many separate feed() calls and let them through unredacted; regression coverage
# for exactly that failure mode, at several delta sizes including the extreme of
# one character at a time.
MULTI_PII_TEXT = (
    "Reach alice@example.com or bob@test.co, card 4111 1111 1111 1111, "
    "and SSN 123-45-6789, thanks for reading this rather long message."
)


@pytest.mark.parametrize("chunk_size", [1, 2, 3, 5, 8, 13, 21])
def test_multiple_pii_split_across_small_realistic_deltas(chunk_size):
    chunks = [MULTI_PII_TEXT[i:i + chunk_size] for i in range(0, len(MULTI_PII_TEXT), chunk_size)]
    assert _run(chunks) == direct_redact(MULTI_PII_TEXT)
