"""Compact public chat policy; independent of native UI modules."""
import builtins
import json
import math
import os
import re
import tempfile
import time
from urllib.parse import quote, unquote, urlsplit

REAL_OPEN = getattr(builtins, 'old_open', builtins.open)
MAX_TABS = 10
# Persisted filter IDs remain stable; 8 (EXP) is permanently unavailable.
AVAILABLE_FILTERS = (1, 2, 3, 4, 5, 6, 7, 9, 10)
MAX_TEXT_BYTES = 480
EMOJI = (
    ('happiness', ':)', 'Úsměv'), ('happy', ':D', 'Radost'),
    ('tongue', ':p', 'Jazyk'), ('amazed', ':o', 'Údiv'),
    ('angry', '>:(', 'Vztek'), ('in-love', ':3', 'Zamilovaný'),
    ('kiss', ':*', 'Polibek'), ('muted', ':X', 'Beze slov'),
    ('indifferent', ':\\', 'Nerozhodný'), ('evil', '>:D', 'Čertík'),
    ('quiet', ':||', 'Ticho'), ('surprised', ':O', 'Překvapení'),
    ('dead', 'xP', 'Mimo'), ('heart', '<3', 'Srdce'),
)
EMOJI_NAMES = tuple(row[0] for row in EMOJI)
RICH = re.compile(r'(\|H[^|\r\n]*\|h.*?\|h|\|I[^|\r\n]*\|i|\|c[0-9a-fA-F]{8}|\|r|\|\|)', re.S)
LINK = re.compile(r'^\|H([^|]*)\|h(.*?)\|h$', re.S)
WEB = re.compile(r'(?<![\w@/])(?:https?://|www\.|twitch\.tv(?:/|\b))[^\s<>"\x00-\x20|]*', re.I)
SENDER = re.compile(r'^[^\r\n]*?\|Hmsg:([^|]{1,24})\|h(.*?)\|h(?:\|r)?\s* : (.*)$', re.S)


def web_url(value):
    if not isinstance(value, str) or not value or len(value.encode('utf-8')) > 256:
        return None
    if re.search(r'[\x00-\x20\x7f\\|<>"\u202a-\u202e\u2066-\u2069]', value):
        return None
    if re.search(r'%(?:0[0-9a-f]|1[0-9a-f]|7f)', value, re.I):
        return None
    if value.lower().startswith(('twitch.tv', 'www.')):
        value = 'https://' + value
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in ('http', 'https') or not parts.hostname or parts.username or parts.password:
            return None
        if parts.port is not None and not 1 <= parts.port <= 65535:
            return None
        host = parts.hostname
        # Literal Unicode hosts must remain readable and cannot hide a new scheme.
        host.encode('idna')
        if not re.fullmatch(r'[\w.\-:\[\]]+', host, re.UNICODE):
            return None
    except (ValueError, UnicodeError):
        return None
    return value


def web_link(url, label=None):
    valid = web_url(url)
    if not valid:
        return label if label is not None else url
    return '|Hchatweb:%s|h%s|h' % (quote(valid, safe=''), label if label is not None else url)


def link_target(value):
    match = LINK.match(value)
    if match:
        value = match.group(1)
    kind, sep, encoded = value.partition(':')
    if not sep:
        return None, None
    if kind == 'chatweb':
        return kind, web_url(unquote(encoded))
    if kind == 'chatplayer':
        name = unquote(encoded)
        if 0 < len(name.encode('utf-8')) <= 24 and not re.search(r'[\s|:/\\\x00-\x1f]', name):
            return kind, name
    return None, None


def visible_text(value):
    value = re.sub(r'\|H[^|]*\|h(.*?)\|h', r'\1', value, flags=re.S)
    value = re.sub(r'\|I[^|]*\|i', '◊', value)
    value = re.sub(r'\|c[0-9a-fA-F]{8}|\|r', '', value)
    return value.replace('||', '|')


def linkify(value, system_links=False):
    def substitute(match):
        address = match.group(0)
        tail = ''
        while address and (address[-1] in '.,;!?' or
                           (address[-1] == ')' and address.count(')') > address.count('('))):
            tail = address[-1] + tail
            address = address[:-1]
        return web_link(address) + tail

    result = []
    for part in RICH.split(value):
        if not part:
            continue
        link = LINK.match(part)
        if link:
            # Player/web destinations come only from our header/text parser.
            # Retain established in-game item, pet and wiki links unchanged.
            kind = link.group(1).split(':', 1)[0]
            trusted_invite = False
            if system_links and kind == "guildinvite":
                from guildv2model import invitation_link_id
                trusted_invite = invitation_link_id(link.group(1)) is not None
            result.append(part if kind in ('item', 'petitem', 'wiki') or trusted_invite else visible_text(link.group(2)))
        elif RICH.fullmatch(part):
            result.append(part)
        else:
            result.append(WEB.sub(substitute, part))
    return ''.join(result)


