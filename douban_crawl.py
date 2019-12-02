import re
import json
import time
import jieba
import requests
import numpy as np
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
        self.movie_url = "https://movie.douban.com/subject/%s/"
        self.movie_comment_url = "https://movie.douban.com/subject/%s/comments?start=%d&limit=20&sort=new_score&status=P"

        self.book_search_url = "https://book.douban.com/j/subject_suggest?q="
        self.book_url = "https://book.douban.com/subject/%s/"
        self.book_comment_url = "https://book.douban.com/subject/%s/comments/hot?p=%d"

    def info_crawl(self, name, bg_image=None):
        name_str = self.__handle_name(name)  # 获取url的gbk编码
        text_list = []
        if self.info_type == "movie":
            print(">>>> 爬取电影短评中 >>>>")
            self.movie_search_url += name_str
            self.movie_url, num_str = self.__find_url(self.movie_search_url, 0)
            if not num_str:
                return
            for i in range(0, 15):
                url = self.movie_comment_url % (num_str, i*20)
                time.sleep(np.random.randint(1, 3))  # 间隔1~3秒
                print("正在获取第%d个页面" % (i+1), "剩余：%d" % (15-i-1))
                r = requests.get(url, headers=self.headers[0])
                soup = BeautifulSoup(r.content, 'lxml')
                comment_list = soup.find_all('span', class_='short')
                for ct in comment_list:
                    text_list.append(ct.text)
            self.__comment_to_txt(name, text_list)  # 存储评论文字
            self.__plot_wordcloud(name, bg_image)  # 绘制词云
        else:
            print(">>>> 爬取书籍短评中 >>>>")
            self.book_search_url += name_str
            self.book_url, num_str = self.__find_url(self.book_search_url, 1)
            for i in range(1, 20):
                url = self.book_comment_url % (num_str, i)
                time.sleep(np.random.randint(1, 3))  # 间隔1~3秒
                print("正在获取第%d个页面" % (i+1), "剩余：%d" % (20-i-1))
                r = requests.get(url, headers=self.headers[1])
                soup = BeautifulSoup(r.content, 'lxml')
                comment_list = soup.find_all('span', class_='short')
                for ct in comment_list:
                    text_list.append(ct.text)
            self.__comment_to_txt(name, text_list)
            self.__plot_wordcloud(name, bg_image)

    def __plot_wordcloud(self, name, bg_image=None):
        """
        绘制词云
        :param name:
        :param bg_image:
        :return:
        """
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
        """
        编码中文关键字
        :param name:
        :return:
        """
        return str(quote(name))

    def __find_url(self, url, tp):
        """
        获取真实主页地址和编号id
        :param url:
        :param tp:
        :return:
        """
        r = requests.get(url, headers=self.headers[tp])
        json_data = json.loads(r.text)
        if not json_data:
            print('爬取内容不存在！ 退出··· ···')
            return None, None
        address_num = re.search('[0-9]+', json_data[0]['url'])
        if tp == 0:
            return self.movie_url % address_num, address_num.group(0)  # 获取电影地址
        else:
            return self.book_url % address_num, address_num.group(0)  # 获取书籍地址


if __name__ == '__main__':
    print('·····豆瓣短评爬虫 v1.0·····')
    user_type = input("输入类型（1-电影，2-书籍）：")
    search_name = input("名字：")
    type_dict = {'1': 'movie', '2': 'book'}
    my_crawl = DoubanCrawl(type_dict[user_type])
    my_crawl.info_crawl(search_name)