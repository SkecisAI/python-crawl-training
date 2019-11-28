import re
import json
import time
import jieba
import requests
import numpy as np
from PIL import Image
from urllib.parse import quote
from wordcloud import WordCloud
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt


class DoubanCrawl:
    def __init__(self, info_type):
        self.info_type = info_type
        self.headers = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
                'Host': 'movie.douban.com'
            },  # movie's headers
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
                'Host': 'book.douban.com'
            }  # book's headers
        ]
        self.movie_search_url = "https://movie.douban.com/j/subject_suggest?q="
        self.book_search_url = "https://book.douban.com/j/subject_suggest?q="
        self.movie_url = "https://movie.douban.com/subject/%s/"
        self.book_url = "https://book.douban.com/subject/%s/"
        self.movie_comment_url = "https://movie.douban.com/subject/%s/comments?start=%d&limit=20&sort=new_score&status=P"
        self.book_comment_url = "https://book.douban.com/subject/%s/comments/hot?p=%d"

    def info_crawl(self, name, bg_image=None):
        name_str = self.__handle_name(name)  # 获取url的gbk编码
        text_list = []
        if self.info_type == "movie":
            print("-----爬取电影短评-----")
            self.movie_search_url += name_str
            self.movie_url, num_str = self.__find_url(self.movie_search_url, 0)
            for i in range(0, 15):
                url = self.movie_comment_url % (num_str, i*20)
                time.sleep(np.random.randint(1, 3))  # 间隔1~3秒
                print("正在获取第%d个页面" % i)
                r = requests.get(url, headers=self.headers[0])
                soup = BeautifulSoup(r.content, 'lxml')
                comment_list = soup.find_all('span', class_='short')
                for ct in comment_list:
                    text_list.append(ct.text)
            self.__comment_to_txt(name, text_list)
            self.__plot_wordcloud(name, bg_image)
        else:
            print("-----爬取书籍短评-----")
            self.book_search_url += name_str
            self.book_url, num_str = self.__find_url(self.book_search_url, 1)
            for i in range(1, 20):
                url = self.book_comment_url % (num_str, i)
                time.sleep(np.random.randint(1, 3))  # 间隔1~3秒
                print("正在获取第%d个页面" % i)
                r = requests.get(url, headers=self.headers[1])
                soup = BeautifulSoup(r.content, 'lxml')
                comment_list = soup.find_all('span', class_='short')
                for ct in comment_list:
                    text_list.append(ct.text)
            self.__comment_to_txt(name, text_list)
            self.__plot_wordcloud(name, bg_image)

    def __plot_wordcloud(self, name, bg_image=None):
        file_name = str(name) + '.txt'
        f = open(file_name, 'r', encoding='utf-8').read()
        cut_text = " ".join(jieba.cut(f))
        print("正在生成词云...")
        word_cloud = WordCloud(
            scale=10,
            font_path='C:/Windows/Fonts/simfang.ttf',
            background_color="white", width=1000, height=1000
        ).generate(cut_text)
        plt.imshow(word_cloud, interpolation='bilinear')
        plt.axis('off')
        plt.show()

    def __comment_to_txt(self, name, clist):
        file_name = str(name) + '.txt'
        with open(file_name, 'a+', encoding='utf-8') as f:
            for c in clist:
                f.write(c)
            f.close()

    def __handle_name(self, name):
        return str(quote(name))

    def __find_url(self, url, tp):
        r = requests.get(url, headers=self.headers[tp])
        json_data = json.loads(r.text)
        address_num = re.search('[0-9]+', json_data[0]['url'])
        if tp == 0:
            return self.movie_url % address_num, address_num.group(0)  # 获取电影地址
        else:
            return self.book_url % address_num, address_num.group(0)  # 获取书籍地址


if __name__ == '__main__':
    my_crawl = DoubanCrawl("movie")
    my_crawl.info_crawl('小丑')