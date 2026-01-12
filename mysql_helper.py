import pymysql


class MySQLHelper:

    def __init__(self, host='localhost', user='root', password='', database=''):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
            self.cursor = self.conn.cursor()
            print("✓ 连接成功")
            return True
        except Exception as e:
            print(f"✗ 连接失败: {e}")
            return False

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✓ 连接已关闭")

    def run_sql(self, sql, params=None):
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)

            self.conn.commit()
            affected = self.cursor.rowcount
            print(f"✓ 执行成功，影响{affected}行")
            return affected

        except Exception as e:
            print(f"✗ 执行失败: {e}")
            self.conn.rollback()
            return 0

    def get_data(self, sql, params=None):
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)

            results = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]

            print(f"✓ 查询成功，找到{len(results)}条数据")
            return {
                'columns': columns,
                'data': results,
                'count': len(results)
            }

        except Exception as e:
            print(f"✗ 查询失败: {e}")
            return {'columns': [], 'data': [], 'count': 0}

    def insert(self, table, data):
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return self.run_sql(sql, tuple(data.values()))

    def select(self, table, where=None, params=None):
        sql = f"SELECT * FROM {table}"
        if where:
            sql += f" WHERE {where}"
        return self.get_data(sql, params)

    def update(self, table, data, where, where_params=None):
        set_parts = []
        params = []

        for key, value in data.items():
            set_parts.append(f"{key} = %s")
            params.append(value)

        set_clause = ', '.join(set_parts)
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"

        if where_params:
            params.extend(where_params)

        return self.run_sql(sql, tuple(params))

    def delete(self, table, where, params=None):
        sql = f"DELETE FROM {table} WHERE {where}"
        return self.run_sql(sql, params)

    def get_one(self, table, where, params=None):
        result = self.select(table, where, params)
        if result['data']:
            return result['data'][0]
        return None

    def count(self, table, where=None, params=None):
        sql = f"SELECT COUNT(*) FROM {table}"
        if where:
            sql += f" WHERE {where}"
        result = self.get_data(sql, params)
        if result['data']:
            return result['data'][0][0]
        return 0
