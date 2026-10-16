"""Measured wrapping for native skill names, descriptions and bonus rows."""


def Wrap(text, width, measure):
    lines = []
    for paragraph in text.replace('\\n', '\n').splitlines():
        line = ''
        for word in paragraph.split():
            candidate = line + ' ' + word if line else word
            if measure(candidate) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
                line = ''
            for char in word:
                if line and measure(line + char) > width:
                    lines.append(line)
                    line = ''
                line += char
        if line:
            lines.append(line)
    return lines
