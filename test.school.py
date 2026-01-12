from mysql_helper import MySQLHelper


def test_school_system():
    print("=" * 60)
    print("学校学生管理系统测试")
    print("=" * 60)

    db = MySQLHelper(
        host='localhost',
        user='root',
        password='123456',
        database='school_db'
    )

    if not db.connect():
        print("连接失败")
        return

    print("\n初始学生数据...")
    result = db.select('students')
    show_students(result)

    print("\n插入新学生...")
    new_students = [
        {'name': '诸葛亮', 'height': 178.5},
        {'name': '赵云', 'height': 185.2},
        {'name': '小乔', 'height': 162.8}
    ]

    for student in new_students:
        db.insert('students', student)
        print(f"添加：{student['name']} - {student['height']}cm")

    print("\n查询所有学生...")
    result = db.select('students')
    show_students(result)

    print("\n条件查询：身高>170cm的学生...")
    tall_students = db.select('students', 'height > %s', (170,))
    if tall_students['count'] > 0:
        print("身高超过170cm的学生：")
        for row in tall_students['data']:
            print(f"{row[1]} - {row[2]}cm")

    print("\n查询指定列（学号和姓名）...")
    sql = "SELECT student_id, name FROM students"
    result = db.get_data(sql)
    print("学号 姓名")
    for row in result['data']:
        print(f"{row[0]} {row[1]}")

    print("\n排序查询：按身高降序...")
    sql = "SELECT * FROM students ORDER BY height DESC"
    result = db.get_data(sql)
    print("身高排名：")
    for i, row in enumerate(result['data'], 1):
        print(f"第{i}名: {row[1]} - {row[2]}cm")

    print("\n模糊查询：姓张的学生...")
    zhang_students = db.select('students', 'name LIKE %s', ('张%',))
    if zhang_students['count'] > 0:
        print("姓张的学生：")
        for row in zhang_students['data']:
            print(f"{row[1]} - {row[2]}cm")

    print("\n更新数据：张翼德身高改为176.0cm...")
    affected = db.update('students', {'height': 176.0}, 'name = %s', ('张翼德',))
    print(f"更新了{affected}条记录")

    zhang = db.get_one('students', 'name = %s', ('张翼德',))
    if zhang:
        print(f"张翼德新身高：{zhang[2]}cm")

    print("\n删除数据：删除露娜...")
    affected = db.delete('students', 'name = %s', ('露娜',))
    print(f"删除了{affected}条记录")

    print("\n最终学生列表...")
    result = db.select('students')
    show_students(result)

    print("\n统计信息...")
    total = db.count('students')
    avg_result = db.get_data("SELECT AVG(height) as avg_height FROM students")
    max_result = db.get_data("SELECT MAX(height) as max_height FROM students")
    min_result = db.get_data("SELECT MIN(height) as min_height FROM students")

    if total > 0:
        avg_height = avg_result['data'][0][0] if avg_result['data'][0][0] else 0
        max_height = max_result['data'][0][0] if max_result['data'][0][0] else 0
        min_height = min_result['data'][0][0] if min_result['data'][0][0] else 0

        print(f"总人数：{total}人")
        print(f"平均身高：{float(avg_height):.2f}cm")
        print(f"最高身高：{float(max_height):.2f}cm")
        print(f"最低身高：{float(min_height):.2f}cm")

    print("\n分身高段统计...")
    height_groups = db.get_data("""
                                SELECT CASE
                                           WHEN height < 160 THEN '160cm以下'
                                           WHEN height BETWEEN 160 AND 170 THEN '160-170cm'
                                           WHEN height BETWEEN 170 AND 180 THEN '170-180cm'
                                           ELSE '180cm以上'
                                           END AS height_group,
                                       COUNT(*) as count
                                FROM students
                                GROUP BY height_group
                                ORDER BY height_group
                                """)

    if height_groups['data']:
        print("身高分布：")
        for row in height_groups['data']:
            print(f"{row[0]}: {row[1]}人")

    print("\n关闭数据库连接...")
    db.close()

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


def show_students(result):
    if result['count'] == 0:
        print("暂无学生数据")
        return

    print(f"共 {result['count']} 名学生：")
    for row in result['data']:
        print(f"学号:{row[0]} 姓名:{row[1]} 身高:{row[2]}cm")


def check_database():
    print("检查数据库状态...")

    db = MySQLHelper(
        host='localhost',
        user='root',
        password='123456'
    )

    try:
        import pymysql
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            charset='utf8mb4'
        )

        cursor = conn.cursor()

        cursor.execute("SHOW DATABASES LIKE 'school_db'")
        if cursor.fetchone():
            print("数据库 school_db 存在")

            cursor.execute("USE school_db")

            cursor.execute("SHOW TABLES LIKE 'students'")
            if cursor.fetchone():
                print("表 students 存在")

                cursor.execute("DESC students")
                columns = cursor.fetchall()
                print("表结构：")
                for col in columns:
                    print(f"{col[0]} {col[1]}")
            else:
                print("表 students 不存在")
        else:
            print("数据库 school_db 不存在")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"连接失败：{e}")


def create_database_and_table():
    print("创建数据库和表...")

    db = MySQLHelper(
        host='localhost',
        user='root',
        password='123456'
    )

    try:
        import pymysql
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            charset='utf8mb4'
        )

        cursor = conn.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS school_db")
        print("数据库 school_db 创建成功")

        cursor.execute("USE school_db")

        create_table_sql = """
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
                           )
                               ) \
                           """
        cursor.execute(create_table_sql)
        print("表 students 创建成功")

        cursor.execute("TRUNCATE TABLE students")

        insert_sql = """
                     INSERT INTO students (name, height) \
                     VALUES ('张翼德', 175.5), \
                            ('宇智波佐助', 168.2), \
                            ('李白', 180.0), \
                            ('露娜', 172.8), \
                            ('理查德', 165.3) \
                     """
        cursor.execute(insert_sql)
        conn.commit()

        print("初始数据插入成功")
        print("数据库准备完成")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"创建失败：{e}")


if __name__ == "__main__":
    print("请选择操作：")
    print("1. 检查数据库状态")
    print("2. 创建数据库和表（如果不存在）")
    print("3. 运行完整测试")

    choice = input("请输入数字 (1/2/3): ")

    if choice == '1':
        check_database()
    elif choice == '2':
        create_database_and_table()
    elif choice == '3':
        test_school_system()
    else:
        print("输入错误")