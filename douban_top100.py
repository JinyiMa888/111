"""
豆瓣电影Top100爬虫 - 存储到MySQL
设计字段用于可视化
"""

import requests
from bs4 import BeautifulSoup
import pymysql
import time
import re
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

    def insert_one(self, table, data):

        columns = ', '.join([f'`{k}`' for k in data.keys()])
        placeholders = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return self.execute(sql, tuple(data.values()))


class DoubanTop100Crawler:
    def __init__(self):
        self.base_url = "https://movie.douban.com/top250"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.movies = []

    def get_page(self, start):
        url = f"{self.base_url}?start={start}&filter="
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                return None
            return response.text
        except Exception as e:
            print(f"请求异常: {e}")
            return None

    def parse_page(self, html, base_rank):
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('.item')

        for idx, item in enumerate(items):
            rank = base_rank + idx + 1

            title_tag = item.select_one('.title')
            title = title_tag.text.strip() if title_tag else ''

            info_tag = item.select_one('.bd p')
            info = info_tag.text.strip() if info_tag else ''
            lines = info.split('\n')
            director_actor = lines[0].strip() if len(lines) > 0 else ''
            year_country_genre = lines[1].strip() if len(lines) > 1 else ''

            director = ''
            if '导演:' in director_actor:
                director_part = director_actor.split('导演:')[1].split('主演:')[0].strip() if '主演:' in director_actor else director_actor.split('导演:')[1].strip()
                director = director_part.replace('\xa0', ' ')

            actors = ''
            if '主演:' in director_actor:
                actors_part = director_actor.split('主演:')[1].strip()
                actors = actors_part.replace('\xa0', ' ')

            year = None
            country = ''
            genre = ''
            if year_country_genre:
                parts = year_country_genre.split('/')
                if len(parts) >= 3:
                    year_str = parts[0].strip()
                    year_match = re.search(r'\d{4}', year_str)
                    if year_match:
                        year = int(year_match.group())
                    country = parts[1].strip()
                    genre = parts[2].strip()

            rating_tag = item.select_one('.rating_num')
            rating = rating_tag.text.strip() if rating_tag else '0'
            try:
                rating = float(rating)
            except:
                rating = 0.0

            star_spans = item.select('.star span')
            votes = 0
            if len(star_spans) >= 3:
                votes_text = star_spans[2].text
                votes_text = votes_text.replace('人评价', '').strip()
                try:
                    votes = int(votes_text)
                except:
                    votes = 0
            else:
                star_div = item.select_one('.star')
                if star_div:
                    all_text = star_div.get_text()
                    match = re.search(r'(\d+)人评价', all_text)
                    if match:
                        votes = int(match.group(1))

            quote_tag = item.select_one('.inq')
            quote = quote_tag.text.strip() if quote_tag else ''

            movie = {
                'rank': rank,
                'title': title,
                'year': year,
                'country': country,
                'genre': genre,
                'director': director,
                'actors': actors,
                'rating': rating,
                'votes': votes,
                'quote': quote,
                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.movies.append(movie)
            print(f"已抓取: {rank}. {title}")

        time.sleep(2)

    def crawl_top100(self):
        for page in range(4):
            start = page * 25
            print(f"\n正在抓取第{page+1}页，起始索引{start}")
            html = self.get_page(start)
            if html:
                self.parse_page(html, start)
            else:
                print(f"第{page+1}页抓取失败")
                break
        print(f"\n抓取完成，共 {len(self.movies)} 部电影")

    def save_to_database(self):
        if not self.movies:
            print("没有数据可保存")
            return False

        db = MySQLHelper(
            host='localhost',
            user='root',
            password='123456',
            database='movie_db'
        )

        if not db.connect():
            if self.create_database():
                db = MySQLHelper(
                    host='localhost',
                    user='root',
                    password='123456',
                    database='movie_db'
                )
                if not db.connect():
                    return False
            else:
                return False

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS douban_top100 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            `rank` INT NOT NULL,
            title VARCHAR(200) NOT NULL,
            year INT,
            country VARCHAR(100),
            genre VARCHAR(200),
            director VARCHAR(200),
            actors TEXT,
            rating FLOAT,
            votes INT,
            quote TEXT,
            crawl_time DATETIME,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        db.execute(create_table_sql)

        success = 0
        for movie in self.movies:
            data = {k: v for k, v in movie.items()}
            affected = db.insert_one('douban_top100', data)
            if affected > 0:
                success += 1

        db.close()
        print(f"成功保存 {success}/{len(self.movies)} 条记录")
        return success > 0

    def create_database(self):
        try:
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='123456'
            )
            cursor = conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS movie_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("数据库 movie_db 创建成功")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"创建数据库失败: {e}")
            return False


def main():
    print("豆瓣电影Top100爬虫")
    print("=" * 50)
    crawler = DoubanTop100Crawler()
    crawler.crawl_top100()
    if crawler.movies:
        save_choice = input("\n是否保存到数据库? (y/n): ").strip().lower()
        if save_choice == 'y':
            if crawler.save_to_database():
                print("\n任务完成！")
            else:
                print("\n保存失败")
        else:
            print("数据未保存")
    else:
        print("没有抓到数据")
    print("=" * 50)


if __name__ == "__main__":
    main()