# -*- coding: utf-8 -*-
"""Display policy for explicit NOTICE/BIG_NOTICE channels, independent of scope."""
import re

ASSET_ROOT = 'd:/ymir work/ui/game/notice_01_04/'
METEOR_STYLE = 5
METEOR_ASSET_ROOT = 'd:/ymir work/ui/game/althea_meteor_notice/'
MAX_QUEUE = 64
DEDUP_SECONDS = 2.0
TIMING = {1: (0.25, 4.5, 0.25), 4: (0.55, 5.0, 0.35), METEOR_STYLE: (0.25, 5.0, 0.35)}
COLORS = {'body': (0.95, 0.925, 0.875), 'title': (0.973, 0.863, 0.639)}
PROFILE_WIDTHS = (520, 780, 1040)


def profile(width, height):
    if width >= 2400 and height >= 1800:
        return 1040
    if width >= 1600 and height >= 1300:
        return 780
    return 520


def meteor_profile(width, height):
    # Select an authored raster; 4K remains 1040, larger viewports use 1560.
    if width >= 4800 and height >= 2700:
        return 1560
    return profile(width, height)


def meteor_layout(text, width, measure):
    scale = width / 520.0
    font = 'Tahoma:%dba' % round(22 * scale)
    gap = max(3, round(5 * scale))
    limit = round(61 * scale)
    pages, page, used = [], [], 0
    for value in wrap(text, round(300 * scale), lambda value: measure(font, value)[0]):
        height = max(1, measure(font, value)[1])
        if page and used + gap + height > limit:
            pages.append(page)
            page, used = [], 0
        if page:
            used += gap
        page.append({'text': value, 'font': font, 'height': height, 'color': 'title'})
        used += height
    if page:
        pages.append(page)
    for page in pages:
        total = sum(row['height'] for row in page) + gap * (len(page)-1)
        y = round(86 * scale) + max(0, (limit-total)//2)
        for row in page:
            row['y'] = y
            y += row['height'] + gap
    return 'meteor', pages or [[]]


def clean_text(text):
    if isinstance(text, bytes):
        try:
            text = text.decode('utf-8')
        except UnicodeDecodeError:
            text = text.decode('cp1250', 'replace')
    if not isinstance(text, str):
        return ''
    # Native receive normally strips color markup. Local AFK callers use this
    # same board, so normalize here as well, without guessing message meaning.
    text = re.sub(r'\|c[0-9a-fA-F]{8}', '', text).replace('|r', '')
    text = text.replace('[ENTER]', '\n').replace('\r\n', '\n').replace('\r', '\n')
    return '\n'.join(' '.join(line.split()) for line in text.split('\n')).strip()


def wrap(text, max_width, measure):
    """Keep all codepoints, including a single token wider than the panel."""
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split():
            candidate = (line + ' ' + word) if line else word
            if measure(candidate) <= max_width:
                line = candidate
                continue
            if line:
                lines.append(line)
                line = ''
            # Split long tokens using measured characters, never byte slices.
            for char in word:
                if line and measure(line + char) > max_width:
                    lines.append(line)
                    line = ''
                line += char
        if line:
            lines.append(line)
    return lines


def font_name(style, title, scale):
    # Production uses native Tahoma for every family alias. The explicit 'a'
    # modifier preserves grayscale edges and opacity without changing metrics.
    if style == 4 and title:
        return 'Tahoma:%dba' % round(22 * scale)
    return 'Tahoma:%da' % round((15 if style == 4 else 16) * scale)


def layout(text, style, width, measure):
    """Measure native fonts before choosing a carrier and bounded pages.

    BIG_NOTICE's first explicit paragraph is its title; subsequent paragraphs
    are body. This wire structure does not classify content by keywords.
    """
    if style == METEOR_STYLE:
        return meteor_layout(text, width, measure)
    scale = width / 520.0
    available = round(396 * scale)
    paragraphs = text.split('\n')
    rows = []
    for i, paragraph in enumerate(paragraphs):
        title = style == 4 and i == 0
        name = font_name(style, title, scale)
        for line in wrap(paragraph, available, lambda value: measure(name, value)[0]):
            height = max(1, measure(name, line)[1])
            rows.append({'text': line, 'font': name, 'height': height,
                         'color': 'title' if title else 'body'})
    if not rows:
        return 'notice', [[]]
    role = 'notice' if style == 1 and len(rows) == 1 else 'result'
    safe_top, safe_height = ((3, 33) if role == 'notice' else
                             ((10, 64) if style == 1 else (32, 68)))
    limit = round(safe_height * scale)
    gap = max(3, round(5 * scale))
    pages, page, used = [], [], 0
    for row in rows:
        needed = row['height'] + (gap if page else 0)
        if page and used + needed > limit:
            pages.append(page)
            page, used = [], 0
        if page:
            used += gap
        page.append(row)
        used += row['height']
    if page:
        pages.append(page)
    for page in pages:
        total = sum(row['height'] for row in page) + gap * (len(page)-1)
        y = round(safe_top * scale) + max(0, (limit-total)//2)
        for row in page:
            row['y'] = y
            y += row['height'] + gap
    return role, pages


def animation(style, elapsed, hold=None):
    enter, default_hold, leave = TIMING[style]
    hold = default_hold if hold is None else hold
    if elapsed < enter:
        p = max(0.0, elapsed / enter)
        eased = 1.0 - (1.0-p)**3
        if style in (1, METEOR_STYLE):
            return {'art': eased, 'text': eased, 'reveal': 1.0,
                    'offset': round(-12 * (1.0-eased)) if style == 1 else 0, 'done': False}
        return {'art': 1.0, 'text': max(0.0, min(1.0, (elapsed-0.2)/0.25)),
                'reveal': eased, 'offset': 0, 'done': False}
    alpha = max(0.0, min(1.0, 1.0 - (elapsed-enter-hold)/leave))
    return {'art': alpha, 'text': alpha, 'reveal': 1.0, 'offset': 0,
            'done': elapsed >= enter+hold+leave}


def reveal_bands(width, progress, count=7):
    """Disjoint pixel crops of one unchanged texture; feather at the leading edge."""
    if progress >= 1.0:
        return [(0, width, 1.0)]
    feather = max(1, round(28 * width / 520.0))
    edge = round(-feather + (width+2*feather) * progress)
    solid = max(0, min(width, edge-feather))
    bands = [(0, solid, 1.0)] if solid else []
    for i in range(count-1):
        left = max(0, min(width, round(edge-feather+i*feather/(count-1))))
        right = max(0, min(width, round(edge-feather+(i+1)*feather/(count-1))))
        if right > left:
            bands.append((left, right, 1.0-(i+0.5)/(count-1)))
    return bands


class NoticeQueue:
    def __init__(self):
        self.pending = []
        self.last = None

    def clear(self):
        self.pending = []
        self.last = None

    def add(self, text, style, now):
        text = clean_text(text)
        if not text:
            return False
        identity = (style, text)
        if self.last and self.last[:2] == identity and now-self.last[2] < DEDUP_SECONDS:
            return False
        self.last = (style, text, now)
        if len(self.pending) >= MAX_QUEUE:
            ordinary = next((i for i, entry in enumerate(self.pending) if entry[0] == 1), 0)
            self.pending.pop(ordinary)
        self.pending.append((style, text))
        return True

    def pop(self):
        return self.pending.pop(0) if self.pending else None
