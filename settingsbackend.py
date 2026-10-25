"""Native/provider bindings for Settings A. Reads never send packets or save files."""
import builtins
import json
import math
import os
import tempfile

import app
import background
import cfg
import constInfo
import fontconfig
import musicInfo
import net
import osfInfo
import player
import snd
import systemSetting
import settingsmodel as model

REAL_OPEN = getattr(builtins, 'old_open', builtins.open)
PREFERENCES = 'UserData/settings-a.json'
# metin2.cfg [OPTION] names of the frame options (read by the executable at start).
CFG_KEYS = dict(fps='fps_limit', background_fps='background_fps_limit')
BINDINGS = {
    'world_level': ('GetWorldGraphicsLevel', 'SetWorldGraphicsLevel'),
    'aa': ('GetWorldAntialiasMode', 'SetWorldAntialiasMode'),
    'shadow_target': ('GetShadowTargetLevel', 'SetShadowTargetLevel'),
    'shadow_quality': ('GetShadowQualityLevel', 'SetShadowQualityLevel'),
    'rain': ('GetWorldRainLevel', 'SetWorldRainLevel'),
    'rain_fx': ('GetWorldRainFx', 'SetWorldRainFx'),
    'grass': ('GetWorldGrass', 'SetWorldGrass'),
    'grass_radius': ('GetWorldGrassRadius', 'SetWorldGrassRadius'),
    'lights': ('GetWorldLights', 'SetWorldLights'),
    'reflections': ('GetWorldReflections', 'SetWorldReflections'),
    'postprocess': ('GetWorldPostProcessing', 'SetWorldPostProcessing'),
    'fov': ('GetFOV', 'SetFOV'), 'camera': ('GetCameraModeOption', 'SetCameraModeOption'),
    'fog': ('GetFogMode', 'SetFogMode'), 'sky': ('GetSkyboxPreset', 'SetSkyboxPreset'),
    'font': ('GetFontLevel', 'SetFontLevel'), 'chat': ('IsViewChat', 'SetViewChatFlag'),
    'quests': ('GetQuestModeOption', 'SetQuestModeOption'),
    'affects': ('IsAffectIconShow', 'SetEffectIconShow'),
    'names': ('IsAlwaysShowName', 'SetAlwaysShowNameFlag'),
    'family_names': ('IsOwnFamilyNameVisible', 'SetOwnFamilyNameVisible'),
    'npc_names': ('IsNpcNameStatus', 'SetNpcNameStatusFlag'),
    'outline': ('GetNamesType', 'SetNamesType'),
    'mob_level': ('IsShowMobLevel', 'SetShowMobLevel'),
    'mob_aggressive': ('IsShowMobAIFlag', 'SetShowMobAIFlag'),
    'damage': ('IsShowDamage', 'SetShowDamageFlag'),
    'damage_size': ('GetDamageTextureScale', 'SetDamageTextureScale'),
    'damage_height': ('GetDamageHeight', 'SetDamageHeight'),
    'damage_font': ('GetDamageFont', 'SetDamageFont'),
    'damage_normal_color': ('GetDamageNormalColor', 'SetDamageNormalColor'),
    'damage_critical_color': ('GetDamageCriticalColor', 'SetDamageCriticalColor'),
    'damage_outline': ('GetDamageOutline', 'SetDamageOutline'),
    'damage_grouping': ('GetDamageGrouping', 'SetDamageGrouping'),

    'stone_size': ('GetMetinstoneScale', 'SetMetinstoneScale'),
    'special_effects': ('GetEffectLevel', 'SetEffectLevel'),
    'pet': ('IsShowPet', 'SetShowPet'), 'mount': ('IsShowMount', 'SetShowMount'),
    'support': ('IsShowSupport', 'SetShowSupport'), 'shop': ('IsShowShop', 'SetShowShop'),
    'loot_messages': ('GetDropInfomation', 'SetDropInfomation'),
    'yang': ('IsShowYang', 'SetShowYang'),
    'sound': ('GetSoundVolume', 'SetSoundVolumef'), 'music': ('GetMusicVolume', 'SetMusicVolume'),
}
NOTIFICATION_KEYS = ('biolog_hud', 'biolog_messages', 'dungeon_hud', 'dungeon_messages', 'switchbot_messages')
# Effect switches -> native index of GetBLEffectOption / SetBLEffectOption. The native value is True when the
# effects are SHOWN (the legacy "Hide effects" toggle was pressed on False); metin2.cfg keeps it under the
# misleading names HIDE_SKILL_EFFECT / HIDE_BUFF_EFFECT, 1 = shown.
EFFECT_SWITCHES = (('skills', 1), ('buffs', 0))
SKY_REGISTERED = set()
DAMAGE_KEYS = tuple(key for key in BINDINGS if key.startswith('damage_') and key not in ('damage_size', 'damage_height'))


