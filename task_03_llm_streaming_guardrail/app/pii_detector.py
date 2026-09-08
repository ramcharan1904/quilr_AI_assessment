import re

EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SSN = re.compile(r"\b\d{3}[- ]\d{2}[- ]\d{4}\b")
CARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

# SSN/card matches top out around 20-24 chars; email has no hard upper bound, so this
# is a practical cutoff, not a guarantee - StreamingRedactor uses it to size the
# context window it re-scans on every feed() call. Emails longer than this can still
# be split; there's no way to bound that without buffering the whole message.
MAX_PATTERN_LENGTH = 64


def _luhn_valid(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _redact_card(match: re.Match) -> str:
    digits = re.sub(r"\D", "", match.group())
    if 13 <= len(digits) <= 19 and _luhn_valid(digits):
        return "[REDACTED]"
    return match.group()


def redact(text):
    text = EMAIL.sub("[REDACTED]", text)
    text = SSN.sub("[REDACTED]", text)
    return CARD.sub(_redact_card, text)


def find_match_spans(text):
    """(start, end) for every span redact() would replace. Used by the streaming
    buffer to detect a match that straddles its emit boundary, without relying on
    substitution-shortened text - see StreamingRedactor.feed()."""
    spans = [m.span() for m in EMAIL.finditer(text)]
    spans += [m.span() for m in SSN.finditer(text)]
    for m in CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn_valid(digits):
            spans.append(m.span())
    return spans
