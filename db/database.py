import json
from pathlib import Path
from .table import Table

class Database:
    def __init__(self, path="data/db.json"):
        self.path = Path(path)
        self.tables = {}
        self._load()

    def _load(self):
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            for name, table_data in raw.items():
                self.tables[name] = Table.from_dict(table_data, self)

    def save(self):
        data = {name: t.to_dict() for name, t in self.tables.items()}
        self.path.parent.mkdir(exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2))

    def create_table(self, name, columns, primary_key=None, unique_keys=None):
        if name in self.tables:
            return
        
        self.tables[name] = Table(name, columns, self, primary_key=primary_key, unique_keys=unique_keys)
        self.save()


    def t(self, name):
        return self.tables[name]
    
    
    def join(self, left, right, on_left, on_right):
        t1 = self.tables[left]
        t2 = self.tables[right]
        result = []

        for r1 in t1.rows:
            for r2 in t2.rows:
                if r1[on_left] == r2[on_right]:
                    result.append({**r1, **r2})

        return result