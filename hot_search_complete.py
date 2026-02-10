"""
百度热搜爬虫 - 最终版
使用百度热搜JSON API接口
"""

import requests
import json
import pymysql
from datetime import datetime


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
            print("数据库连接成功")
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("数据库连接已关闭")

    def execute(self, sql, params=None):
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            self.conn.commit()
            return self.cursor.rowcount
        except Exception as e:
            print(f"SQL执行失败: {e}")
            self.conn.rollback()
            return 0


class BaiduHotSearchCrawler:
    def __init__(self):
        # 百度热搜API接口
        self.api_url = "https://top.baidu.com/api/board"

        # 请求头设置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://top.baidu.com/board',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }

        self.hot_list = []  # 存储热搜数据

    def get_hot_search_data(self):
        """从API获取热搜数据"""
        print("正在获取百度热搜数据...")

        params = {'tab': 'realtime'}

        try:
            response = requests.get(self.api_url, headers=self.headers, params=params, timeout=10)

            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                return None

            return response.json()

        except Exception as e:
            print(f"获取数据失败: {e}")
            return None

    def parse_hot_data(self, data):
        """解析API返回的热搜数据"""
        print("解析热搜数据...")

        self.hot_list = []

        try:
            if data and 'data' in data:
                cards = data['data'].get('cards', [])

                if cards:
                    first_card = cards[0]
                    hot_items = first_card.get('content', [])

                    for i, item in enumerate(hot_items[:10], 1):
                        title = item.get('query', '') or item.get('word', '') or item.get('title', '')

                        if title:
                            hot_score = item.get('hotScore', 0) or item.get('score', 0)
                            desc = item.get('desc', '')

                            self.hot_list.append({
                                'rank': i,
                                'title': title,
                                'hot_value': int(hot_score) if hot_score else 0,
                                'description': desc,
                                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })

                    print(f"成功解析 {len(self.hot_list)} 条热搜数据")
                    return True

        except Exception as e:
            print(f"解析数据时出错: {e}")

        return False

    def show_results(self):
        """显示热搜结果"""
        if not self.hot_list:
            print("没有找到热搜数据")
            return

        print("\n" + "=" * 60)
        print("百度热搜 TOP 10")
        print("=" * 60)

        for item in self.hot_list:
            print(f"第{item['rank']:2d}名: {item['title']}")
            if item['hot_value'] > 0:
                print(f"热度: {item['hot_value']:,}")
            if item['description']:
                print(f"描述: {item['description']}")
            print("-" * 50)

    def save_to_database(self):
        """保存数据到数据库"""
        if not self.hot_list:
            print("没有数据可保存")
            return False

        print("\n正在保存数据到数据库...")

        # 数据库连接信息 - 请修改为你的实际信息
        db = MySQLHelper(
            host='localhost',
            user='root',
            password='123456',  # 修改为你的MySQL密码
            database='hot_search_db'
        )

        if not db.connect():
            if self.create_database():
                db = MySQLHelper(
                    host='localhost',
                    user='root',
                    password='123456',
                    database='hot_search_db'
                )
                if not db.connect():
                    return False
            else:
                return False

        # 创建表
        create_table_sql = """
                           CREATE TABLE IF NOT EXISTS baidu_hot_search \
                           ( \
                               id \
                               INT \
                               AUTO_INCREMENT \
                               PRIMARY \
                               KEY, \
                               `rank` \
                               INT \
                               NOT \
                               NULL, \
                               title \
                               VARCHAR \
                           ( \
                               200 \
                           ) NOT NULL,
                               hot_value INT DEFAULT 0,
                               description TEXT,
                               crawl_time DATETIME NOT NULL,
                               create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                               ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci \
                           """
        db.execute(create_table_sql)

        # 插入数据
        success_count = 0
        for item in self.hot_list:
            insert_sql = """
                         INSERT INTO baidu_hot_search (`rank`, title, hot_value, description, crawl_time)
                         VALUES (%s, %s, %s, %s, %s) \
                         """

            affected = db.execute(insert_sql, (
                item['rank'],
                item['title'],
                item['hot_value'],
                item['description'],
                item['crawl_time']
            ))

            if affected > 0:
                success_count += 1

        db.close()

        print(f"成功保存 {success_count}/{len(self.hot_list)} 条数据到数据库")
        return success_count > 0

    def create_database(self):
        """创建数据库"""
        print("创建数据库...")

        try:
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='123456'
            )
            cursor = conn.cursor()

            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS hot_search_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("数据库 hot_search_db 创建成功")

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            print(f"创建数据库失败: {e}")
            return False

    def run(self):
        """运行爬虫"""
        print("百度热搜爬虫 - 开始执行")
        print("=" * 50)

        # 获取数据
        data = self.get_hot_search_data()

        if data:
            if self.parse_hot_data(data):
                self.show_results()

                # 保存到数据库
                save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
                if save_choice == 'y':
                    if self.save_to_database():
                        print("\n任务完成！数据已成功保存到数据库")
                        print(f"共爬取 {len(self.hot_list)} 条热搜")
                    else:
                        print("\n数据保存失败")
                else:
                    print("\n数据未保存到数据库")
            else:
                print("解析热搜数据失败")
        else:
            print("获取热搜数据失败")

        print("=" * 50)


def check_dependencies():
    """检查依赖库"""
    try:
        import requests
        import pymysql
        print("依赖库检查通过")
        return True
    except ImportError as e:
        print(f"缺少依赖库: {e}")
        print("请运行: pip install requests pymysql")
        return False


def main():
    print("百度热搜爬虫系统")
    print("版本: 最终版")
    print("=" * 50)

    if not check_dependencies():
        return

    crawler = BaiduHotSearchCrawler()
    crawler.run()


if __name__ == "__main__":
    main()