# -*- coding: utf-8 -*-
"""Compact world loot tables over the connected TAB-scoped catalogue."""
from _weakref import proxy
import nonplayer
import ui
import WikiRenderTarget
import wikitabs as Tabs
import uir1 as R
import uir1tokens as T
import wikicatalog as M
import wikiarticles as A
import wikihome as H
from wikilocale import Text as L

# Wire enum common/length.h: CHAR_TYPE_STONE (not a content/VNUM classifier).
STONE_TYPE = 2


class LiveModel(object):
    """Same native rotating target as mission books, owned only while visible."""
    def __init__(self, parent, x, y, width, height, vnum):
        self.index = None
        self.vnum = vnum
        self.top, self.height = y, height
        self.view = ui.WikiRenderTargetUi()
        self.view.SetParent(parent)
        self.view.AddFlag('not_pick')
        self.view.SetPosition(x, y)
        self.view.SetSize(width, height)
        self.view.Hide()

    def Open(self):
        if self.index is not None:
            return
        try:
            index = int(WikiRenderTarget.GetFreeIndex(86, 1000000))
            # The widget binds uint8. An exhausted pool never aliases another target.
            if not 1 <= index <= 255:
                return
            self.index = index
            self.view.SetRenderTarget(index)
            WikiRenderTarget.SetBackground(index, 'd:/ymir work/ui/game/crimson_ember/mount_system/k1/preview_254x266.png')
            WikiRenderTarget.SetRotation(index, True)
            WikiRenderTarget.SetScale(index, 0.8)
            WikiRenderTarget.SelectModel(index, self.vnum)
            WikiRenderTarget.SetVisibility(index, True)
            self.view.Show()
        except (AttributeError, RuntimeError, TypeError, ValueError):
            self.Close()

    def Close(self):
        index, self.index = self.index, None
        self.view.Hide()
        if index is not None:
            try:
                WikiRenderTarget.SetVisibility(index, False)
            except (AttributeError, RuntimeError):
                pass
            try:
                WikiRenderTarget.Remove(index)
            except (AttributeError, RuntimeError):
                pass


def entries(catalog, kind, location=None, query='', target=None):
    # World listings use teleport TAB destinations only. Dungeon-only maps stay
    # in the dedicated dungeon UI even though the shared catalogue contains them.
    import teleportmapdata
    teleport_maps = {M.number(r['map_index']) for r in teleportmapdata.DESTINATIONS}
    query = M.folded(query)
    cache_key = (tuple(sorted(teleport_maps)), kind, location, query, target)
    cache = getattr(catalog, '_world_cache', None)
    if cache is None:
        cache = catalog._world_cache = {}
    if cache_key in cache:
        return cache[cache_key]
    grouped = {}
    for mob in catalog.mobs:
        vnum, map_id = M.number(mob['vnum']), M.number(mob['map'])
        if map_id not in teleport_maps or map_id not in catalog.maps or (location is not None and map_id != location):
            continue
        if target is not None and vnum != target:
            continue
        if kind == 'metin':
            if M.number(mob.get('type'), -1) != STONE_TYPE:
                continue
        elif not M.truth(mob.get('boss')):
            continue
        name = nonplayer.GetMonsterName(vnum)
        if query and query not in M.folded(name) and query not in M.folded(catalog.MapName(map_id)):
            continue
        row = grouped.setdefault(vnum, dict(vnum=vnum, name=name, level=M.number(mob.get('level')), maps=set(), drops={}))
        row['maps'].add(map_id)
        for drop in M.rows(mob.get('drops')):
            item, count = M.number(drop['vnum']), M.number(drop['count'])
            if item not in catalog.available or count <= 0:
                continue
            proto = catalog.items[item]
            key = (M.family_name(catalog.names[item]), M.number(proto.get('type')), M.number(proto.get('subtype')),
                   M.number(drop.get('min_level')), M.truth(drop.get('gloves')))
            entry = row['drops'].setdefault(key, dict(variants={}, maps=set(), min_level=key[3], gloves=key[4]))
            entry['maps'].add(map_id)
            entry['variants'].setdefault(item, set()).add(count)
    result = sorted(grouped.values(), key=lambda r: (r['level'], M.folded(r['name']), r['vnum']))
    for row in result:
        row['maps'] = sorted(row['maps'], key=catalog.MapKey)
        row['drops'] = sorted(row['drops'].values(), key=lambda drop: catalog.FamilyKey(drop['variants']))
        for drop in row['drops']:
            drop['variants'] = {v: tuple(sorted(counts)) for v, counts in drop['variants'].items()}
    if len(cache) >= 16:
        cache.clear()
    cache[cache_key] = result
    return result


