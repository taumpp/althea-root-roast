# -*- coding: utf-8 -*-
"""Shared R1 window chrome and controls for the equipment render target."""
import ui
from _weakref import proxy
import uiScriptLocale
import uir1
import uir1tokens as T

WIDTH, HEIGHT = 350, 480


class Skin(object):
    def __init__(self, window):
        self.chrome = None
        self.body = None
        self.widgets = {}
        try:
            self.Build(window)
        except Exception:
            self.Destroy()
            raise

    def Build(self, window):
        kit = uir1.Kit()
        window.SetSize(WIDTH, HEIGHT)
        window.AddFlag('movable')
        window.AddFlag('float')
        self.chrome = uir1.Chrome(window, kit, WIDTH, HEIGHT,
                                 uiScriptLocale.RENDER_PREVIEW_TITLE,
                                 on_close=ui.__mem_func__(window.Close), kind='window')
        body = ui.Window()
        self.body = body
        body.SetParent(window)
        body.SetPosition(T.PAD, self.chrome.ContentTop())
        width = WIDTH - T.PAD * 2
        height = HEIGHT - self.chrome.ContentTop() - T.PAD
        body.SetSize(width, height)
        body.AddFlag('not_pick')
        body.Show()
        gap = T.CONTENT_GAP * 2
        hint_h = kit.cell('text_s')
        race_y = height - hint_h - gap - T.BTN_H
        sex_y = race_y - gap - T.BTN_H
        view = ui.RenderTarget()
        view.SetParent(body)
        view.SetPosition(0, 0)
        view.SetSize(width, sex_y - T.PAD)
        view.SetRenderTarget(2)
        view.Show()
        self.widgets['RenderBoard'] = view
        self.widgets['board'] = body
        control_w = (width - gap * 3) // 4
        labels = (
            ('MaleButton', uiScriptLocale.RENDER_PREVIEW_MALE),
            ('FemaleButton', uiScriptLocale.RENDER_PREVIEW_FEMALE),
            ('ZoomInButton', '+'), ('ZoomOutButton', '-'),
            ('WarriorButton', uiScriptLocale.RENDER_PREVIEW_WARRIOR),
            ('NinjaButton', uiScriptLocale.RENDER_PREVIEW_ASSASSIN),
            ('SuraButton', uiScriptLocale.RENDER_PREVIEW_SURA),
            ('ShamanButton', uiScriptLocale.RENDER_PREVIEW_SHAMAN),
        )
        for index, (name, label) in enumerate(labels):
            button = uir1.Button(body, kit, (index % 4) * (control_w + gap),
                                sex_y if index < 4 else race_y, control_w,
                                label.strip('[]'))
            self.widgets[name] = button
        self.widgets['ZoomInButton'].SetEvent(lambda r=proxy(window): r.OnMouseWheel(1))
        self.widgets['ZoomOutButton'].SetEvent(lambda r=proxy(window): r.OnMouseWheel(-1))
        self.widgets['hint'] = uir1.Text(
            body, uiScriptLocale.RENDER_PREVIEW_CONTROLS_HINT,
            width // 2, height - hint_h, kit.font('text_s'), T.INK_DIM,
            align='center', valign='top')
        for name, widget in self.widgets.items():
            window.InsertChild(name, widget)

    def Destroy(self):
        if self.body:
            self.body.Hide()
        if self.chrome:
            self.chrome.Destroy()
        self.widgets = {}
        self.body = None
        self.chrome = None