def damage_supported():
    return all(callable(getattr(systemSetting, method, None))
               for key in DAMAGE_KEYS for method in BINDINGS[key])


def name_visibility_supported():
    return all(callable(getattr(systemSetting, method, None))
               for method in ('GetNameVisibility', 'SetNameVisibility'))


class SettingsValidationError(ValueError):
    pass


def atomic_write(path, data):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.settings-', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(descriptor, 'wb') as target:
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _read_json(path):
    try:
        with REAL_OPEN(path, 'rb') as source:
            raw = source.read(32769)
        if len(raw) <= 32768:
            value = json.loads(raw.decode('utf-8'))
            if isinstance(value, dict) and value.get('version') == 1:
                return value
    except (OSError, ValueError, TypeError, RecursionError):
        pass
    return {}


def pickup_path():
    name = str(player.GetName())
    if not name or any(c in name for c in ('/', '\\', ':', '\x00')) or name in ('.', '..'):
        raise ValueError('Invalid character name for pickup preferences')
    return 'UserData/pickup/' + name + '.cfg'


def read_pickup():
    result = {}
    try:
        with REAL_OPEN(pickup_path(), 'r') as source:
            lines = source.read(8192).splitlines()
        for line in lines:
            key, separator, value = line.partition(':')
            if not separator:
                continue
            try:
                if key in ('pick_mode', 'min_lvl', 'max_lvl'):
                    result[dict(pick_mode='pickup_mode', min_lvl='pickup_min', max_lvl='pickup_max')[key]] = int(value)
                elif key in ('block_class', 'block_weapon', 'block_armor'):
                    group = key[6:]
                    selected = {int(v) for v in value.split(',') if v}
                    for index in range(4 if group == 'class' else 7):
                        result['pickup_%s_%d' % (group, index)] = int(index in selected)
            except ValueError:
                # One damaged row must not discard subsequent equipment bans.
                continue
    except (OSError, ValueError):
        pass
    return result


def apply_pickup(values):
    osfInfo.PICKUP_MODE = values['pickup_mode']
    player.PickupBlockMinLvl(values['pickup_min'])
    player.PickupBlockMaxLvl(values['pickup_max'])
    for group, count, setter in (('class', 4, player.PickupBlockClassType),
                                  ('weapon', 7, player.PickupBlockWeaponType),
                                  ('armor', 7, player.PickupBlockArmorType)):
        for index in range(count):
            setter(bool(values['pickup_%s_%d' % (group, index)]), index)


def load_pickup():
    # Loading clears native player state even when the Python window survives.
    # Apply a complete character snapshot, including cleared seventh slots.
    apply_pickup(model.normalized(read_pickup()))


def save_pickup(values):
    lines = ['pick_mode:%d' % values['pickup_mode'], 'min_lvl:%d' % values['pickup_min'],
             'max_lvl:%d' % values['pickup_max']]
    for group, count in (('class', 4), ('weapon', 7), ('armor', 7)):
        lines.append('block_%s:%s' % (group, ','.join(str(i) for i in range(count)
                                                    if values['pickup_%s_%d' % (group, i)])))
    atomic_write(pickup_path(), ('\n'.join(lines) + '\n').encode('ascii'))
    apply_pickup(values)


def ui_scale_info():
    methods = ('GetUIScale', 'SetUIScale', 'GetUIScaleInfo', 'GetUIScaleRange')
    if not all(callable(getattr(systemSetting, name, None)) for name in methods):
        return None
    if tuple(systemSetting.GetUIScaleRange()) != (50, 150, 5):
        return None
    requested, active, maximum = systemSetting.GetUIScaleInfo()
    if (requested not in model.UI_SCALE_CHOICES or
            not all(math.isfinite(value) and value > 0 for value in (active, maximum))):
        return None
    return requested, active, maximum


