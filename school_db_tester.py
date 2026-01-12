import pymysql
from mysql_helper import MySQLHelper


class SchoolDBTester:
    """学校数据库测试类"""

    def __init__(self):
        """初始化测试类"""
        self.db = MySQLHelper(
            host='localhost',
            user='root',
            password='123456',  # 改成你的密码
            database='school_db'
        )
        self.test_passed = 0
        self.test_failed = 0

    def setup(self):
        """准备测试环境"""
        print("准备测试环境...")
        if not self.db.connect():
            print("❌ 数据库连接失败")
            return False
        return True

    def cleanup(self):
        """清理测试环境"""
        print("\n清理测试环境...")
        self.db.close()
        print(f"测试结果：通过 {self.test_passed} 个，失败 {self.test_failed} 个")

    def run_test(self, test_func, test_name):
        """运行单个测试并统计结果"""
        try:
            print(f"\n🔧 开始测试：{test_name}")
            test_func()
            self.test_passed += 1
            print(f"✅ 测试通过：{test_name}")
            return True
        except Exception as e:
            self.test_failed += 1
            print(f"❌ 测试失败：{test_name}")
            print(f"   错误信息：{e}")
            return False

    # ---------- 具体的测试用例 ----------

    def test_connection(self):
        """测试数据库连接"""
        if not self.db.connect():
            raise Exception("数据库连接失败")

        # 验证连接是否有效
        result = self.db.get_data("SELECT 1")
        assert result['count'] == 1, "连接测试查询失败"

    def test_create_table(self):
        """测试创建表"""
        create_sql = """
                     CREATE TABLE IF NOT EXISTS test_students \
                     ( \
                         student_id \
                         INT \
                         PRIMARY \
                         KEY \
                         AUTO_INCREMENT, \
                         name \
                         VARCHAR \
                     ( \
                         50 \
                     ) NOT NULL,
                         height DECIMAL \
                     ( \
                         5, \
                         2 \
                     )
                         ) \
                     """
        affected = self.db.run_sql(create_sql)
        assert affected == 0, "创建表应该影响0行"

        # 验证表是否存在
        result = self.db.get_data("SHOW TABLES LIKE 'test_students'")
        assert result['count'] == 1, "表应该存在"

    def test_insert_data(self):
        """测试插入数据"""
        test_data = {'name': '测试学生', 'height': 170.5}

        # 插入数据
        affected = self.db.insert('test_students', test_data)
        assert affected == 1, "应该插入1行数据"

        # 验证数据是否插入成功
        result = self.db.select('test_students', 'name = %s', ('测试学生',))
        assert result['count'] == 1, "应该能找到插入的数据"
        assert result['data'][0][2] == 170.5, "身高数据应该匹配"

    def test_select_data(self):
        """测试查询数据"""
        # 插入一些测试数据
        students = [
            {'name': '学生A', 'height': 165.0},
            {'name': '学生B', 'height': 175.0},
            {'name': '学生C', 'height': 180.0}
        ]

        for student in students:
            self.db.insert('test_students', student)

        # 测试查询所有
        result = self.db.select('test_students')
        assert result['count'] >= 3, "至少应该有3条数据"

        # 测试条件查询
        result = self.db.select('test_students', 'height > %s', (170,))
        assert result['count'] >= 2, "应该有至少2个身高>170的学生"

    def test_update_data(self):
        """测试更新数据"""
        # 先插入一条数据
        self.db.insert('test_students', {'name': '要更新的学生', 'height': 160.0})

        # 更新数据
        affected = self.db.update('test_students',
                                  {'height': 165.0},
                                  'name = %s',
                                  ('要更新的学生',))
        assert affected == 1, "应该更新1行数据"

        # 验证更新
        result = self.db.get_one('test_students', 'name = %s', ('要更新的学生',))
        assert result[2] == 165.0, "身高应该被更新为165.0"

    def test_delete_data(self):
        """测试删除数据"""
        # 先插入一条数据
        self.db.insert('test_students', {'name': '要删除的学生', 'height': 150.0})

        # 删除数据
        affected = self.db.delete('test_students', 'name = %s', ('要删除的学生',))
        assert affected == 1, "应该删除1行数据"

        # 验证删除
        result = self.db.select('test_students', 'name = %s', ('要删除的学生',))
        assert result['count'] == 0, "数据应该被删除"

    def test_get_one(self):
        """测试获取单条数据"""
        test_name = "唯一学生" + str(hash('unique'))
        self.db.insert('test_students', {'name': test_name, 'height': 155.0})

        student = self.db.get_one('test_students', 'name = %s', (test_name,))
        assert student is not None, "应该能获取到学生"
        assert student[1] == test_name, "姓名应该匹配"

    def test_count(self):
        """测试统计功能"""
        # 先记录当前数量
        initial_count = self.db.count('test_students')

        # 插入一些数据
        for i in range(3):
            self.db.insert('test_students', {'name': f'计数学生{i}', 'height': 160 + i})

        # 验证数量增加
        new_count = self.db.count('test_students')
        assert new_count >= initial_count + 3, "数量应该增加至少3个"

    def test_complex_query(self):
        """测试复杂查询"""
        # 测试聚合函数
        result = self.db.get_data("SELECT AVG(height) FROM test_students")
        assert result['data'][0][0] is not None, "应该能计算平均身高"

        # 测试分组查询
        result = self.db.get_data("""
                                  SELECT CASE
                                             WHEN height < 160 THEN '矮'
                                             WHEN height < 175 THEN '中等'
                                             ELSE '高'
                                             END  as 身高类型,
                                         COUNT(*) as 人数
                                  FROM test_students
                                  GROUP BY 身高类型
                                  """)
        assert len(result['data']) > 0, "分组查询应该有结果"

    # ---------- E2E测试（端到端测试） ----------

    def e2e_test(self):
        """端到端测试：完整的业务流程测试"""
        print("\n" + "=" * 60)
        print("开始E2E端到端测试")
        print("=" * 60)

        # 创建一个全新的测试表，避免影响现有数据
        test_table = "e2e_test_students"

        # 1. 创建表
        print("\n1. 创建测试表...")
        self.db.run_sql(f"DROP TABLE IF EXISTS {test_table}")
        create_sql = f"""
        CREATE TABLE {test_table} (
            student_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(50) NOT NULL,
            height DECIMAL(5,2)
        )
        """
        self.db.run_sql(create_sql)

        # 2. 批量插入数据
        print("2. 批量插入测试数据...")
        test_students = [
            {'name': 'E2E学生1', 'height': 165.5},
            {'name': 'E2E学生2', 'height': 172.3},
            {'name': 'E2E学生3', 'height': 180.1},
            {'name': 'E2E学生4', 'height': 158.7}
        ]

        for student in test_students:
            self.db.insert(test_table, student)

        # 3. 查询验证
        print("3. 查询验证...")
        all_students = self.db.select(test_table)
        assert all_students['count'] == 4, "应该有4个学生"

        # 4. 条件查询
        print("4. 条件查询测试...")
        tall_students = self.db.select(test_table, 'height > %s', (170,))
        assert tall_students['count'] == 2, "应该有2个身高>170的学生"

        # 5. 更新操作
        print("5. 更新操作测试...")
        self.db.update(test_table, {'height': 166.0}, 'name = %s', ('E2E学生1',))

        # 验证更新
        updated = self.db.get_one(test_table, 'name = %s', ('E2E学生1',))
        assert updated[2] == 166.0, "身高应该更新为166.0"

        # 6. 删除操作
        print("6. 删除操作测试...")
        self.db.delete(test_table, 'height < %s', (160,))

        remaining = self.db.count(test_table)
        assert remaining == 3, "删除后应该剩下3个学生"

        # 7. 统计功能
        print("7. 统计功能测试...")
        avg_height = self.db.get_data(f"SELECT AVG(height) FROM {test_table}")
        print(f"   平均身高: {avg_height['data'][0][0]:.2f}")

        # 8. 清理测试表
        print("8. 清理测试表...")
        self.db.run_sql(f"DROP TABLE {test_table}")

        print("\n✅ E2E端到端测试完成！")
        print("=" * 60)

    # ---------- 运行所有测试 ----------

    def run_all_tests(self):
        """运行所有测试用例"""
        print("开始运行所有测试用例...")

        # 准备环境
        if not self.setup():
            return

        # 定义要运行的测试用例列表
        test_cases = [
            (self.test_connection, "数据库连接"),
            (self.test_create_table, "创建表"),
            (self.test_insert_data, "插入数据"),
            (self.test_select_data, "查询数据"),
            (self.test_update_data, "更新数据"),
            (self.test_delete_data, "删除数据"),
            (self.test_get_one, "获取单条数据"),
            (self.test_count, "统计功能"),
            (self.test_complex_query, "复杂查询")
        ]

        # 运行每个测试用例
        for test_func, test_name in test_cases:
            self.run_test(test_func, test_name)

        # 运行E2E测试
        self.run_test(self.e2e_test, "E2E端到端测试")

        # 清理环境
        self.cleanup()

    def run_specific_test(self, test_name):
        """运行特定的测试用例"""
        test_map = {
            'connection': self.test_connection,
            'create': self.test_create_table,
            'insert': self.test_insert_data,
            'select': self.test_select_data,
            'update': self.test_update_data,
            'delete': self.test_delete_data,
            'getone': self.test_get_one,
            'count': self.test_count,
            'complex': self.test_complex_query,
            'e2e': self.e2e_test
        }

        if test_name in test_map:
            if not self.setup():
                return
            self.run_test(test_map[test_name], test_name)
            self.cleanup()
        else:
            print(f"未知的测试用例: {test_name}")
            print("可用的测试用例: " + ", ".join(test_map.keys()))


