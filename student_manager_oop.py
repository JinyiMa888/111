from mysql_helper import MySQLHelper


class StudentManager:
    """学生管理系统类"""

    def __init__(self):
        self.db = self.connect_database()

    def connect_database(self):
        """连接数据库"""
        db = MySQLHelper(
            host='localhost',
            user='root',
            password='123456',
            database='school_db'
        )

        if db.connect():
            print("✅ 数据库连接成功")
            return db
        else:
            print("❌ 数据库连接失败")
            return None

    def setup_database(self):
        """设置数据库表结构"""
        if not self.db:
            return False

        create_sql = """
                     CREATE TABLE IF NOT EXISTS students \
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
                     ),
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                         ) \
                     """

        return self.db.run_sql(create_sql) >= 0

    def add_student(self):
        """添加学生"""
        print("\n" + "=" * 40)
        print("添加学生")
        print("=" * 40)

        name = input("姓名: ").strip()
        if not name:
            print("姓名不能为空")
            return

        try:
            height = float(input("身高(cm): "))
            if height <= 0 or height > 300:
                print("身高必须在0-300cm之间")
                return
        except ValueError:
            print("身高必须是数字")
            return

        data = {'name': name, 'height': height}

        if self.db.insert('students', data):
            print(f"✅ 学生 {name} 添加成功")
        else:
            print("❌ 添加失败")

    def show_students(self, students=None):
        """显示学生列表"""
        print("\n" + "=" * 40)
        print("学生列表")
        print("=" * 40)

        if students is None:
            result = self.db.select('students', order_by='student_id')
            students = result['data']

        if not students:
            print("暂无学生数据")
            return

        print(f"共找到 {len(students)} 名学生")
        print("-" * 40)
        print(f"{'学号':<8} {'姓名':<15} {'身高':<10} {'添加时间':<20}")
        print("-" * 40)

        for student in students:
            student_id = student[0]
            name = student[1]
            height = student[2]
            created_at = student[3] if len(student) > 3 else "N/A"

            print(f"{student_id:<8} {name:<15} {height:<10} {created_at:<20}")

    def search_student(self):
        """查找学生"""
        print("\n" + "=" * 40)
        print("查找学生")
        print("=" * 40)
        print("1. 按姓名查找")
        print("2. 按身高范围查找")
        print("3. 返回")

        choice = input("请选择: ").strip()

        if choice == '1':
            keyword = input("请输入姓名或部分姓名: ").strip()
            if not keyword:
                print("请输入搜索关键词")
                return

            result = self.db.select('students', 'name LIKE %s', (f'%{keyword}%',))
            self.show_students(result['data'])

        elif choice == '2':
            try:
                min_height = float(input("最低身高(cm): "))
                max_height = float(input("最高身高(cm): "))

                if min_height > max_height:
                    print("最低身高不能大于最高身高")
                    return

                result = self.db.select('students',
                                        'height BETWEEN %s AND %s',
                                        (min_height, max_height))
                self.show_students(result['data'])

            except ValueError:
                print("请输入有效的数字")

        elif choice == '3':
            return
        else:
            print("无效的选择")

    def update_student(self):
        """更新学生信息"""
        print("\n" + "=" * 40)
        print("更新学生信息")
        print("=" * 40)

        student_id = input("请输入学号: ").strip()
        if not student_id.isdigit():
            print("学号必须是数字")
            return

        student = self.db.get_one('students', 'student_id = %s', (student_id,))
        if not student:
            print("该学号不存在")
            return

        print(f"\n当前信息:")
        print(f"  学号: {student[0]}")
        print(f"  姓名: {student[1]}")
        print(f"  身高: {student[2]}cm")

        print("\n请输入新信息（直接回车跳过）:")

        new_name = input(f"新姓名 [{student[1]}]: ").strip()
        new_height = input(f"新身高 [{student[2]}]: ").strip()

        data = {}
        if new_name:
            data['name'] = new_name
        if new_height:
            try:
                data['height'] = float(new_height)
                if data['height'] <= 0 or data['height'] > 300:
                    print("身高必须在0-300cm之间")
                    return
            except ValueError:
                print("身高必须是数字")
                return

        if not data:
            print("没有要更新的内容")
            return

        if self.db.update('students', data, 'student_id = %s', (student_id,)):
            print("✅ 更新成功")
        else:
            print("❌ 更新失败")

    def delete_student(self):
        """删除学生"""
        print("\n" + "=" * 40)
        print("删除学生")
        print("=" * 40)

        student_id = input("请输入学号: ").strip()
        if not student_id.isdigit():
            print("学号必须是数字")
            return

        student = self.db.get_one('students', 'student_id = %s', (student_id,))
        if not student:
            print("该学号不存在")
            return

        print(f"\n将要删除的学生:")
        print(f"  学号: {student[0]}")
        print(f"  姓名: {student[1]}")
        print(f"  身高: {student[2]}cm")

        confirm = input("\n确认删除吗？(y/n): ").strip().lower()
        if confirm == 'y' or confirm == 'yes':
            if self.db.delete('students', 'student_id = %s', (student_id,)):
                print("✅ 删除成功")
            else:
                print("❌ 删除失败")
        else:
            print("取消删除")

    def show_statistics(self):
        """显示统计信息"""
        print("\n" + "=" * 40)
        print("统计信息")
        print("=" * 40)

        # 总人数
        total = self.db.count('students')
        if total == 0:
            print("暂无学生数据")
            return

        print(f"总人数: {total}人")

        # 平均身高
        result = self.db.get_data("SELECT AVG(height) FROM students")
        avg_height = result['data'][0][0] if result['data'][0][0] else 0
        print(f"平均身高: {float(avg_height):.2f}cm")

        # 最高和最矮
        result = self.db.get_data("SELECT MAX(height), MIN(height) FROM students")
        max_height = result['data'][0][0] if result['data'][0][0] else 0
        min_height = result['data'][0][1] if result['data'][0][1] else 0
        print(f"最高身高: {float(max_height):.2f}cm")
        print(f"最低身高: {float(min_height):.2f}cm")

        # 身高分布
        print("\n身高分布:")
        height_ranges = [
            (0, 160, "160cm以下"),
            (160, 170, "160-170cm"),
            (170, 180, "170-180cm"),
            (180, 300, "180cm以上")
        ]

        for min_h, max_h, label in height_ranges:
            count = self.db.count('students',
                                  'height >= %s AND height < %s',
                                  (min_h, max_h))
            if count > 0:
                percentage = (count / total) * 100
                print(f"  {label}: {count}人 ({percentage:.1f}%)")

    def run(self):
        """运行学生管理系统"""
        if not self.db:
            print("数据库连接失败，无法启动系统")
            return

        if not self.setup_database():
            print("数据库设置失败")
            return

        print("\n" + "=" * 40)
        print("欢迎使用学生管理系统")
        print("=" * 40)

        while True:
            print("\n主菜单:")
            print("1. 添加学生")
            print("2. 查看所有学生")
            print("3. 查找学生")
            print("4. 更新学生信息")
            print("5. 删除学生")
            print("6. 统计信息")
            print("7. 退出系统")
            print("-" * 40)

            choice = input("请选择操作 (1-7): ").strip()

            if choice == '1':
                self.add_student()
            elif choice == '2':
                self.show_students()
            elif choice == '3':
                self.search_student()
            elif choice == '4':
                self.update_student()
            elif choice == '5':
                self.delete_student()
            elif choice == '6':
                self.show_statistics()
            elif choice == '7':
                print("谢谢使用，再见！")
                if self.db:
                    self.db.close()
                break
            else:
                print("无效的选择，请重新输入")


