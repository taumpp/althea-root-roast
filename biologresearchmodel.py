"""Bounded versioned research snapshots; no game imports or optimistic progress."""
MAX_RESEARCHES = 20


def decode_row(values):
    if len(values) not in (24, 28):
        raise ValueError("invalid biolog row length")
    fields = [int(value) for value in values]
    if any(value < 0 or value > 2147483647 for value in fields):
        raise ValueError("invalid biolog numeric field")
    (index, level, vnum, total, interval, stone, choose, elixir, elixir_cost,
     clock, clock_cost) = fields[:11]
    count, due, done, alarm, chosen = fields[-5:]
    if not (1 <= index <= MAX_RESEARCHES and 1 <= level <= 255 and vnum and
            1 <= total <= 10000 and 1 <= interval <= 604800 and choose in (0, 1) and
            elixir and clock and 1 <= elixir_cost <= 9999 and 1 <= clock_cost <= 9999 and
            count <= total + bool(stone) and done in (0, 1) and alarm in (0, 1) and
            0 <= chosen <= 3):
        raise ValueError("invalid biolog row")
    return dict(index=index, level=level, vnum=vnum, total=total, interval=interval,
                stone=stone, choose=bool(choose), elixir=elixir, elixir_cost=elixir_cost,
                clock=clock, clock_cost=clock_cost,
                rewards=list(zip(fields[11:-5:2], fields[12:-5:2])),
                count=count, due=due, done=bool(done), alarm=bool(alarm), chosen=chosen)


def phase(row):
    if row["done"]:
        return "completed"
    if row["count"] < row["total"]:
        return "mission"
    if row["stone"] and row["count"] == row["total"]:
        return "stone"
    return "gift"


def legacy_rows(catalog, active, count=0, due=0, alarm=False, mode="mission"):
    """Rows for an old server, from catalogue prefixes in BiologRow3 order."""
    rows = {}
    for data in catalog:
        index, total, stone = data[0], data[3], data[5]
        row_count = count if index == active else (total if index < active else 0)
        if index == active and mode in ("stone", "gift"):
            row_count = total + int(mode == "gift" and bool(stone))
        values = list(data) + [row_count, due if index == active else 0, int(index < active),
                               int(index == active and alarm), 0]
        rows[index] = decode_row(values)
    return rows


def submission(row, now, level, inventory, elixir=False, clock=False, available=True):
    """UI eligibility only; the server revalidates every input before consumption."""
    state = phase(row)
    if not available or level < row["level"] or state == "completed":
        return False
    if state == "gift":
        return True
    if state == "stone":
        return inventory(row["stone"]) >= 1
    if inventory(row["vnum"]) < 1:
        return False
    if elixir and inventory(row["elixir"]) < row["elixir_cost"]:
        return False
    if row["due"] > now and (not clock or inventory(row["clock"]) < row["clock_cost"]):
        return False
    return True


def duration(seconds):
    seconds = max(0, int(seconds))
    return "%02d:%02d:%02d" % (seconds // 3600, seconds // 60 % 60, seconds % 60)


def passive_totals(rows):
    totals = {}
    for row in rows.values():
        if not row["done"]:
            continue
        rewards = row["rewards"]
        if row["choose"]:
            chosen = row["chosen"]
            rewards = [rewards[chosen - 1]] if 1 <= chosen <= len(rewards) else []
        for kind, value in rewards:
            if kind and value:
                totals[kind] = totals.get(kind, 0) + value
    return totals


class Snapshot:
    def __init__(self):
        self.expected = 0
        self.rows = {}
        self.invalid = False

    def begin(self, count):
        self.expected = int(count)
        self.rows = {}
        self.invalid = self.expected not in (MAX_RESEARCHES - 1, MAX_RESEARCHES)

    def append(self, values):
        try:
            row = decode_row(values)
            if not self.expected or row["index"] in self.rows:
                raise ValueError("duplicate or unsolicited row")
            self.rows[row["index"]] = row
        except (ValueError, TypeError):
            self.invalid = True

    def finish(self):
        if self.invalid or set(self.rows) != set(range(1, self.expected + 1)) or not self.expected:
            return None
        result = self.rows
        self.expected = 0
        self.rows = {}
        return result
