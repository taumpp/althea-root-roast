"""Inventory references, never local item moves or fabricated stacks."""

class Basket:
    def __init__(self):
        self.sources = []
        self.limit = 0

    def clear(self):
        del self.sources[:]

    def add(self, window, cell, vnum, count, material):
        if count <= 0 or vnum <= 0 or len(self.sources) >= self.limit:
            return False
        if any(row['window']==window and row['cell']==cell for row in self.sources):
            return False
        self.sources.append(dict(window=window, cell=cell, vnum=vnum,
                                 count=count, material=material, id=0))
        return True

    def acknowledge(self, window, cell, identity, vnum, count):
        for row in self.sources:
            if (row['window'],row['cell'],row['vnum'],row['count']) == (window,cell,vnum,count):
                if not row['id'] or row['id']==identity:
                    row['id']=identity
                    return True
        return False

    def remove(self, row):
        if row in self.sources:
            self.sources.remove(row)

    def prune(self, read):
        kept=[row for row in self.sources if read(row['window'],row['cell']) == (row['vnum'],row['count'])]
        changed=len(kept)!=len(self.sources)
        self.sources[:]=kept
        return changed

    def refresh_after_make(self, read):
        kept=[]
        for row in self.sources:
            vnum,count=read(row['window'],row['cell'])
            if vnum==row['vnum'] and count>0:
                row['count']=count
                kept.append(row)
        self.sources[:]=kept
