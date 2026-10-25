"""Settings A: editable drafts; no native mutation until Apply.

Camera, colors and quality are independent. Persist only presentation preferences;
server PvP/block state and item alarms remain authoritative at their providers.
"""
import copy
import math


COLOR_DEFAULTS = dict(image_enabled=1., exposure=0., contrast=1.13, saturation=1.08,
                      temperature=.04, shadows=.035, highlights=-.06, sharpness=.3,
                      glow=0., ambient=1., self_light=1., sun_temperature=0.)
NAME_VISIBILITY_KEYS = ('name_own', 'name_players', 'name_monsters', 'name_stones',
                        'name_bosses', 'name_npcs', 'name_buff_support', 'name_companions')
COLOR_BOUNDS = dict(image_enabled=(0, 1), exposure=(-1, 1), contrast=(.5, 1.5),
                    saturation=(0, 1.7), temperature=(-.5, .5), shadows=(-.3, .3),
                    highlights=(-.4, .1), sharpness=(0, 1), glow=(0, .25),
                    ambient=(.5, 1.5), self_light=(.3, 1.2), sun_temperature=(-.3, .3))
# Rain is weather, not quality: a preset never starts or stops it (as in Alturi2).
# Ultra uses FXAA - MSAA hides the scene depth the reference god rays and fog need.
# tree_shadow: SpeedTree shadow casters beyond this many metres from the camera
# target are skipped (0 = unlimited). Original 80, Low 60, High 100, Ultra 150.
QUALITY_KEYS = ('world_level', 'aa', 'shadow_target', 'shadow_quality',
                'rain_fx', 'grass', 'grass_radius', 'lights', 'reflections', 'postprocess', 'tree_shadow')
QUALITY_PRESETS = tuple(dict(zip(QUALITY_KEYS, values)) for values in (
    (0, 0, 3, 1, 0, 0, 100, 0, 0, 1, 80),
    (1, 1, 1, 0, 0, 1, 100, 0, 0, 1, 60),
    (2, 2, 3, 1, 1, 1, 100, 1, 0, 1, 100),
    (3, 1, 3, 2, 1, 1, 200, 1, 1, 1, 150),
))
# Quality keys added after settings-a.json v1 shipped: a saved snapshot without
# them still identifies its preset instead of silently becoming Custom.
LATE_QUALITY_KEYS = ('tree_shadow',)
TREE_SHADOW_CHOICES = (60, 80, 100, 150, 0)
# FPS of an inactive or minimized client window (a second client behind the active one). 30 keeps weak machines
# with several clients responsive; the executable accepts 10-360 (background_fps_limit in metin2.cfg).
BACKGROUND_FPS_CHOICES = (10, 30, 60)
UI_SCALE_CHOICES = tuple(range(50, 151, 5))
BOUNDS = dict(ui_scale=(50, 150), world_level=(0, 3), aa=(0, 3), shadow_target=(0, 3), shadow_quality=(0, 2),
              rain=(0, 3), rain_fx=(0, 1), grass=(0, 1), grass_radius=(100, 300), tree_shadow=(0, 150),
              lights=(0, 1), reflections=(0, 1), postprocess=(0, 1), fps=(30, 360), background_fps=(10, 360), refresh_hz=(0, 1000),
              vsync=(0, 1), show_fps=(0, 1), fov=(10, 100), camera=(0, 1), fog=(0, 1),
              sky=(0, 11), font=(0, 1), chat=(0, 1), quests=(0, 1), affects=(0, 1),
              names=(0, 1), family_names=(0, 1), npc_names=(0, 1), outline=(0, 1), mob_level=(0, 1),
              mob_aggressive=(0, 1), damage=(0, 1), damage_size=(0, 1), damage_height=(0, 2), stone_size=(0, 1),
              skills=(0, 1), buffs=(0, 1), special_effects=(0, 2), pet=(0, 1),
              mount=(0, 1), support=(0, 1), shop=(0, 1), loot_messages=(0, 2),
              yang=(0, 1), loot_placement=(0, 1), loot_lifetime=(0, 15), costumes=(0, 1), sound=(0, 1),
              music=(0, 1), pickup_mode=(1, 2), pickup_min=(1, 150), pickup_max=(1, 150),
              block=(0, 127), pvp=(0, 4))
