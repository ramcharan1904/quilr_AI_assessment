from .pii_detector import MAX_PATTERN_LENGTH, find_match_spans, redact

# Tail must be at least as long as the longest pattern redact() can match, so a
# pattern straddling two feed() calls is never released before it's complete.
# Sized to the pattern length (not an arbitrary round number) to keep the
# cold-start buffering delay - and therefore time-to-first-token - as small as
# the safety guarantee allows.
DEFAULT_TAIL_SIZE = MAX_PATTERN_LENGTH


class StreamingRedactor:
    def __init__(self, tail_size=DEFAULT_TAIL_SIZE):
        self.buffer = ""
        self.tail_size = tail_size

    def feed(self, chunk):
        self.buffer += chunk
        boundary = len(self.buffer) - self.tail_size
        if boundary <= 0:
            return ""
        # A match that starts before the boundary but ends after it would be torn
        # in half if we cut here - pull the boundary back to just before any such
        # match so it stays whole in the buffer until more text confirms it.
        for start, end in find_match_spans(self.buffer):
            if start < boundary < end:
                boundary = min(boundary, start)
        if boundary <= 0:
            return ""
        safe_part = self.buffer[:boundary]
        self.buffer = self.buffer[boundary:]
        return redact(safe_part)

    def flush(self):
        result = redact(self.buffer)
        self.buffer = ""
        return result
