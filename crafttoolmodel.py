# -*- coding: utf-8 -*-
"""Parse server tool-upgrade records into values for the blacksmith refine window.
Player text uses locale keys; the server owns prices, materials and eligibility.

    CraftToolShopV1 <tool ids>              the shop of an upgrade NPC opened: the shop offers "Vylepšit nástroj"
    CraftToolOpenV1 <cell>                  a tool dragged onto the NPC: the window opens, the state of the cell follows
    CraftToolV1 <cell> 0                    the cell holds no tool of this NPC (or the NPC is too far away)
    CraftToolV1 <cell> <vnum> <next> <practice> <need> <chance> <band> <seal|0> <seals held> <price> <fail %> <icon>
                <tool id> <state> <n> {<material> <need> <held>} x n

Parse(command, args) returns the tool ids, the cell or a ToolState; None for a malformed line (the window keeps what
it shows). Every player text is a locale_game key CRAFT_TOOL_<key>; the nouns and sentences of a tool come by the
server's tool id (CRAFT_TOOL_NOUN_ROD, CRAFT_TOOL_TOP_PICK ...), so the client knows no vnum of a tool.
"""
import re

SHOP = 'CraftToolShopV1'
OPEN = 'CraftToolOpenV1'
STATE = 'CraftToolV1'
COMMANDS = (SHOP, OPEN, STATE)

# the states of the server (craft_tool_catalog StateName), in the order it checks them
READY, PRACTICE, SEAL, MATERIAL, YANG, TOP = 'ready', 'practice', 'seal', 'material', 'yang', 'top'
STATES = (READY, PRACTICE, SEAL, MATERIAL, YANG, TOP)
# the window's own states (never sent): no tool in the slot / the cell holds no tool of this NPC
EMPTY, NOT_TOOL = 'empty', 'none'

BAND_A = 1                  # the item's chance (bands B / C: one seal, sure)
SEAL_NEED = 1               # one seal of the band's class per upgrade (craft_tool.cpp Upgrade)
HEAD_TOKENS = 15            # the tokens of a state line before its material rows
ROW_TOKENS = 3
MAX_ROWS = 8                # more material rows than the window can show = a malformed line
MAX_VALUE = 10 ** 15        # counts, practice and Yang (64 bit gold)
TOOL_ID = re.compile(r'^[a-z][a-z0-9_]{0,23}$')
PREFIX = 'CRAFT_TOOL_'
MATERIAL_GROUPS_PATH = 'locale/common/craft_tool_material_groups.txt'
_materialGroups = None


def LoadMaterialGroups(lines):
    """Presentation groups: tool id, locale key, interchangeable item ids."""
    groups = {}
    for line in lines:
        fields = line.split()
        if not fields or fields[0].startswith('#'):
            continue
        if len(fields) < 4 or _ToolId(fields[0]) is None:
            continue
        members = tuple(_Number(value) for value in fields[2:])
        if any(value is None or value == 0 for value in members):
            continue
        for vnum in members:
            groups[(fields[0], vnum)] = (fields[1], members)
    return groups


def MaterialGroup(toolId, vnum):
    """A localized group for a representative item; no change to server counts."""
    global _materialGroups
    if _materialGroups is None:
        try:
            with open(MATERIAL_GROUPS_PATH, 'r') as source:
                _materialGroups = LoadMaterialGroups(source)
        except (IOError, OSError):
            _materialGroups = {}
    group = _materialGroups.get((toolId, vnum))
    if group:
        import localeInfo
        title = getattr(localeInfo, group[0], None)
        if isinstance(title, str) and title:
            return title, group[1]
    return None


def _Number(token, limit=MAX_VALUE):
    """A whole number 0 .. limit from a server token, else None."""
    text = str(token).strip()
    if not text.isdigit():
        return None
    value = int(text)
    return value if value <= limit else None


def _ToolId(token):
    text = str(token).strip()
    return text if TOOL_ID.match(text) else None


class ToolState(object):
    """One CraftToolV1 answer."""

    def __init__(self, cell, vnum=0, next=0, practice=0, need=0, chance=0, band=BAND_A, seal=0, sealsHeld=0, price=0,
                 failPct=0, icon=0, toolId='', state=NOT_TOOL, materials=()):
        self.cell = cell
        self.vnum = vnum
        self.next = next
        self.practice = practice
        self.need = need
        self.chance = chance
        self.band = band
        self.seal = seal
        self.sealsHeld = sealsHeld
        self.price = price
        self.failPct = failPct
        self.icon = icon
        self.toolId = toolId
        self.state = state
        self.materials = tuple(materials)       # (vnum, need, held)

    def IsTool(self):
        return self.vnum > 0

    def IsTop(self):
        return self.state == TOP

    def CanUpgrade(self):
        return self.IsTool() and self.state == READY

    def Missing(self):
        """The practice still missing for the next grade."""
        return max(0, self.need - self.practice)

    def ShowsLoss(self):
        """Band A with a chance below 100 %: a failure costs practice (the chance line shows it)."""
        return self.IsTool() and not self.IsTop() and self.band == BAND_A and self.chance < 100 and self.failPct > 0