for _key in ('biolog_hud', 'biolog_messages', 'dungeon_hud', 'dungeon_messages', 'switchbot_messages'):
    BOUNDS[_key] = (0, 1)
BOUNDS['dps_meter'] = (0, 1)        # Ukazatel poškození (DPS) in the target form: 0 = off completely
for _group, _count in (('class', 4), ('weapon', 7), ('armor', 7)):
    for _index in range(_count):
        BOUNDS['pickup_%s_%d' % (_group, _index)] = (0, 1)
BOUNDS.update(damage_font=(0, 11), damage_normal_color=(0, 0xFFFFFF),
              damage_critical_color=(0, 0xFFFFFF), damage_outline=(0, 1), damage_grouping=(0, 2))
BOUNDS.update((key, (0, 2)) for key in NAME_VISIBILITY_KEYS)
FLOAT_KEYS = set(('damage_height', 'damage_size', 'stone_size', 'sound', 'music', 'fov'))
DEFAULTS = dict((key, bounds[0]) for key, bounds in BOUNDS.items())
DEFAULTS.update(QUALITY_PRESETS[2])
DEFAULTS.update((key, 2) for key in NAME_VISIBILITY_KEYS)
DEFAULTS.update(ui_scale=100, rain=0, fps=60, background_fps=30, vsync=1, fov=30, camera=1, fog=1, chat=1, quests=1, affects=1,
                npc_names=1, outline=1, mob_level=1, mob_aggressive=1, damage=1,
                skills=1, buffs=1, pet=1, mount=1, support=1, shop=1, yang=1,
                sound=1, music=.5, loot_lifetime=7, pickup_mode=1, pickup_min=1, pickup_max=150,
                biolog_hud=1, biolog_messages=1, dungeon_hud=1, dungeon_messages=1,
                switchbot_messages=1, dps_meter=1, track='', menu_music='shuffle')
# Hudba v menu: the music of the login-free menus (select, creation) - root/pregamemusic.py
MENU_MUSIC_TRACKS = (('crimson_citadel', 'Crimson Citadel'), ('blood_and_steel', 'Blood and Steel'),
                     ('by_blood_and_steel', 'By Blood and Steel'), ('rise_althea', 'Rise, Althea'))
MENU_MUSIC_CHOICES = ('shuffle',) + tuple(key for key, unused in MENU_MUSIC_TRACKS)

DEFAULTS.update(damage_font=0, damage_normal_color=0xFFFF00, damage_critical_color=0x66BFFF,
                damage_outline=1, damage_grouping=0, damage_height=0.)


def normalized(values, defaults=DEFAULTS, bounds=BOUNDS):
    result = dict(defaults)
    if not isinstance(values, dict):
        return result
    for key, (low, high) in bounds.items():
        try:
            value = float(values[key])
            if (key == 'ui_scale' and bounds is BOUNDS and value not in UI_SCALE_CHOICES) or (
                    key == 'tree_shadow' and bounds is BOUNDS and value not in TREE_SHADOW_CHOICES):
                continue
            if not math.isfinite(value):
                continue
            value = max(low, min(high, value))
            result[key] = value if key in FLOAT_KEYS or bounds is COLOR_BOUNDS else int(round(value))
        except (KeyError, ValueError, TypeError, OverflowError):
            pass
    if bounds is BOUNDS:
        if result['loot_lifetime'] not in (3, 5, 7, 10, 15, 0):
            result['loot_lifetime'] = defaults['loot_lifetime']
        track = values.get('track')
        if isinstance(track, str) and len(track) <= 240 and not any(c in track for c in ('/', '\\', '\x00')):
            result['track'] = track
        if values.get('menu_music') in MENU_MUSIC_CHOICES:
            result['menu_music'] = values['menu_music']
        result['pickup_min'] = min(result['pickup_min'], result['pickup_max'])
    return result


def colors_for(preset, sharpness=.3):
    if preset not in range(4):
        raise ValueError('Invalid color preset')
    values = dict(COLOR_DEFAULTS)
    values.update(image_enabled=0., contrast=1., saturation=1., temperature=0.,
                  shadows=0., highlights=0., glow=0., sharpness=sharpness)
    if preset:
        values.update(image_enabled=1., contrast=(1.13, 1.25, 1.19)[preset - 1],
                      saturation=(1.08, 1.22, 1.06)[preset - 1],
                      temperature=(.04, .025, .10)[preset - 1],
                      shadows=.035 if preset == 1 else .045,
                      highlights=-.15 if preset == 3 else -.06,
                      glow=.065 if preset == 3 else 0.)
    return values