def refresh_rate_info():
    getter = getattr(systemSetting, 'GetRefreshRateInfo', None)
    if not callable(getter):
        return None
    saved, active, windowed, supported = getter()
    rates = tuple(sorted({int(rate) for rate in supported if 2 <= int(rate) <= 1000}))
    return int(saved), int(active), bool(windowed), rates


def family_names_bridge():
    return all(callable(getattr(systemSetting, name, None)) for name in
               BINDINGS['family_names'] + ('CanChangeOwnFamilyNameVisibility',))


def family_names_supported():
    return family_names_bridge() and bool(systemSetting.CanChangeOwnFamilyNameVisibility())


def family_names_value():
    return int(bool(systemSetting.IsOwnFamilyNameVisible())) if family_names_bridge() else 0


def request_family_names(value):
    return family_names_supported() and bool(systemSetting.SetOwnFamilyNameVisible(int(bool(value))))


def background_fps_supported():
    # Older executables keep a fixed inactive-window limit; the row is then hidden.
    return all(callable(getattr(app, name, None)) for name in ('SetBackgroundFPS', 'GetBackgroundFPSLimit'))


def tree_shadow_supported():
    # Older clients lack the native limit; the setting is then shown disabled.
    return all(callable(getattr(background, name, None))
               for name in ('SetTreeShadowDistance', 'GetTreeShadowDistance'))


def saved_tree_shadow(preferences):
    """Persisted tree shadow distance; older files follow their saved preset."""
    value = preferences.get('tree_shadow') if isinstance(preferences, dict) else None
    if value is None and isinstance(preferences, dict) and preferences.get('quality_preset') in range(4):
        value = model.QUALITY_PRESETS[preferences['quality_preset']]['tree_shadow']
    return model.normalized(dict(tree_shadow=value))['tree_shadow']


def apply_tree_shadow(value):
    if not tree_shadow_supported():
        return False
    background.SetTreeShadowDistance(float(value))
    return True


def saved_dps_meter(preferences):
    """Ukazatel poškození (DPS) on (1, the default) or off (0), from the settings preferences file."""
    value = preferences.get('dps_meter') if isinstance(preferences, dict) else None
    return model.normalized(dict(dps_meter=1 if value is None else value))['dps_meter']


def load_dps_meter():
    """The saved DPS meter switch (uidpsmeter reads it once, lazily, when the first table is made)."""
    return saved_dps_meter(_read_json(PREFERENCES))


def dps_meter_enabled():
    """The live switch (uidpsmeter, shared by the Settings row and the target form's chip); the saved value when
    the module is not loaded yet."""
    import sys
    for name in ('uiDpsMeter', 'uidpsmeter'):
        module = sys.modules.get(name)
        if module is not None and callable(getattr(module, 'IsEnabled', None)):
            return int(bool(module.IsEnabled()))
    return load_dps_meter()


def set_dps_meter(value):
    """Settings row: saves the switch at once (only this key of the preferences file) and applies it live."""
    value = int(bool(value))
    preferences = _read_json(PREFERENCES) or dict(version=1)
    preferences['dps_meter'] = value
    atomic_write(PREFERENCES, json.dumps(preferences, sort_keys=True).encode('utf-8'))
    apply_dps_meter(value)
    return value


def apply_dps_meter(value):
    """Live: off collapses an open DPS section and drops the snapshots; on takes the next snapshot again."""
    import sys
    done = False
    # uitarget imports the module as uiDpsMeter, uidpsmeterr1 as uidpsmeter: every loaded copy gets the switch
    for name in ('uiDpsMeter', 'uidpsmeter'):
        module = sys.modules.get(name)
        if module is not None and callable(getattr(module, 'SetEnabled', None)):
            module.SetEnabled(bool(value))
            done = True
    if not done:
        try:
            import uidpsmeter
            uidpsmeter.SetEnabled(bool(value))
            done = True
        except Exception:
            pass
    return done


