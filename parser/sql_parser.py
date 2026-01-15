import re
from typing import Dict


class SQLParser:
    
    @staticmethod
    def parse(sql: str) -> Dict:
        sql = sql.strip().rstrip(';')
        sql_upper = sql.upper()
        
        if sql_upper.startswith('CREATE TABLE'):
            return SQLParser._parse_create_table(sql)
        elif sql_upper.startswith('INSERT INTO'):
            return SQLParser._parse_insert(sql)
        elif sql_upper.startswith('SHOW TABLES'):
            return SQLParser._parse_show_tables(sql)
        elif sql_upper.startswith('SELECT'):
            return SQLParser._parse_select(sql)
        elif sql_upper.startswith('UPDATE'):
            return SQLParser._parse_update(sql)
        elif sql_upper.startswith('DELETE FROM'):
            return SQLParser._parse_delete(sql)
        else:
            raise ValueError(f"Unsupported SQL command: {sql}")
        
        
    @staticmethod
    def _parse_show_tables(sql: str) -> Dict:
        pattern = r'SHOW TABLES'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid SHOW TABLES syntax. Expected: SHOW TABLES")
        
        return {
            'type': 'SHOW_TABLES'
        }       
    
    @staticmethod
    def _parse_create_table(sql: str) -> Dict:
        pattern = r'CREATE TABLE (\w+)\s*\((.*)\)'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise ValueError("Invalid CREATE TABLE syntax. Expected: CREATE TABLE name (col1 TYPE, col2 TYPE)")
        
        table_name = match.group(1)
        columns_str = match.group(2)
        
        # Parse columns
        columns = []
        col_defs = [c.strip() for c in columns_str.split(',') if c.strip()]
        
        for col_def in col_defs:
            # Extract column info
            col_parts = col_def.split()
            if len(col_parts) < 2:
                raise ValueError(f"Invalid column definition: {col_def}")
            
            col_name = col_parts[0]
            col_type = col_parts[1].upper()
            
            # Check constraints
            constraints = ' '.join(col_parts[2:]).upper() if len(col_parts) > 2 else ''
            is_primary = 'PRIMARY KEY' in constraints
            is_unique = 'UNIQUE' in constraints or is_primary
            nullable = 'NOT NULL' not in constraints
            
            columns.append({
                'name': col_name,
                'type': col_type,
                'primary': is_primary,
                'unique': is_unique,
                'nullable': nullable
            })
        
        return {
            'type': 'CREATE_TABLE',
            'table_name': table_name,
            'columns': columns
        }
    
    @staticmethod
    def _parse_insert(sql: str) -> Dict:
        pattern1 = r'INSERT INTO (\w+)\s*\((.*?)\)\s*VALUES\s*\((.*)\)'
        match = re.match(pattern1, sql, re.IGNORECASE | re.DOTALL)
        
        if match:
            table_name = match.group(1)
            columns = [c.strip() for c in match.group(2).split(',')]
            values_str = match.group(3)
            return {
                'type': 'INSERT',
                'table_name': table_name,
                'columns': columns,
                'values_str': values_str
            }
        
        pattern2 = r'INSERT INTO (\w+)\s*VALUES\s*\((.*)\)'
        match = re.match(pattern2, sql, re.IGNORECASE | re.DOTALL)
        
        if match:
            table_name = match.group(1)
            values_str = match.group(2)
            return {
                'type': 'INSERT',
                'table_name': table_name,
                'columns': None,
                'values_str': values_str
            }
        
        raise ValueError("Invalid INSERT syntax. Expected: INSERT INTO table (col1, col2) VALUES (val1, val2)")
    
    @staticmethod
    def _parse_select(sql: str) -> Dict:
        # Check for JOIN
        if re.search(r'\bJOIN\b', sql, re.IGNORECASE):
            return SQLParser._parse_join(sql)

        
        pattern = r'SELECT (.*?) FROM (\w+)(?: WHERE (.*))?'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise ValueError("Invalid SELECT syntax. Expected: SELECT * FROM table WHERE condition")
        
        columns_str = match.group(1).strip()
        table_name = match.group(2).strip()
        where_clause = match.group(3).strip() if match.group(3) else None
        
        columns = [c.strip() for c in columns_str.split(',')] if columns_str != '*' else None
        
        return {
            'type': 'SELECT',
            'columns': columns,
            'table_name': table_name,
            'where_clause': where_clause
        }
    
    @staticmethod
    def _parse_join(sql: str) -> Dict:
        pattern = r'SELECT (.*?) FROM (\w+)\s+JOIN (\w+)\s+ON\s+(.*?)(?: WHERE (.*))?'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise ValueError("Invalid JOIN syntax. Expected: SELECT * FROM table1 JOIN table2 ON table1.id = table2.id")
        
        columns_str = match.group(1).strip()
        table1 = match.group(2).strip()
        table2 = match.group(3).strip()
        join_condition = match.group(4).strip()
        where_clause = match.group(5).strip() if match.group(5) else None
        
        columns = [c.strip() for c in columns_str.split(',')] if columns_str != '*' else None
        
        return {
            'type': 'JOIN',
            'columns': columns,
            'table1': table1,
            'table2': table2,
            'join_condition': join_condition,
            'where_clause': where_clause
        }
    
    @staticmethod
    def _parse_update(sql: str) -> Dict:
        pattern = r'UPDATE (\w+)\s+SET\s+([\s\S]*?)(?: WHERE (.*))?$'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise ValueError("Invalid UPDATE syntax. Expected: UPDATE table SET col1 = val1 WHERE condition")
        
        table_name = match.group(1).strip()
        set_clause = match.group(2).strip()
        where_clause = match.group(3).strip() if match.group(3) else None
        
        set_pairs = []
        for pair in set_clause.split(','):
            pair = pair.strip()
            if '=' not in pair:
                raise ValueError(f"Invalid SET pair: {pair}")
            col, val = pair.split('=', 1)
            set_pairs.append({
                'column': col.strip(),
                'value': val.strip()
            })
        
        return {
            'type': 'UPDATE',
            'table_name': table_name,
            'set_pairs': set_pairs,
            'where_clause': where_clause
        }
    
    @staticmethod
    def _parse_delete(sql: str) -> Dict:
        pattern = r'DELETE FROM (\w+)(?: WHERE (.*))?'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise ValueError("Invalid DELETE syntax. Expected: DELETE FROM table WHERE condition")
        
        table_name = match.group(1).strip()
        where_clause = match.group(2).strip() if match.group(2) else None
        
        return {
            'type': 'DELETE',
            'table_name': table_name,
            'where_clause': where_clause
        }