# The embedded client omits unicodedata. Fold Czech search terms using only
# built-in string operations, including decomposed accents from pasted text.
_SEARCH_FOLD = str.maketrans('áčďéěíňóřšťúůýž', 'acdeeinorstuuyz')


def search_text(text):
    return ''.join(c for c in text.casefold().translate(_SEARCH_FOLD)
                   if not '\u0300' <= c <= '\u036f')


class Session:
    def __init__(self, backend):
        self.backend = backend
        self.begin()

    def begin(self):
        self.values = normalized(self.backend.read())
        visual = self.backend.read_colors()
        self.colors = normalized(visual, COLOR_DEFAULTS, COLOR_BOUNDS)
        self.color_preset = int(visual.get('preset', 1))
        if self.color_preset not in range(5):
            self.color_preset = 4
        self.custom_colors = (normalized(visual['custom'], self.colors, COLOR_BOUNDS)
                              if isinstance(visual.get('custom'), dict) else None)
        saved = self.backend.read_preferences()
        self.quality_preset = self.values['world_level']
        self.custom_quality = None
        if isinstance(saved, dict):
            custom = saved.get('custom_quality')
            if isinstance(custom, dict) and all(key in custom for key in QUALITY_KEYS
                                                if key not in LATE_QUALITY_KEYS):
                self.custom_quality = {key: normalized(custom)[key] for key in QUALITY_KEYS}
            if saved.get('quality_preset') in range(5):
                # Native settings changed elsewhere must be represented as Custom.
                snapshot = saved.get('quality_values')
                if isinstance(snapshot, dict) and all(
                        snapshot.get(k, self.values[k] if k in LATE_QUALITY_KEYS else None) == self.values[k]
                        for k in QUALITY_KEYS):
                    self.quality_preset = saved['quality_preset']
                else:
                    self.quality_preset = 4
        if self.quality_preset != 4 and any(self.values[k] != QUALITY_PRESETS[self.quality_preset][k] for k in QUALITY_KEYS):
            self.quality_preset = 4
        if self.quality_preset == 4:
            self.custom_quality = {key: self.values[key] for key in QUALITY_KEYS}
        self.before = self.snapshot()

    def snapshot(self):
        return copy.deepcopy(dict(values=self.values, colors=self.colors,
                                  color_preset=self.color_preset, quality_preset=self.quality_preset,
                                  custom_colors=self.custom_colors, custom_quality=self.custom_quality))

    def discard(self):
        for key, value in copy.deepcopy(self.before).items():
            setattr(self, key, value)

    def set(self, key, value):
        if key in COLOR_BOUNDS:
            new = normalized({key: value}, self.colors, COLOR_BOUNDS)
            if new == self.colors:
                return
            self.colors = new
            if key not in ('sharpness', 'exposure', 'image_enabled'):
                self.colors['image_enabled'] = 1.
            self.color_preset = 4
            self.custom_colors = dict(self.colors)
        elif key in BOUNDS or key in ('track', 'menu_music'):
            new = normalized({key: value}, self.values)
            if new == self.values:
                return
            self.values = new
            if key in QUALITY_KEYS:
                self.quality_preset = 4
                self.custom_quality = {k: self.values[k] for k in QUALITY_KEYS}
        else:
            raise KeyError(key)

    def select_colors(self, preset):
        if preset not in range(5):
            raise ValueError('Invalid color preset')
        if preset == 4:
            if self.custom_colors is None:
                self.custom_colors = dict(self.colors)
            self.colors = dict(self.custom_colors)
        else:
            self.colors = colors_for(preset, self.colors['sharpness'])
        self.color_preset = preset

    def select_quality(self, preset):
        if preset not in range(5):
            raise ValueError('Invalid quality preset')
        if preset == 4:
            if self.custom_quality is None:
                self.custom_quality = {key: self.values[key] for key in QUALITY_KEYS}
            self.values.update(self.custom_quality)
        else:
            self.values.update(QUALITY_PRESETS[preset])
        self.quality_preset = preset

    def apply(self):
        if self.snapshot() == self.before:
            return True
        self.backend.apply(self.snapshot(), self.before)
        self.before = self.snapshot()
        return True