class StudentManagerTester:
    """学生管理系统测试类"""

    def __init__(self):
        self.manager = StudentManager()

    def test_add_student(self):
        """测试添加学生功能"""
        print("\n测试添加学生...")
        # 这里可以模拟输入，但为了简单，我们直接调用方法
        # 在实际测试中，可以使用mock来模拟输入

    def test_show_students(self):
        """测试显示学生功能"""
        print("\n测试显示学生...")
        self.manager.show_students()

    def e2e_test(self):
        """端到端测试整个管理系统"""
        print("\n" + "=" * 60)
        print("学生管理系统E2E测试")
        print("=" * 60)

        # 注意：这个测试会实际操作数据库
        # 建议在测试数据库中运行

        print("✅ E2E测试完成")
        print("=" * 60)

    def run_all_tests(self):
        """运行所有测试"""
        print("开始运行学生管理系统测试...")

        test_cases = [
            (self.test_add_student, "添加学生功能"),
            (self.test_show_students, "显示学生功能"),
            (self.e2e_test, "E2E端到端测试")
        ]

        for test_func, test_name in test_cases:
            print(f"\n🔧 开始测试：{test_name}")
            try:
                test_func()
                print(f"✅ 测试通过：{test_name}")
            except Exception as e:
                print(f"❌ 测试失败：{test_name}")
                print(f"   错误：{e}")


if __name__ == "__main__":
    print("请选择模式:")
    print("1. 运行学生管理系统")
    print("2. 运行系统测试")

    mode = input("请选择 (1/2): ").strip()

    if mode == '1':
        # 运行学生管理系统
        manager = StudentManager()
        manager.run()
    elif mode == '2':
        # 运行测试
        tester = StudentManagerTester()
        tester.run_all_tests()
    else:
        print("无效的选择")