def ParseShop(args):
    ids = tuple(_ToolId(token) for token in args)
    if not ids or None in ids:
        return None
    return ids


def ParseOpen(args):
    if len(args) != 1:
        return None
    return _Number(args[0])


def ParseState(args):
    args = tuple(args)
    if len(args) < 2:
        return None
    cell = _Number(args[0])
    if cell is None:
        return None
    if len(args) == 2:
        return ToolState(cell) if args[1] == '0' else None
    if len(args) < HEAD_TOKENS:
        return None
    numbers = [_Number(token) for token in args[1:12]]
    if None in numbers:
        return None
    vnum, next, practice, need, chance, band, seal, sealsHeld, price, failPct, icon = numbers
    toolId = _ToolId(args[12])
    state = args[13]
    rows = _Number(args[14], MAX_ROWS)
    if not vnum or toolId is None or state not in STATES or rows is None or chance > 100 or failPct > 100 \
            or band < BAND_A or len(args) != HEAD_TOKENS + rows * ROW_TOKENS:
        return None
    if (state == TOP) != (next == 0):
        return None
    materials = []
    for index in range(rows):
        row = [_Number(token) for token in args[HEAD_TOKENS + index * ROW_TOKENS:HEAD_TOKENS + (index + 1) * ROW_TOKENS]]
        if None in row or not row[0]:
            return None
        materials.append(tuple(row))
    return ToolState(cell, vnum, next, practice, need, chance, band, seal, sealsHeld, price, failPct, icon, toolId,
                     state, materials)


PARSERS = {SHOP: ParseShop, OPEN: ParseOpen, STATE: ParseState}


def Parse(command, args):
    parser = PARSERS.get(command)
    return parser(args) if parser else None


# --------------------------------------------------------------------------- player texts (locale_game CRAFT_TOOL_*)
def Text(key, *args):
    """The locale_game text CRAFT_TOOL_<key> formatted with ``args``; the key itself when the locale lacks it."""
    try:
        import localeInfo
        value = getattr(localeInfo, PREFIX + key, None)
    except Exception:
        value = None
    if not isinstance(value, str) or not value:
        return PREFIX + key
    if not args:
        return value
    try:
        return value % args
    except (TypeError, ValueError):
        return value


def _HasText(key):
    try:
        import localeInfo
        value = getattr(localeInfo, PREFIX + key, None)
    except Exception:
        return False
    return isinstance(value, str) and bool(value)


def _ByTool(kind, toolId, *args):
    """CRAFT_TOOL_<kind>_<TOOL> (a sentence or noun of one tool), CRAFT_TOOL_<kind>_ANY for a tool the locale lacks."""
    key = '%s_%s' % (kind, (toolId or '').upper())
    return Text(key if toolId and _HasText(key) else kind + '_ANY', *args)


def Noun(toolIds):
    """'prut': the tool of the NPC as the empty hint names it; 'nástroj' for an NPC of several tools (Deokbae: pickaxe
    and axe), whose two nouns would not fit the line (CRAFT_TOOL_NOUN_ANY)."""
    toolIds = tuple(toolIds or ())
    return _ByTool('NOUN', toolIds[0]) if len(toolIds) == 1 else Text('NOUN_ANY')


def GradeOf(name):
    """The "+N" an item name ends with (the grade of a refine chain), None without one."""
    match = re.search(r'\+(\d+)\s*$', name or '')
    return int(match.group(1)) if match else None


def Hint(state, toolIds=(), grade=None):
    """The line the window shows instead of the chance; '' when the chance line shows (the tool can or could be
    upgraded once the rows are green)."""
    if state is None:
        return Text('HINT_EMPTY', Noun(toolIds))
    if not state.IsTool():
        return Text('HINT_NOT_TOOL')
    if state.IsTop():
        return _ByTool('TOP', state.toolId, grade if grade is not None else 0)
    if state.state == YANG:
        return Text('NO_YANG')
    if state.state == PRACTICE:
        return _ByTool('PRACTICE', state.toolId, state.Missing())
    return ''


def LossText(state):
    """'[–10 % cviku]': what a failure in band A costs."""
    return Text('FAIL_LOSS', state.failPct)
