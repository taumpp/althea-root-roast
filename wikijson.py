"""Cooperative JSON reader: bounded token scans, no whole-document json.loads."""
import json
import re

# Transport resource limits, not gameplay/content values.
MAX_DEPTH = 64
MAX_TOKEN = 64 * 1024
SCAN_CHARS = 256
CONTAINER_CHARS = 2048
# Decode at most one bounded subtree. Inspect structural depth only after
# successful JSON decoding, so escaped delimiters cannot become structure.
_CONTAINER_DECODER = json.JSONDecoder()
_JSON_STRINGS = re.compile(r'"(?:[^"\\]|\\.)*"')
# The standard decoder already validates syntax. This bounded regular grammar
# checks nesting in the native regex engine instead of one Python call per
# delimiter. Alternatives are disjoint; each bracket consumes one depth level.
_structure = r'[^{}\[\]]*'
for _depth in range(MAX_DEPTH):
    _structure = r'(?:[^{}\[\]]|[\[{]' + _structure + r'[\]}])*'
_BOUNDED_STRUCTURE = re.compile(_structure)
del _structure, _depth

# Fast path for ordinary short tokens; long tokens retain cooperative scanning.
_STRING = re.compile(r'[^"\\]*(?:\\.[^"\\]*)*"')


class Reader(object):
    def __init__(self, text):
        self.text, self.position, self.result = text, 0, None

    def Space(self):
        start = self.position
        while self.position < len(self.text) and self.text[self.position] in ' \t\r\n':
            self.position += 1
            if (self.position-start) % SCAN_CHARS == 0:
                yield

    def Take(self, char):
        if self.position >= len(self.text) or self.text[self.position] != char:
            raise ValueError('JSON punctuation')
        self.position += 1

    def String(self):
        start = self.position
        self.Take('"')
        end = _STRING.match(self.text, self.position, min(len(self.text), start+SCAN_CHARS))
        if end is None:
            escaped = False
            while self.position < len(self.text):
                char = self.text[self.position]
                self.position += 1
                if self.position-start > MAX_TOKEN:
                    raise ValueError('JSON token size')
                if not escaped and char == '"':
                    return json.loads(self.text[start:self.position])
                escaped = char == '\\' and not escaped
                if (self.position-start) % SCAN_CHARS == 0:
                    yield
            raise ValueError('JSON string incomplete')
        value, position = json.decoder.scanstring(self.text, self.position, True)
        if position != end.end():
            raise ValueError('JSON string framing')
        self.position = position
        return value

    def Value(self, depth=0):
        yield
        if depth > MAX_DEPTH:
            raise ValueError('JSON nesting')
        yield from self.Space()
        if self.position >= len(self.text):
            raise ValueError('JSON missing value')
        char = self.text[self.position]
        if char == '"':
            return (yield from self.String())
        if char in '[{':
            # Standard decoding is bounded by source length, never the whole
            # catalogue. Incomplete/large/deep subtrees use the yielding path.
            chunk = self.text[self.position:self.position+CONTAINER_CHARS]
            try:
                result, consumed = _CONTAINER_DECODER.raw_decode(chunk)
            except (ValueError, RecursionError):
                pass
            else:
                structure = _JSON_STRINGS.sub('', chunk[:consumed])
                # Prefix depth accounts for the cooperative parent's nesting.
                if _BOUNDED_STRUCTURE.fullmatch('['*depth+structure+']'*depth):
                    self.position += consumed
                    return result
            object_ = char == '{'
            end = '}' if object_ else ']'
            result = {} if object_ else []
            self.position += 1
            yield from self.Space()
            if self.position < len(self.text) and self.text[self.position] == end:
                self.position += 1
                return result
            while True:
                yield
                if object_:
                    self.Take('"')
                    self.position -= 1
                    key = yield from self.String()
                    yield from self.Space()
                    self.Take(':')
                value = yield from self.Value(depth+1)
                if object_:
                    result[key] = value
                else:
                    result.append(value)
                yield from self.Space()
                if self.position < len(self.text) and self.text[self.position] == end:
                    self.position += 1
                    return result
                self.Take(',')
                yield from self.Space()
        start = self.position
        while self.position < len(self.text) and self.text[self.position] not in ' \t\r\n,]}':
            self.position += 1
            if self.position-start > MAX_TOKEN:
                raise ValueError('JSON token size')
            if (self.position-start) % SCAN_CHARS == 0:
                yield
        value = json.loads(self.text[start:self.position])
        if isinstance(value, (dict, list)):
            raise ValueError('JSON scalar')
        return value

    def Read(self):
        value = yield from self.Value()
        yield from self.Space()
        if self.position != len(self.text):
            raise ValueError('JSON trailing data')
        self.result = value
