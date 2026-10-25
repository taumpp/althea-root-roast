"""Craft contracts in the Denní úkoly window (owner 13. 10., REM-SVITEK2 = B, ZAKAZKY-PERIODA = C).

The server sends one line per craft on "/craft_mastery contracts", after every
gathering result, after a hand-in and after a GM day shift:

    CraftContractV1 <craft 0 fishing|1 mining|2 woodcut> <enabled> <goal> <progress> <waiting> <stack_max>
                    <hand_in> <exp>

The model keeps the last line of every craft; Records() turns them into rows of uidailytasks.DailyTaskRow and
Waiting() is the number on the Denní úkoly icon. Texts are locale_game CRAFT_CONTRACT_*; the client keeps no goal,
count or reward of its own.
"""

REQUEST = '/craft_mastery contracts'
HAND_IN = '/craft_mastery hand_in %s'     # one click in the window (ZAKAZKY-NAVRHY = B), the server checks the NPC
REPLY = 'CraftContractReply'               # the server's answer to that click: <craft> <code> <value>
NPC = 'CraftContractNpcV1'                 # <craft> <distance> <vid>...: the hand-in NPCs on the player's map
KINDS = 'CraftContractKindsV1'             # <craft> <vnum>...: the kinds a contract takes (the hand-in window)
KEYS = ('fishing', 'mining', 'woodcut')
CRAFTS = (0, 1, 2)
FIELDS = 7      # after the craft index


class Contract(object):
    __slots__ = ('craft', 'enabled', 'goal', 'progress', 'waiting', 'stack', 'handIn', 'exp')

    def __init__(self, craft, values):
        self.craft = craft
        self.enabled = values[0] == 1
        self.goal, self.progress, self.waiting, self.stack, self.handIn, self.exp = [max(0, v) for v in values[1:]]
        self.progress = min(self.progress, self.goal)


def Text(key, default=u''):
    """locale_game text (localeInfo.<key>), the default when the client has no such key."""
    try:
        import localeInfo
        value = getattr(localeInfo, key)
    except Exception:
        return default
    if isinstance(value, bytes):
        try:
            value = value.decode('cp1250')
        except Exception:
            return default
    return value