def load_tree_shadow():
    """Game start: the native limit is not persisted by the client itself."""
    return apply_tree_shadow(saved_tree_shadow(_read_json(PREFERENCES)))


def load_effect_switches():
    """Game start: hand the saved effect switches to the effect manager. A metin2.cfg without them (first start)
    otherwise leaves the effects hidden while the switches already read as on."""
    for unused, index in EFFECT_SWITCHES:
        systemSetting.SetBLEffectOption(index, bool(systemSetting.GetBLEffectOption(index)))


class GameBackend:
    def __init__(self, get_block):
        self.get_block = get_block
        self.block_requests = []

    def confirm_block(self, mode):
        """Keep later clicks visible while ordered server acknowledgements arrive."""
        mode = int(mode) & 127
        if mode in self.block_requests:
            del self.block_requests[:self.block_requests.index(mode)+1]
        else:
            # An unexpected authoritative value (including a rejection) wins.
            self.block_requests = []
        return self.block_requests[-1] if self.block_requests else mode

    def interface(self):
        return osfInfo.GetInterfaceInstance()

    def read_preferences(self):
        return _read_json(PREFERENCES)

    def read_colors(self):
        return systemSetting.GetWorldVisualPreview()

    def read(self):
        values = dict(model.DEFAULTS)
        for key, (getter, unused) in BINDINGS.items():
            if key == 'damage_height' and not callable(getattr(systemSetting, getter, None)):
                continue
            if key in DAMAGE_KEYS and not damage_supported():
                continue
            if key == 'family_names' and not family_names_bridge():
                continue
            values[key] = getattr(background if key == 'fog' else systemSetting, getter)()
        if name_visibility_supported():
            for category, key in enumerate(model.NAME_VISIBILITY_KEYS):
                values[key] = systemSetting.GetNameVisibility(category)
        values['font'] = fontconfig.NormalizeFontLevel(values['font'])
        values['sound'] /= 5.
        values['npc_names'] = int(not values['npc_names'])
        values['special_effects'] = {0: 0, 1: 1, 2: 0, 3: 1, 4: 2}.get(values['special_effects'], 0)
        for key, index in EFFECT_SWITCHES:
            values[key] = int(bool(systemSetting.GetBLEffectOption(index)))
        for key, default in (('fps', 60), ('background_fps', 30), ('vsync', 1), ('show_fps', 0)):
            values[key] = cfg.Get(cfg.SAVE_OPTION, CFG_KEYS.get(key, key), str(default))
        if background_fps_supported():
            values['background_fps'] = app.GetBackgroundFPSLimit()
        scale = ui_scale_info()
        if scale is not None:
            values['ui_scale'] = systemSetting.GetUIScale()
        info = refresh_rate_info()
        values['refresh_hz'] = info[0] if info else 0
        values.update(read_pickup())
        values['pvp'] = player.GetPKMode()
        values['block'] = self.block_requests[-1] if self.block_requests else self.get_block()
        values['track'] = musicInfo.fieldMusic
        try:
            import pregamemusic
            values['menu_music'] = pregamemusic.ReadSetting()
        except Exception:
            values['menu_music'] = model.DEFAULTS['menu_music']
        values['tree_shadow'] = saved_tree_shadow(self.read_preferences())
        values['dps_meter'] = dps_meter_enabled()
        interface = self.interface()
        if interface:
            values['loot_lifetime'] = interface.GetDropTrackerRecentLifetime()
            values['loot_placement'] = int(interface.GetDropTrackerPlacementMode() == 'free')
            values['costumes'] = int(interface.IsSeparateCostumeInventory())
            manager = getattr(interface, 'systemNotifications', None)
            if manager:
                values.update(manager.store.preferences)
        return values

    def _validate(self, values, before):
        if values['pvp'] != before['pvp']:
            import localeInfo
            if player.GetStatus(player.LEVEL) < constInfo.PVPMODE_PROTECTED_LEVEL:
                raise SettingsValidationError(localeInfo.OPTION_PVPMODE_PROTECT % constInfo.PVPMODE_PROTECTED_LEVEL)
            if not constInfo.PVPMODE_ENABLE:
                raise SettingsValidationError(localeInfo.OPTION_PVPMODE_NOT_SUPPORT)
            if values['pvp'] == 4 and not player.GetGuildID():
                raise SettingsValidationError(localeInfo.OPTION_PVPMODE_CANNOT_SET_GUILD_MODE)
            if values['pvp'] not in (0, 1, 2, 4):
                raise ValueError('Unsupported PvP mode')
        if values['ui_scale'] != before['ui_scale'] and ui_scale_info() is None:
            from settingslocale import Text
            raise SettingsValidationError(Text('Velikost rozhran\u00ed nen\u00ed dostupn\u00e1.', 'UI scaling is unavailable.'))
        if values['refresh_hz'] != before['refresh_hz']:
            info = refresh_rate_info()
            if info is None or info[2] or (values['refresh_hz'] and values['refresh_hz'] not in info[3]):
                from settingslocale import Text
                raise SettingsValidationError(Text('Vybraná frekvence není dostupná.', 'The selected refresh rate is unavailable.'))
        sky = values['sky']
        if sky and sky != before['sky']:
            path = 'd:/ymir work/environment/jtx_skybox/env_%02d.msenv' % sky
            if not app.IsExistFile(path):
                from settingslocale import Text
                raise SettingsValidationError(Text('Vybraná obloha není dostupná.', 'The selected sky is unavailable.'))

    def _set_native(self, key, value):
        if key == 'damage_height' and not callable(getattr(systemSetting, 'SetDamageHeight', None)):
            return
        if key in DAMAGE_KEYS and not damage_supported():
            return
        if key == 'family_names':
            if not request_family_names(value):
                raise ValueError('Family-name visibility request is unavailable')
            return
        if key == 'special_effects':
            value = (0, 3, 4)[value]
        elif key == 'npc_names':
            value = int(not value)
        setter = BINDINGS[key][1]
        if key in ('rain', 'rain_fx', 'grass_radius'):
            getattr(background, setter)(value)
        else:
            getattr(systemSetting, setter)(value)
        if key in ('shadow_target', 'shadow_quality', 'fog'):
            getattr(background, setter)(value)
        if key == 'camera':
            app.SetCameraMaxDistance(7000. if value else 2500.)
        elif key in ('pet', 'mount', 'support', 'shop'):
            net.SendChatPacket('/show_hide_%s %d' % (key, value))
        elif key == 'affects':
            osfInfo.AffectIconState = 1
        elif key == 'quests':
            import interfacemodule
            interfacemodule.IsQBHide = not value
            if self.interface():
                self.interface().DynamicArrangeQuestBtn()
        elif key == 'sky':
            if not value:
                background.ClearUserEnvironmentSlot()
            else:
                slot = value + 19
                if slot not in SKY_REGISTERED:
                    background.RegisterEnvironmentData(slot, 'd:/ymir work/environment/jtx_skybox/env_%02d.msenv' % value)
                    SKY_REGISTERED.add(slot)
                background.SetUserEnvironmentSlot(slot)
        elif key == 'sound':
            snd.SetSoundVolumef(value)
        elif key == 'music':
            snd.SetMusicVolume(value * net.GetFieldMusicVolume())

    def preview(self, state, previous):
        """Continuous native feedback; final apply owns durable preferences."""
        for key, value in state['colors'].items():
            if value != previous['colors'][key]:
                if not systemSetting.SetWorldVisualPreview(key, value):
                    raise OSError('Unable to preview color preference')
        for key in ('fov', 'stone_size', 'damage_size', 'damage_height', 'sound', 'music', 'grass_radius'):
            if state['values'][key] != previous['values'][key]:
                self._set_native(key, state['values'][key])

    def apply(self, state, original):
        values, before = state['values'], original['values']
        self._validate(values, before)
        changed = {key for key in values if values[key] != before[key]}
        interface = self.interface()
        # Commit the complete desired color state after any live slider preview.
        # A failed save leaves the settings session available for retry.
        if (state['colors'], state['color_preset'], state['custom_colors']) != (
                original['colors'], original['color_preset'], original['custom_colors']):
            if not systemSetting.ApplyWorldVisualSettings(state['color_preset'], state['colors'], state['custom_colors']):
                raise OSError('Unable to save color preferences')
        if 'ui_scale' in changed:
            if not systemSetting.SetUIScale(values['ui_scale']):
                raise OSError('Unable to save UI scale preference')
        if 'refresh_hz' in changed:
            if not systemSetting.SetRefreshRate(values['refresh_hz']):
                from settingslocale import Text
                raise OSError(Text('Frekvenci se nepodařilo uložit.', 'Unable to save refresh rate.'))
        if any(key.startswith('pickup_') for key in changed):
            save_pickup(values)
        if 'font' in changed:
            atomic_write('UserData/font/fontoption.cfg', str(values['font']).encode('ascii'))
        if any(key in changed for key in NOTIFICATION_KEYS) and interface:
            manager = getattr(interface, 'systemNotifications', None)
            if manager and not manager.ApplyPreferences({key: bool(values[key]) for key in NOTIFICATION_KEYS}):
                raise OSError('Unable to save notification preferences')
        if any(key in changed for key in model.NAME_VISIBILITY_KEYS):
            if not name_visibility_supported():
                raise SettingsValidationError('Name visibility is unavailable')
            for category, key in enumerate(model.NAME_VISIBILITY_KEYS):
                if key in changed:
                    systemSetting.SetNameVisibility(category, values[key])
        # Base renderer first: all subsequent feature fields remain explicit.
        for key in BINDINGS:
            if key in changed:
                self._set_native(key, values[key])
        for key, index in EFFECT_SWITCHES:
            if key in changed:
                systemSetting.SetBLEffectOption(index, bool(values[key]))
        for key in ('fps', 'background_fps', 'vsync', 'show_fps'):
            if key in changed:
                cfg.Set(cfg.SAVE_OPTION, CFG_KEYS.get(key, key), str(values[key]))
        if 'fps' in changed:
            app.SetFPS(values['fps'])
        if 'background_fps' in changed and background_fps_supported():
            app.SetBackgroundFPS(values['background_fps'])
        if 'show_fps' in changed and interface and interface.wndMiniMap:
            interface.wndMiniMap.SetFPSCounterVisible(bool(values['show_fps']))
        if 'loot_placement' in changed and interface:
            interface.SetDropTrackerPlacementMode('free' if values['loot_placement'] else 'taskbar')
        if 'loot_lifetime' in changed and interface:
            if not interface.SetDropTrackerRecentLifetime(values['loot_lifetime']):
                raise OSError('Unable to save loot display duration')
        if 'costumes' in changed and interface:
            interface.SetSeparateCostumeInventory(bool(values['costumes']))
        if 'menu_music' in changed:
            import pregamemusic
            pregamemusic.WriteSetting(values['menu_music'])
        if 'track' in changed:
            if musicInfo.fieldMusic:
                snd.FadeOutMusic('BGM/' + musicInfo.fieldMusic)
            musicInfo.fieldMusic = values['track']
            musicInfo.SaveLastPlayFieldMusic()
            if musicInfo.fieldMusic:
                snd.FadeInMusic('BGM/' + musicInfo.fieldMusic)
        if 'tree_shadow' in changed:
            apply_tree_shadow(values['tree_shadow'])
        if 'dps_meter' in changed:
            apply_dps_meter(values['dps_meter'])
        if not systemSetting.SaveConfig():
            raise OSError('Unable to save native settings')
        preferences = dict(version=1, quality_preset=state['quality_preset'],
                           custom_quality=state['custom_quality'], tree_shadow=values['tree_shadow'],
                           dps_meter=values['dps_meter'] if 'dps_meter' in changed else dps_meter_enabled(),
                           quality_values={key: values[key] for key in model.QUALITY_KEYS})
        atomic_write(PREFERENCES, json.dumps(preferences, sort_keys=True).encode('utf-8'))
        # Requests go last, after local persistence. The next server snapshot
        # confirms PvP/block state; selecting an option grants no local authority.
        if 'pvp' in changed:
            net.SendChatPacket('/pkmode %d' % values['pvp'])
        if 'block' in changed:
            edited_bits = values['block'] ^ before['block']
            base = self.block_requests[-1] if self.block_requests else self.get_block()
            desired = (base & ~edited_bits) | (values['block'] & edited_bits)
            net.SendChatPacket('/setblockmode %d' % desired)
            self.block_requests.append(desired)
