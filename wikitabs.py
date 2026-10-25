# -*- coding: utf-8 -*-
"""Shared wiki section and filter tabs; native R1 skin."""
import uir1 as R
import uir1tokens as T

HEIGHT = T.WIKI_SEG_H
GAP = HEIGHT + 4


def create(w, parent, x, y, width, options, selected, event, font='Noto Sans:14a'):
    control = R.Segment(parent, w.kit, options, event=event, font=font,
                        width=width, height=HEIGHT)
    # Give longer labels room without changing option order or identities.
    needs = [R.TextWidth(cell.label)+16 for cell in control.cells]
    if needs and sum(needs) <= width and any(need > cell.GetWidth() for need, cell in zip(needs, control.cells)):
        left = 0
        extra = (width-sum(needs))//len(needs)
        for i, (cell, need) in enumerate(zip(control.cells, needs)):
            size = width-left if i == len(needs)-1 else need+extra
            cell.Place(left, size)
            left += size
    control.SetValue(selected)
    return w._Keep(control, parent, x, y, w.content)


def anchors(w, parent, x, y, width, options, positions, event, font='Noto Sans:14a'):
    options = list(options)
    control = create(w, parent, x, y, width, options, options[0][0], event, font)
    w.sectionTabs.append((control, positions))
    return control


def update(w):
    offset = max(0, -w.body.GetLocalPosition()[1])
    bottom = offset >= max(0, w.bodyHeight-w.viewHeight) and w.bodyHeight > w.viewHeight
    for control, positions in w.sectionTabs:
        known = [(key, positions[key]) for key in control.values if key in positions]
        if not known:
            continue
        before = [(key, y) for key, y in known if y <= offset+4]
        selected = max(before, key=lambda row:row[1])[0] if before else known[0][0]
        # The last section can be shorter than the viewport: it still becomes
        # active when the player reaches the document's end.
        control.SetValue(known[-1][0] if bottom else selected)