class CraftContractModel(object):
    def __init__(self):
        self.contracts = {}
        self.npcs = {}          # craft -> (distance, vids): the Odevzdat button is active only in their range
        self.handedIn = set()   # crafts handed in by the Odevzdat button while no next contract waits ("Odevzdáno")
        self.kinds = {}         # craft -> (vnum, ...): what the hand-in window accepts (server data, contract.vnums)
        self.revision = 0

    def Feed(self, command, args):
        """True when a line changed the model."""
        if command == NPC:
            return self._FeedNpcs(args)
        if command == KINDS:
            return self._FeedKinds(args)
        if command != 'CraftContractV1' or len(args) != 1 + FIELDS:
            return False
        try:
            values = [int(arg) for arg in args]
        except ValueError:
            return False
        if values[0] not in CRAFTS:
            return False
        contract = Contract(values[0], values[1:])
        if contract.waiting > 0 and contract.progress < contract.goal:
            self.handedIn.discard(contract.craft)      # a new contract is open: the "Odevzdáno" state is over
        old = self.contracts.get(contract.craft)
        if old is not None and all(getattr(old, name) == getattr(contract, name) for name in Contract.__slots__):
            return False
        self.contracts[contract.craft] = contract
        self.revision += 1
        return True

    def _FeedNpcs(self, args):
        try:
            values = [int(arg) for arg in args]
        except (TypeError, ValueError):
            return False
        if len(values) < 2 or values[0] not in CRAFTS:
            return False
        npcs = (values[1], tuple(values[2:]))
        if self.npcs.get(values[0]) == npcs:
            return False
        self.npcs[values[0]] = npcs
        return True

    def _FeedKinds(self, args):
        try:
            values = [int(arg) for arg in args]
        except (TypeError, ValueError):
            return False
        if not values or values[0] not in CRAFTS:
            return False
        kinds = tuple(values[1:])
        if self.kinds.get(values[0]) == kinds:
            return False
        self.kinds[values[0]] = kinds
        return True

    def HandInKinds(self, taskId):
        """The kinds the hand-in window of a contract row accepts (empty before the server's line)."""
        craft = _CraftOf(taskId)
        return self.kinds.get(craft, ()) if craft is not None else ()

    def HandInPieces(self, taskId):
        """How many pieces the contract takes (CraftContractV1 hand_in)."""
        craft = _CraftOf(taskId)
        c = self.contracts.get(craft) if craft is not None else None
        return c.handIn if c and c.enabled and c.waiting > 0 and c.progress >= c.goal else 0

    def HandInNear(self, taskId, distanceOf):
        """True when the player stands in range of a hand-in NPC of the row's contract (owner 14. 10.: the Odevzdat
        button is grey elsewhere). distanceOf(vid) is player.GetCharacterDistance (-1 for a vid the client does not
        see). No NPC line from the server (an older one) or distance 0 (no NPC list): True, the server decides."""
        craft = _CraftOf(taskId)
        if craft is None or craft not in self.npcs:
            return True
        distance, vids = self.npcs[craft]
        if distance <= 0:
            return True
        for vid in vids:
            try:
                d = float(distanceOf(vid))
            except Exception:
                continue
            if 0 <= d <= distance:
                return True
        return False

    def Reply(self, args):
        """The server's answer to the Odevzdat button: code 0 (handed in) keeps the row "Odevzdáno" until a new
        contract opens. True when that changed the rows."""
        try:
            craft, code = int(args[0]), int(args[1])
        except (TypeError, ValueError, IndexError):
            return False
        if code != 0 or craft not in CRAFTS or craft in self.handedIn:
            return False
        self.handedIn.add(craft)
        return True

    def Waiting(self):
        """Contracts waiting at the NPCs, done ones (ready to hand in) included, all crafts together (the number on
        the Denní úkoly icon). Only crafts whose contracts can pile up (the server's stack_max above 1) count: with
        one contract a day that lapses at the day's end the icon has no number (owner 15. 10.)."""
        return sum(c.waiting for c in self.contracts.values() if c.enabled and c.stack > 1)

    def Records(self):
        """Rows for uidailytasks.DailyTaskRow: name, objective, current / required, the reward text, no items."""
        rows = []
        for craft in CRAFTS:
            c = self.contracts.get(craft)
            if c is None or not c.enabled or c.goal <= 0:
                continue
            ready = c.waiting > 0 and c.progress >= c.goal
            # handed in: by the button in this session, or (one contract a day, stack_max 1) the server has none
            # waiting = today's was handed in; the server keeps that in its flags, so "Odevzdáno" survives a relog
            # (DEV 15. 10.: after a relog the row went back to a count that kept growing)
            handed = (craft in self.handedIn or (c.stack <= 1 and c.waiting <= 0)) and not ready
            # the server's data say "hand it in anywhere" (CraftContractNpcV1 distance 0): no NPC in the texts
            anywhere = craft in self.npcs and self.npcs[craft][0] <= 0
            if ready:                       # done, waiting at the NPC: the completed look of a daily task
                objective = Text('CRAFT_CONTRACT_READY_ANYWHERE' if anywhere else 'CRAFT_CONTRACT_READY_%d' % craft, u'')
            elif c.waiting > 0:
                objective = Text('CRAFT_CONTRACT_GATHER_%d' % craft if anywhere else 'CRAFT_CONTRACT_OBJECTIVE_%d' % craft, u'')
            elif handed:                    # handed in by the button, the next contract comes tomorrow
                objective = Text('CRAFT_CONTRACT_NONE', u'')
            elif c.progress >= c.goal and c.stack > 1:     # nothing waits, the pieces count for the next contract
                objective = Text('CRAFT_CONTRACT_AHEAD', u'')   # (stack_max 1: nothing is gathered ahead)
            else:
                objective = Text('CRAFT_CONTRACT_NONE', u'')
            # owner 15. 10.: the stock still works, but the window does not say that contracts can pile up; the
            # text is locale_game CRAFT_CONTRACT_STOCK, empty = not shown (put "Zásoba %d/%d" back to show it)
            # stack_max 1 (one contract a day, it lapses): no stock to speak of, whatever the text
            stock = _Fill(Text('CRAFT_CONTRACT_STOCK', u''), max(0, c.waiting - 1), c.stack) if c.stack > 1 else u''
            rows.append({
                'id': 'craft_contract_%d' % craft,
                'name': Text('CRAFT_CONTRACT_NAME_%d' % craft, u'%d') % c.goal,
                'objective': objective,
                'current': c.goal if handed else c.progress,          # handed in: the full bar, not what counts on
                'required': c.goal,
                'percent': 100 if handed else int(c.progress * 100 / c.goal),
                'status': 1 if (ready or handed) else 0,
                'rewards': (),
                'reward_text': Text('CRAFT_CONTRACT_REWARD', u'+%d') % c.exp,
                'hand_in': 'craft_contract_%d' % craft if ready else '',   # the row's Odevzdat button
                'hand_in_hint': Text('CRAFT_CONTRACT_STAND_BY_%d' % craft, u''),   # its hint while it is grey
                # owner 14. 10.: the state stands in ONE place right of the row – the Odevzdat button alone while it is
                # done (no "Splněno" above it), "Odevzdáno" once handed in, else the count
                # a done row keeps its count (owner 14. 10.: "where is 5/5?"), the button under it; "Odevzdáno" alone
                'progress_text': (u'%d / %d' % (c.progress, c.goal)) if ready else (Text('CRAFT_CONTRACT_HANDED', u'') if handed else None),
                # the stock right of the row (owner 14. 10.: "čeká 1 z 3" read as the current one): the contracts
                # waiting AFTER the current one, out of the most that can wait after it
                'side_text': stock,
                'side_hint': _Fill(Text('CRAFT_CONTRACT_STOCK_HINT', u''), c.stack) if stock else u'',
            })
        return rows