def format_outgoing(value, emoji_filter):
    """Send URLs as plain text; convert emoticons only outside links/URLs."""
    result = []
    for part in RICH.split(value):
        if RICH.fullmatch(part):
            result.append(part)
            continue
        start = 0
        for match in WEB.finditer(part):
            result.append(emoji_filter(part[start:match.start()]))
            result.append(match.group(0))
            start = match.end()
        result.append(emoji_filter(part[start:]))
    return ''.join(result)


def message_text(row, own_name, timestamps, channel):
    _, _, raw, received, network_player, _ = row
    prefix = ('|cFF8E877B%s|r ' % time.strftime('%H:%M', time.localtime(received))) if timestamps else ''
    if channel:
        prefix += '|cFFA49983[%s]|r ' % channel
    match = SENDER.match(raw) if network_player else None
    if match:
        name, _, body = match.groups()
        kind, valid_name = link_target('chatplayer:' + quote(name, safe=''))
        if valid_name:
            sender = name if name.casefold() == own_name.casefold() else '|Hchatplayer:%s|h%s|h' % (quote(name, safe=''), name)
            return prefix + '|cFFE1C594' + sender + '|r: ' + linkify(body)
    return prefix + linkify(raw, system_links=not network_player)


def wrap_rich(value, width, measure):
    """Wrap native single-line runs, keeping rich links balanced on every line.

    The native renderer supplies actual font/image widths. Splitting long links
    repeats the same destination, never fragments an item payload or image tag.
    """
    width = max(8, width)
    lines, current, color = [], '', ''

    def flush():
        nonlocal current
        if visible_text(current).strip():
            lines.append(current + ('|r' if color else ''))
        current = color

    def append(piece, opening='', closing=''):
        nonlocal current
        full = opening + piece + closing
        if measure(current + full) <= width:
            current += full
            return
        if visible_text(current).strip():
            flush()
        if measure(current + full) <= width or piece.startswith('|I'):
            current += full
            return
        # An unbroken URL / item name can be wider than the viewport.
        while piece:
            low, high = 1, len(piece)
            while low < high:
                middle = (low + high + 1) // 2
                if measure(current + opening + piece[:middle] + closing) <= width:
                    low = middle
                else:
                    high = middle - 1
            current += opening + piece[:low] + closing
            piece = piece[low:]
            if piece:
                flush()

    for part in RICH.split(value):
        if not part:
            continue
        if re.fullmatch(r'\|c[0-9a-fA-F]{8}', part):
            color = part
            current += part
        elif part == '|r':
            color = ''
            current += part
        elif part.startswith('|I') or part == '||':
            append(part)
        else:
            match = LINK.match(part)
            opening, closing = ('|H' + match.group(1) + '|h', '|h') if match else ('', '')
            content = visible_text(match.group(2)) if match else part
            content = content.replace('\\n', '\n')
            for piece in re.findall(r'\n|[^\S\n]+|[^\s]+', content):
                if piece == '\n':
                    flush()
                elif piece.isspace() and not visible_text(current).strip():
                    continue
                else:
                    append(piece, opening, closing)
    flush()
    return lines or ['']


class RepeatShout:
    def __init__(self):
        self.running = False
        self.text = ''
        self.interval = 60
        self.next_send = 0

    def start(self, text, interval, now):
        text = text.strip()
        if not text or len(text.encode('utf-8')) > MAX_TEXT_BYTES or any(c in text for c in '\r\n\x00'):
            raise ValueError('Zpráva je prázdná nebo příliš dlouhá.')
        self.text = text
        self.interval = min(300, max(60, int(interval)))
        self.running = True
        self.next_send = now

    def pause(self):
        self.running = False

    def due(self, now):
        if not self.running or now < self.next_send:
            return False
        self.next_send = now + self.interval
        return True

    def remaining(self, now):
        return max(0, int(math.ceil(self.next_send - now))) if self.running else 0


FONT_SIZES = tuple(range(12, 19))
MIN_CHAT_WIDTH = 360


