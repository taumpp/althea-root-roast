"""Place passive announcements around the live target/drop/DPS block."""
GAP = 12


def protected_rectangles(target):
    # Child IsShow alone does not account for a hidden parent.
    if target is None or not target.IsShow():
        return []
    windows = [target]
    windows.extend(getattr(target, name, None) for name in
                   ('target_details_thinboard', 'dpsMeter', 'monsterIndicators'))
    form = getattr(target, 'form', None)          # the unified target form: its sections under the header
    if form is not None:
        windows.append(getattr(form, 'body', None))
    result = []
    for window in windows:
        if window is not None and window.IsShow():
            x, y = window.GetGlobalPosition()
            width, height = window.GetWidth(), window.GetHeight()
            if width > 0 and height > 0:
                result.append((x, y, x + width, y + height))
    return result


def place(size, preferred, screen, obstacles, bottom=90):
    """Return an integer position, or None when the complete card cannot fit.

    Keep the authored size. Prefer moving below the target block, then beside
    it; never clamp a rejected position back over a protected rectangle.
    """
    width, height = map(int, size)
    max_x, max_y = screen[0] - width, screen[1] - bottom - height
    if max_x < 0 or max_y < 0:
        return None
    x = max(0, min(int(preferred[0]), max_x))
    y = max(0, min(int(preferred[1]), max_y))
    xs = [x, 0, max_x]
    ys = [y, 0, max_y]
    for left, top, right, lower in obstacles:
        xs.extend((left - GAP - width, right + GAP))
        ys.extend((lower + GAP, top - GAP - height))
    candidates = [(x, y)]
    candidates.extend((x, v) for v in sorted(set(ys)) if v > y)
    candidates.extend((u, v) for u in sorted(set(xs), key=lambda u: abs(u-x))
                      for v in sorted(set(ys), key=lambda v: abs(v-y)))
    for cx, cy in candidates:
        if not (0 <= cx <= max_x and 0 <= cy <= max_y):
            continue
        if all(cx + width + GAP <= left or cx >= right + GAP or
               cy + height + GAP <= top or cy >= lower + GAP
               for left, top, right, lower in obstacles):
            return int(cx), int(cy)
    return None