def _CraftOf(taskId):
    """The craft of a contract row id ('craft_contract_<craft>'), None for other rows."""
    if not isinstance(taskId, str) or not taskId.startswith('craft_contract_'):
        return None
    try:
        craft = int(taskId[len('craft_contract_'):])
    except ValueError:
        return None
    return craft if craft in CRAFTS else None


def _Fill(text, *values):
    """text % values when the text has the numbers, else the text (a locale without them)."""
    if text.count('%d') != len(values):
        return text
    try:
        return text % values
    except (TypeError, ValueError):
        return text


def HandInCellsCommand(taskId, cells):
    """The server command of the hand-in window: the inventory cells the player put in, in order (at most 16)."""
    craft = _CraftOf(taskId)
    if craft is None or not cells:
        return None
    cells = [int(cell) for cell in cells][:16]
    return (HAND_IN % KEYS[craft]) + ''.join(' %d' % cell for cell in cells)


def HandInCommand(taskId):
    """The server command of a contract row's Odevzdat button ('craft_contract_<craft>'), None for other rows."""
    craft = _CraftOf(taskId)
    return HAND_IN % KEYS[craft] if craft is not None else None


def ReplyText(args):
    """Text of the server's answer to the Odevzdat button ("CraftContractReply <craft> <code> <value>"):
    0 handed in (+value EXP), 1 no done contract, 2 stand by the craft's NPC, 3 need value pieces, 4 cannot now.
    locale_game CRAFT_CONTRACT_REPLY_<code> (code 2: CRAFT_CONTRACT_REPLY_2_<craft>); None for a broken line."""
    try:
        craft, code, value = [int(arg) for arg in args]
    except (TypeError, ValueError):
        return None
    if craft not in CRAFTS or code not in (0, 1, 2, 3, 4):
        return None
    key = 'CRAFT_CONTRACT_REPLY_2_%d' % craft if code == 2 else 'CRAFT_CONTRACT_REPLY_%d' % code
    text = Text(key, u'')
    if not text:
        return None
    if '%d' in text:
        try:
            text = text % value
        except (TypeError, ValueError):
            return None
    return text