def redraw(w):
    w.UpdateBreadcrumb()
    w.Draw()
    w.SaveHistory()


def select_kind(w, kind):
    w.worldKind, w.worldMob, w.worldChoosingMap = kind, None, False
    w.worldDropPages, w.worldMapPages = {}, {}
    w.scroll.SetPos(0)
    w.DrawSidebar()
    redraw(w)


def select_map(w, location):
    w.location, w.worldMob, w.worldChoosingMap = location, None, False
    w.worldDropPages, w.worldMapPages = {}, {}
    w.scroll.SetPos(0)
    redraw(w)


def choose_map(w):
    w.worldChoosingMap = not w.worldChoosingMap
    w.scroll.SetPos(0)
    redraw(w)


def page(w, field, vnum, value):
    getattr(w, field)[vnum] = value
    # Paging a long drop must not jump the containing world list.
    w.restoreScroll = w.scroll.GetPos()
    redraw(w)


def focus(w, vnum):
    w.worldMob = None if w.worldMob == vnum else vnum
    w.scroll.SetPos(0)
    redraw(w)


def small_button(w, parent, x, y, width, text, event, height=22):
    button = w._Button(parent, x, y, width, text, event)
    button.SetSize(width, height)
    button.band.Resize(0, 0, width, height)
    button.label.SetPosition(7, 1)
    return button


