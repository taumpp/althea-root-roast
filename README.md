# Althea Client Root — A Museum of Questionable Decisions

![lines](https://img.shields.io/badge/lines_of_python-251%2C057-red)
![bare excepts](https://img.shields.io/badge/bare_except%3A-461-orange)
![tests](https://img.shields.io/badge/tests-0-black)
![hexcolorinfo](https://img.shields.io/badge/hexcolorinfo.py-1.4_MB-blueviolet)
![vibes](https://img.shields.io/badge/AI_slop-certified-ff69b4)

> "It works on my machine." — the machine, probably, also not sure

Welcome to the guided tour of the Althea Metin2 client `root`. Get comfortable and keep your hands
inside the vehicle. Some of these files bite.

---

## The numbers

| Metric | Value | Comment |
|---|---|---|
| Python files | **331** | One file per thought, sometimes one file per half thought |
| Lines of Python | **251,057** | A quarter million lines, for a game UI |
| Lines that are one color table | **65,540** | ~26% of the codebase is a dictionary of strings. More on that below |
| `ui.py` | **10,018 lines** | Not a module, a lifestyle |
| `uitooltip.py` | **7,530 lines** | It's a tooltip. It shows text when you hover |
| Bare `except:` clauses | **461** | Every error gets caught, and almost none get explained |
| Unit tests | **0** | Players are the test suite |

---

## Exhibit A: `hexcolorinfo.py`, the 1.4 MB color picker

Most developers write a color gradient as a small math function. Althea wrote it out by hand,
all 65,536 values:

```python
# Keys are color-picker coordinates; values are RGB hex colors.
HEX_CODES = {
	'0x0': '#ffffff',
	'0x1': '#fefdfd',
	'0x2': '#fefbfb',
	'0x3': '#fef9f9',
	# ... 65,526 more lines of this ...
	'255x254': '#030000',
	'255x255': '#010000',
}
```

That is **65,540 lines** and **1,451,149 bytes**. Exactly **one** file imports it
(`uiskillcolor.py`), which looks colors up like this:

```python
hexCode = self.colorHexCodes[str("%sx%s" % (xMouse, yMouse))].lstrip('#')
```

The mouse position is formatted into a string, then wrapped in `str()` to be sure it is a string,
used to look up another string, and the `#` is stripped so the hex can be parsed back into a number.

The best part is that this is the **performance** option. It is switched on by a checkbox
literally named `perfCheckBox`. Your client loads 1.4 MB of Python so your sword can be slightly
more pink, *faster*.

---

## Exhibit B: `ON_UNCKECK`

From `ui.py`, the base widget library that every other window depends on:

```python
self.eventFunc = { "ON_CHECK" : None, "ON_UNCKECK" : None, }
self.eventArgs = { "ON_CHECK" : None, "ON_UNCKECK" : None, }
```

The typo has since spread to other files (`uibuffupgrade.py`, `uiskillcolor.py`), which means it
can no longer be fixed in one place. It's part of the API now.

---

## Exhibit C: The Talent Tree Quadruplets

| File | Lines | Size |
|---|---|---|
| `talent_tree_layout_v6_780.py` | 35 | 45 KB |
| `talent_tree_layout_v6_900.py` | 35 | 45 KB |
| `talent_tree_layout_v7_780.py` | 34 | 45 KB |
| `talent_tree_layout_v7_900.py` | 34 | 45 KB |

180 KB over 138 lines. The longest single line is **25,539 characters**. Nobody will ever review
that line, and nobody ever did.

The `_780` and `_900` versions differ by **18 lines**, mostly `WINDOW_WIDTH` and `WINDOW_HEIGHT`.
Copy-pasting 45 KB was apparently easier than adding a scale parameter.

Nothing imports **v6**. It's shipped in the client anyway and never used, like a museum piece.

Each of the four files also carries **four SHA-256 hashes**:

```python
CATALOG_HASH = '6d9ec62f...'
PROJECT_SHA256 = 'cabc89bc...'
PREVIEW_HASH = '1972b340...'
RUNTIME_MANIFEST_SHA256 = '8cf09819...'
```

That's four cryptographic hashes for **a UI layout**, or sixteen across the set. Nothing is getting
tampered with here. It's a skill tree.

---

## Exhibit D: Customer support, anime edition

From `new_intrologin.py`:

```python
"REDE_SOCIAL_1" : "https://www.youtube.com/watch?v=XFwaFFeJ9k4&ab_channel=AnimeMomentzz",
"REDE_SOCIAL_2" : "https://www.youtube.com/watch?v=XFwaFFeJ9k4&ab_channel=AnimeMomentzz",
"REDE_SOCIAL_3" : "https://discord.com",
"CREATE_ACC"    : "https://www.youtube.com/watch?v=XFwaFFeJ9k4&ab_channel=AnimeMomentzz",
"LOSE_PW"       : "https://www.youtube.com/watch?v=XFwaFFeJ9k4&ab_channel=AnimeMomentzz",
```

Want to create an account? Anime clip. Lost your password? The same anime clip. Social media?
Anime clip twice, plus the Discord homepage, not even an invite link.

The keys are in Portuguese (`REDE_SOCIAL`) on a Czech server, which suggests this file has had a
few owners.

---

## Exhibit E: `constinfo.py`, the config that keeps changing its mind

```python
CONVERT_EMPIRE_LANGUAGE_ENABLE = 1
USE_ITEM_WEAPON_TABLE_ATTACK_BONUS = 0
ADD_DEF_BONUS_ENABLE = 1
LOGIN_COUNT_LIMIT_ENABLE = 0
# ... a few lines later, in the same file ...
CONVERT_EMPIRE_LANGUAGE_ENABLE = 0
USE_ITEM_WEAPON_TABLE_ATTACK_BONUS = 0
ADD_DEF_BONUS_ENABLE = 0
LOGIN_COUNT_LIMIT_ENABLE = 0
PVPMODE_PROTECTED_LEVEL = 15   # was 30 at the top of the file
TWO_HANDED_WEAPON_ATT_SPEED_DECREASE_VALUE = 10   # was 0 at the top of the file
```

Six settings are defined twice and the second value wins. If you only read the top of the file,
you get the wrong answer.

---

## Exhibit F: Server status where everything is "ON"

From `serverinfo.py`:

```python
STATE_DICT = {
	#0 : localeInfo.CHANNEL_STATUS_OFFLINE,
	#1 : localeInfo.CHANNEL_STATUS_VACANT,
	#2 : localeInfo.CHANNEL_STATUS_RECOMMENDED,
	#3 : localeInfo.CHANNEL_STATUS_BUSY,
	#4 : localeInfo.CHANNEL_STATUS_FULL,
	0 : "OFF",
	1 : "ON",
	2 : "ON",
	3 : "ON",
	4 : "ON",
}
```

Vacant, recommended, busy and full were all mapped to "ON", and the proper locale strings were left
commented out above. A full server shows the same status as an empty one.

The same file also still contains `CHINA_PORT = 50000`. This is a Czech server.

---

## Exhibit G: `try` / `except: pass` as a way of life

**461** bare `except:` clauses. Some favorites:

```python
try:
	self.board.SetTitleName(localeInfo.MINIMAP_ZONE_NAME_DICT[mapName])
except:
	pass
```

```python
try:
	pyScrLoader.LoadScriptFile(self, "UIScript/AtlasWindow.py")
except:
	import exception
```

`intrologin.py` alone has **18** of them, so a lot can fail during login without anyone being told.

---

## Exhibit H: The class that lies about who it is

The entire file `uimetinqueuespirits.py`:

```python
"""Compatibility entry: spirits live in the shared queue editor."""
class SpiritWindow(object):
    def __new__(cls, onChange=None):
        from uimetinqueuedesigneditor import MetinQueueDesignEditor
        return MetinQueueDesignEditor()
```

Calling `SpiritWindow` gives you a `MetinQueueDesignEditor` instead, and the `onChange` callback
you passed is silently ignored. It is labeled a "compatibility entry", but no other file in the
codebase references `SpiritWindow`, so there is nothing for it to be compatible with.

---

## Exhibit I: The file explosion

Suffixes, counted:

| Suffix | Files |
|---|---|
| `*model.py` | 16 |
| `*catalog.py` | 8 |
| `*policy.py` | 6 |
| `*locale.py` | 6 |
| `*presentation.py` | 5 |
| `*layout.py` | 5 |
| `*controls.py` | 4 |
| `*style.py` | 4 |

It looks like enterprise Java, written in Python 2, for a 2004 MMO.

Highlights:

- **`uicuberenewal.py`** is one comment and one import:
  ```python
  # Shared entry point retained for interface/game callbacks at every crafting NPC.
  from uicrafting import CubeRenewalWindows
  ```
- **`globalhub.py`**: a whole module, with a `try/except`, to check whether two integers are `0`
  and `1`.
- **`game.py`** imports `snd` twice and `localeInfo` twice, just in case.
- `new_intrologin.py`, `new_introselect.py`, `new_introcreate.py` and `new_introloading.py` sit next
  to `intrologin.py`, `introselect.py`, `introcreate.py` and `introloading.py`. All eight are kept
  in the codebase.
- There is a `npclist.txt` (105 KB) and also a `npclist_dogs.txt` (98 KB).

---

## Exhibit J: The fossil layer

Under the shiny new `*model.py` / `*policy.py` / `*catalog.py` layer, the original 2004 Ymir code
is still there:

```python
STATE_COLOR_DICT = { "..." : 0xffdadada} # 퍼블리셔에서 channel상태에 ...을 유지하도 있어서 문제가 발생.
```

The Korean comments were never translated, and there are still links to `metin2.co.kr` and
`wiki.metin.co.kr` in `uishop.py` and `consolemodule.py`.

There's also a comment in `settingsmodel.py` that says:

```python
# Rain is weather, not quality: a preset never starts or stops it (as in Alturi2).
```

That comment cites **another private server** as the reference.

---

## Verdict

| Category | Score |
|---|---|
| Architecture | 🗿 Ymir would be proud, in a bad way |
| Readability | 25,539 characters on one line |
| Error handling | `except: pass` |
| DRY | ×4 |
| Testing | Done in production by the players |
| Color management | 1.4 MB |
| Overall | **AI SLOP CERTIFIED™** |

---

## Contributing

Please don't. It's already big enough.

## License

Unclear, much like the server status (which says "ON").

---

<sub>This README is satire and commentary on code quality.</sub>
