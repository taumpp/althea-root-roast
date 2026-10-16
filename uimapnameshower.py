# -*- coding: utf-8 -*-
"""Shared, click-through map arrival using the approved Crimson Gate artwork."""
import app
import dbg
import ui
import wndMgr

import maparrivalfont as font
import maparrivalnames
import maparrivalstyle as style


class MapNameShower(ui.Window):
    def __init__(self):
        ui.Window.__init__(self, "TOP_MOST")
        self.AddFlag("not_pick")
        self._art = []
        self._shadow = []
        self._title = []
        self._shine = []
        self._started = 0.0
        self._viewport = None
        self.Hide()

    def _image(self, path, x=0.0, y=0.0, scale=1.0, strip=False):
        image = ui.ExpandedImageBox()
        image.SetParent(self)
        image.AddFlag("not_pick")
        image.LoadImage(style.ASSET_ROOT + path)
        image.SetAlpha(0.0)
        image.Show()
        center = x + image.GetWidth() * scale / 2.0
        return (image, x, y, scale, center, strip)

    def _clear_title(self):
        # Hide before releasing Python owners; never leave the previous name
        # visible when an unknown map or a failed image replaces this arrival.
        for image, x, y, scale, center, strip in self._shadow + self._title + self._shine:
            image.Hide()
        self._shadow = []
        self._title = []
        self._shine = []

    def _load_art(self):
        if self._art:
            return
        images = []
        for index in range(style.ART_STRIPS):
            x = index * style.ART_STRIP_WIDTH
            images.append(self._image("art/%02d.sub" % index, x, strip=True))
        self._art = images

    def _load_title(self, title):
        cached = font.TITLE_CACHE.get(title)
        if cached:
            self._title.append(self._image(cached[0]))
            for index in range(style.ART_STRIPS):
                x = index * style.ART_STRIP_WIDTH
                self._shine.append(self._image("art/city_shine_%02d.sub" % index, x, strip=True))
            return
        glyphs, scale = style.glyph_layout(title, font.GLYPHS, font.KERNING)
        # All shadows are below all gold glyphs: italic overhangs must not be
        # covered by a following letter's shadow.
        for kind, children in (("shadow", self._shadow), ("gold", self._title),
                               ("shine", self._shine)):
            for code, x, y in glyphs:
                children.append(self._image("glyphs/%04x_%s.sub" % (code, kind),
                                            x, y, scale))

    def _place(self):
        viewport = style.viewport(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        if viewport == self._viewport:
            return
        self._viewport = viewport
        left, top, scale = viewport
        self.SetPosition(left, top)
        self.SetSize(int(round(style.CANVAS_WIDTH * scale)),
                     int(round(style.CANVAS_HEIGHT * scale)))
        # Quantize shared boundaries, not each strip's width independently;
        # fractional viewport scales must not create cracks between art strips.
        for image, x, y, local_scale, center, strip in self._art + self._shadow + self._title + self._shine:
            image.SetPosition(int(round(x * scale)), int(round(y * scale)))
            if strip:
                width = round((x + style.ART_STRIP_WIDTH) * scale) - round(x * scale)
                image.SetScale(width / float(style.ART_STRIP_WIDTH), scale)
            else:
                image.SetScale(local_scale * scale, local_scale * scale)

    def ShowMapName(self, mapName, x, y):
        # x/y remain part of the native game hook. Presentation shows one
        # official map name, without separate floor/objective subtitles.
        self.Hide()
        self._clear_title()
        title = maparrivalnames.resolve(mapName)
        if not title:
            return
        title = style.normalize_title(title)
        try:
            self._load_art()
            self._load_title(title)
        except RuntimeError as error:
            self._clear_title()
            dbg.TraceError("Map arrival assets unavailable: %s" % error)
            return
        if not self._title:
            return
        self._viewport = None
        self._started = app.GetTime()
        self._place()
        self.Show()
        self.Update()

    def Update(self):
        # Existing GameWindow.Update owns the tick; no second OnUpdate loop.
        if not self.IsShow():
            return
        elapsed = max(0.0, app.GetTime() - self._started)
        if elapsed >= style.DURATION:
            self.Hide()
            return
        self._place()
        reveal, title_alpha, fade = style.animation(elapsed)
        for image, x, y, scale, center, strip in self._art:
            amount = max(0.0, min(1.0, (reveal * (style.CANVAS_WIDTH + 60) - center) / 45.0))
            image.SetAlpha(amount * fade)
        for image, x, y, scale, center, strip in self._shadow + self._title:
            image.SetAlpha(title_alpha)
        shine_x = (elapsed - 1.15) / 0.65 * style.CANVAS_WIDTH
        for image, x, y, scale, center, strip in self._shine:
            amount = max(0.0, 1.0 - abs(center - shine_x) / 30.0)
            image.SetAlpha(amount * 0.26 * title_alpha if 1.15 < elapsed < 1.8 else 0.0)