def draw(w, query=''):
    catalog, owner, x, width = w.receiver.catalog, proxy(w), H.ARTICLE_X, w.pageWidth-8
    title = L('detail_'+w.worldKind)
    A.heading(w, L('maps')+' / '+title, title)
    Tabs.create(w,w,x,101,208,[('boss',L('detail_boss')),('metin',L('detail_metin'))],
                w.worldKind,lambda value,r=owner:select_kind(r,value))
    map_name = catalog.MapName(w.location) if w.location in catalog.maps else L('world_all_maps')
    w._Button(w, x+224, 101, width-224, map_name, lambda r=owner: choose_map(r), arrow=w.worldChoosingMap)
    if w.worldChoosingMap:
        A.viewport(w, 143, 10)
        small_button(w, w.body, 0, 0, width, L('world_all_maps'), lambda r=owner: select_map(r, None), 27)
        maps = sorted({m for row in entries(catalog, w.worldKind) for m in row['maps']}, key=catalog.MapKey)
        y = 30
        for map_id in maps:
            small_button(w, w.body, 0, y, width, catalog.MapName(map_id), lambda m=map_id, r=owner: select_map(r, m), 27)
            y += 29
        return y
    location_width = 140 if w.compact else 158
    left, middle = 62, width-location_width-62
    w._Rect(w, x, 140, width, 22, A.BAND)
    w.ExactText(w, x+8, 144, L('world_loot'), 'Noto Sans:14a', T.IVORY)
    w.ExactText(w, x+width-location_width+9, 144, L('world_locations'), 'Noto Sans:14a', T.IVORY)
    A.viewport(w, 162, 24)
    rows = entries(catalog, w.worldKind, w.location, query, w.worldMob)
    y = 0
    if not rows:
        return w._Flow(y+10, L('empty'))
    for row in rows:
        vnum, drops = row['vnum'], row['drops']
        cols = max(1, (middle-12)//34)
        per_page = cols*2
        pages = max(1, (len(drops)+per_page-1)//per_page)
        selected = min(max(0, w.worldDropPages.get(vnum, 0)), pages-1)
        height = 119 if pages > 1 else 94
        right = width-location_width
        w._Rect(w.body, 0, y, width, height, 0xff121010)
        for xx in (left, right):
            w._Rect(w.body, xx, y, 1, height, T.LINE)
        w._Rect(w.body, 0, y, width, 1, T.LINE)
        w._Rect(w.body, left+1, y+1, middle-1, 23, A.BAND)
        header = small_button(w, w.body, left+1, y+1, middle-1, '', lambda v=vnum, r=owner: focus(r, v))
        w.ExactText(header, 7, 4, row['name'], 'Althea Caps:15a', T.IVORY, width=middle-87)
        w.ExactText(header, middle-10, 5, L('level')+' '+str(row['level']), 'Noto Sans:13a', align='right')
        model = LiveModel(w.body, 0, y+1, left, height-1, vnum)
        w.modelPreviews.append(model)
        w.content.append(model.view)
        for i, drop in enumerate(drops[selected*per_page:(selected+1)*per_page]):
            counts = sorted({n for values in drop['variants'].values() for n in values})
            caption = str(counts[0]) if len(counts) == 1 else '%d–%d' % (counts[0], counts[-1])
            item = min(drop['variants'])
            icon = w._Icon(w.body, left+7+i%cols*34, y+27+i//cols*34, item, caption)
            if icon.count and not caption.isdigit():
                R.Fit(icon.count, caption, 32)
            icon.variants = drop['variants']
            icon.extraLines = []
            if set(drop['maps']) != set(row['maps']):
                icon.extraLines.extend(catalog.MapName(m) for m in sorted(drop['maps']))
            if drop['min_level']:
                icon.extraLines.append(L('level')+' %d+' % drop['min_level'])
            if drop['gloves']:
                icon.extraLines.append(L('gloves'))
        if not drops:
            w.ExactText(w.body, left+7, y+34, L('world_no_drop'), 'Noto Sans:13a', width=middle-14)
        if pages > 1:
            w.ExactText(w.body, left+7, y+height-20, '%d–%d / %d' % (selected*per_page+1, min((selected+1)*per_page, len(drops)), len(drops)), 'Noto Sans:13a')
            w.ExactText(w.body, right-42, y+height-20, '%d / %d' % (selected+1, pages), 'Noto Sans:13a', align='center')
            for delta, xx, enabled in ((-1, right-88, selected>0), (1, right-26, selected+1<pages)):
                text = '‹' if delta < 0 else '›'
                if enabled:
                    small_button(w, w.body, xx, y+height-23, 22, text,
                                 lambda n=selected+delta, v=vnum, r=owner: page(r, 'worldDropPages', v, n))
                else:
                    w.ExactText(w.body, xx+7, y+height-20, text, color=T.INK_DIM)
        maps = row['maps']
        per_location_page = 4 if height > 94 else 3
        map_pages = max(1, (len(maps)+per_location_page-1)//per_location_page)
        map_page = w.worldMapPages.get(vnum, 0) % map_pages
        for i, map_id in enumerate(maps[map_page*per_location_page:(map_page+1)*per_location_page]):
            small_button(w, w.body, right+2, y+9+i*21, location_width-5, catalog.MapName(map_id),
                         lambda m=map_id, r=owner: select_map(r, m), 20)
        if map_pages > 1:
            small_button(w, w.body, right+2, y+height-22, location_width-5, L('world_more_maps')+' %d/%d' % (map_page+1, map_pages),
                         lambda n=(map_page+1)%map_pages, v=vnum, r=owner: page(r, 'worldMapPages', v, n), 20)
        y += height+4
    w.ExactText(w, x, w.windowHeight-20, L('world_hint'), 'Noto Sans:12a', width=width)
    return y