def chat_font(size):
    # Sub-12px chat glyphs remain unreadable in the native outlined renderer.
    return 'Tahoma:%d' % max(FONT_SIZES[0], bounded_integer(size, 8, 18, 13))


def bounded_integer(value, low, high, default):
    return value if type(value) is int and low <= value <= high else default


def chat_geometry(width, height, screen, anchor_x=None, anchor_bottom=None):
    sw, sh = screen
    if anchor_bottom is None:
        baseline = max(0, sh-37)
    else:
        # Moving keeps the full window visible, including when dragged to the
        # top edge or restored after a resolution change.
        minimum = min(sh, max(180, min(height, 2160)))
        baseline = max(minimum, min(anchor_bottom, sh))
    width = max(min(MIN_CHAT_WIDTH, sw), min(width, sw, 3840))
    x = (sw-width)//2 if anchor_x is None else max(0, min(anchor_x, sw-min(MIN_CHAT_WIDTH, sw)))
    width = min(width, sw-x)
    height = max(min(180, baseline), min(height, baseline, 2160))
    return x, baseline-height, width, height


def normalize_preferences(value, legacy=None):
    value = value if isinstance(value, dict) and value.get('version') == 1 else {}
    tabs = []
    if isinstance(value.get('tabs'), list):
        for tab in value['tabs'][:MAX_TABS]:
            if isinstance(tab, dict):
                selected = tab.get('filters', list(AVAILABLE_FILTERS))
                selected = selected if isinstance(selected, list) else []
                tabs.append(dict(name=str(tab.get('name', 'Chat')).replace('|', '')[:12],
                                 filters=sorted({i for i in selected if type(i) is int and i in AVAILABLE_FILTERS})))
    elif isinstance(legacy, dict):
        for key in sorted(legacy)[:MAX_TABS]:
            old = legacy[key]
            if isinstance(old, (tuple, list)) and len(old) >= 11:
                tabs.append(dict(name='Vše' if not tabs else str(old[0])[:12],
                                 filters=[i for i in AVAILABLE_FILTERS if old[i] == 1]))
    if not tabs:
        tabs = [dict(name='Vše', filters=list(AVAILABLE_FILTERS))]
    tabs[0]['name'] = 'Vše'
    recent = value.get('recent', [])
    recent = recent if isinstance(recent, list) else []
    unique = []
    for name in recent[:100]:
        if name in EMOJI_NAMES and name not in unique:
            unique.append(name)
    text = str(value.get('repeat_text', ''))
    if len(text.encode('utf-8')) > MAX_TEXT_BYTES:
        text = ''
    return dict(version=1, tabs=tabs, recent=unique, repeat_text=text,
                interval=value.get('interval') if type(value.get('interval')) is int and value.get('interval') in (60, 120, 180, 300) else 60,
                font=max(FONT_SIZES[0], bounded_integer(value.get('font'), 8, 18, 13)),
                width=bounded_integer(value.get('width'), MIN_CHAT_WIDTH, 3840, 627 if value.get('compact') is False else 588),
                height=bounded_integer(value.get('height'), 180, 2160, 259 if value.get('compact') is False else 230),
                x=bounded_integer(value.get('x'), 0, 32768, None),
                bottom=bounded_integer(value.get('bottom'), 0, 32768, None),
                opacity=bounded_integer(value.get('opacity'), 0, 100, 89),
                idle_opacity=bounded_integer(value.get('idle_opacity'), 0, 100, 20),
                timestamps=value.get('timestamps', True) is not False)


class PreferenceStore:
    def __init__(self, name, directory='UserData/compact_chat'):
        if not name or re.search(r'[\\/:|\x00-\x1f]', name) or name in ('.', '..'):
            raise ValueError('Invalid character name')
        self.path = os.path.join(directory, name + '.json')

    def load(self, legacy):
        value = {}
        try:
            with REAL_OPEN(self.path, 'rb') as handle:
                raw = handle.read(32769)
            if len(raw) <= 32768:
                value = json.loads(raw.decode('utf-8'))
        except (OSError, ValueError, TypeError, RecursionError):
            pass
        return normalize_preferences(value, legacy)

    def save(self, value):
        data = json.dumps(normalize_preferences(value), ensure_ascii=False).encode('utf-8')
        directory = os.path.dirname(self.path)
        os.makedirs(directory, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.chat-', dir=directory)
        try:
            with os.fdopen(descriptor, 'wb') as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