if __name__ == "__main__":
    # 创建测试器实例
    tester = SchoolDBTester()

    print("请选择测试模式：")
    print("1. 运行所有测试")
    print("2. 运行E2E端到端测试")
    print("3. 运行特定测试")
    print("4. 查看可用的测试用例")

    choice = input("请输入数字 (1-4): ")

    if choice == '1':
        tester.run_all_tests()
    elif choice == '2':
        tester.run_test(tester.e2e_test, "E2E端到端测试")
    elif choice == '3':
        print("可用的测试用例：")
        print("  connection - 测试数据库连接")
        print("  create     - 测试创建表")
        print("  insert     - 测试插入数据")
        print("  select     - 测试查询数据")
        print("  update     - 测试更新数据")
        print("  delete     - 测试删除数据")
        print("  getone     - 测试获取单条数据")
        print("  count      - 测试统计功能")
        print("  complex    - 测试复杂查询")
        print("  e2e        - 运行E2E端到端测试")

        test_name = input("请输入测试用例名称: ").strip().lower()
        tester.run_specific_test(test_name)
    elif choice == '4':
        print("\n测试用例说明：")
        print("1. connection: 测试MySQL连接是否正常")
        print("2. create:     测试创建数据库表")
        print("3. insert:     测试插入学生数据")
        print("4. select:     测试查询学生数据")
        print("5. update:     测试更新学生信息")
        print("6. delete:     测试删除学生记录")
        print("7. getone:     测试获取单条记录")
        print("8. count:      测试统计学生数量")
        print("9. complex:    测试复杂SQL查询")
        print("10.e2e:        完整业务流程测试")
    else:
        print("输入错误，请输入1-4之间的数字")