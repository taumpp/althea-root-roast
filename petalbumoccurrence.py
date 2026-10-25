"""Read-only geometry and availability for a durable album hunt."""
import math


def Available(row, utc):
    return bool(row and row.get('phase') == 1 and
                row.get('hunt_from', 0) <= utc < row.get('hunt_until', 0) and
                row.get('channel', 0) > 0 and
                row.get('area_id') and row.get('radius', 0) > 0)


def Identity(context, row):
    return (context, row['hunt_high'], row['hunt_low'], row['hunt_revision'],
            row['area_id'], row['map'], row['channel'])


def Layout(map_width, map_height, units_width, units_height, x, y, radius,
           screen_width, screen_height):
    if min(map_width, map_height, units_width, units_height, radius) <= 0:
        raise ValueError('invalid occurrence geometry')
    if not 0 <= x < units_width or not 0 <= y < units_height:
        raise ValueError('occurrence center outside map')
    scale = min(1.0, 512.0 / map_width, 512.0 / map_height,
                max(1, screen_width-64) / float(map_width),
                max(1, screen_height-208) / float(map_height))
    width, height = round(map_width*scale), round(map_height*scale)
    sx, sy = width / float(units_width), height / float(units_height)
    ring = ((x-radius)*sx, (y-radius)*sy, 2*radius*sx, 2*radius*sy)
    return width, height, scale, ring


def OutlineRows(ring, width, height, thickness):
    """Cache a screen-pixel ellipse stroke, clipped to the atlas bounds."""
    left, top, diameter_x, diameter_y = ring
    cx, cy = left+diameter_x/2.0, top+diameter_y/2.0
    rx, ry = diameter_x/2.0, diameter_y/2.0
    outer_x, outer_y = rx+thickness/2.0, ry+thickness/2.0
    inner_x, inner_y = max(0, rx-thickness/2.0), max(0, ry-thickness/2.0)
    rows = []
    for y in range(max(0, int(math.floor(cy-outer_y))),
                   min(height, int(math.ceil(cy+outer_y)))):
        dy = y+0.5-cy
        if abs(dy) >= outer_y:
            continue
        outer = outer_x*math.sqrt(1-(dy/outer_y)**2)
        spans = [(cx-outer, cx+outer)]
        if inner_y and abs(dy) < inner_y:
            inner = inner_x*math.sqrt(1-(dy/inner_y)**2)
            spans = [(cx-outer, cx-inner), (cx+inner, cx+outer)]
        for start, end in spans:
            start = max(0, int(math.ceil(start-0.5)))
            end = min(width, int(math.ceil(end-0.5)))
            if end > start:
                rows.append((start, y, end-start, 1))
    return tuple(rows)
