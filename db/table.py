class Table:
    def __init__(self, name, columns, db=None, primary_key=None, unique_keys=None):
        self.name = name
        self.columns = columns
        self.primary_key = primary_key
        self.unique_keys = unique_keys or []
        self.db = db  # 🔹 NEW: reference to Database

        self.rows = []
        self.pk_index = {}
        self.unique_indexes = {k: {} for k in self.unique_keys}
        self._auto_id = 1

    def insert(self, row: dict):
        if self.primary_key and self.primary_key not in row:
            row[self.primary_key] = self._auto_id
            self._auto_id += 1

        if self.primary_key:
            pk = row[self.primary_key]
            if pk in self.pk_index:
                raise ValueError(f"Primary key '{self.primary_key}' violation: {pk}")

        for col in self.unique_keys:
            if row.get(col) in self.unique_indexes[col]:
                raise ValueError(f"Unique constraint violated on '{col}': {row.get(col)}")

        for col in row:
            if col not in self.columns:
                raise ValueError(f"Unknown column '{col}' for table '{self.name}'")

        for col in self.columns:
            row.setdefault(col, None)

        for col, col_type in self.columns.items():
            if row[col] is not None and not isinstance(row[col], col_type):
                raise TypeError(
                    f"Column '{col}' expects type {col_type.__name__}, got {type(row[col]).__name__}"
                )

        self.rows.append(row)

        if self.primary_key:
            self.pk_index[row[self.primary_key]] = row
        for col in self.unique_keys:
            self.unique_indexes[col][row[col]] = row

        self._persist()

    # get
    def find(self, column, value):
        if column == self.primary_key:
            return self.pk_index.get(value)
        if column in self.unique_indexes:
            return self.unique_indexes[column].get(value)
        return next((r for r in self.rows if r.get(column) == value), None)

    # Update / PUT
    def update(self, column, value, updates: dict):
        row = self.find(column, value)
        if not row:
            raise ValueError(f"Row not found for {column}={value}")

        if self.primary_key in updates:
            raise ValueError("Primary key cannot be updated")

        row.update(updates)
        self._persist()

    # delete
    def delete(self, column, value):
        row = self.find(column, value)
        if not row:
            return

        self.rows.remove(row)

        if self.primary_key:
            self.pk_index.pop(row[self.primary_key], None)
        for col in self.unique_keys:
            self.unique_indexes[col].pop(row.get(col), None)

        self._persist()

    def select(self, where=None):
        if not where:
            return list(self.rows)
        return [r for r in self.rows if all(r.get(k) == v for k, v in where.items())]

    def _persist(self):
        if self.db:
            self.db.save()

    def to_dict(self):
        return {
            "name": self.name,
            "columns": {k: v.__name__ for k, v in self.columns.items()},
            "primary_key": self.primary_key,
            "unique_keys": self.unique_keys,
            "rows": self.rows,
            "_auto_id": self._auto_id,
        }

    @classmethod
    def from_dict(cls, data, db):
        cols = {k: eval(v) for k, v in data["columns"].items()}
        table = cls(
            data["name"],
            cols,
            db=db,
            primary_key=data["primary_key"],
            unique_keys=data["unique_keys"],
        )
        table.rows = data["rows"]
        table._auto_id = data["_auto_id"]

        # rebuild indexes
        for r in table.rows:
            if table.primary_key:
                table.pk_index[r[table.primary_key]] = r
            for col in table.unique_keys:
                table.unique_indexes[col][r[col]] = r

        return table
