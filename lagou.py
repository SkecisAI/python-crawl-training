import re
import time
import json
import jieba
import requests
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib as mpl
from urllib.parse import quote
from bs4 import BeautifulSoup
from wordcloud import WordCloud
from matplotlib import pyplot as plt

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 10)
mpl.rcParams['font.sans-serif'] = ['SimHei']


class JobSearch:
    def __init__(self, kd):
        self.key_word = kd
        self.__job_count = 0
        self.get_url = "https://www.lagou.com/jobs/list_%s?labelWords=sug&fromSearch=true&suginput=%s" % \
                       (str(quote(kd)), str(quote(kd)))
        self.get_headers = {
            'Host': 'www.lagou.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        }
        self.post_rul = "https://www.lagou.com/jobs/positionAjax.json?needAddtionalResult=false"
        self.post_headers = {
            'Host': 'www.lagou.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'Referer': self.get_url  # 这个参数决定了post是否成功
        }
        self.detail_url = "https://www.lagou.com/jobs/%s.html?show=%s"  # 职位信息页面
        self.detail_headers = self.post_headers

    def job_info_crawl(self):
        s = requests.Session()
        r = s.get(self.get_url, headers=self.get_headers)
        soup = BeautifulSoup(r.content, "lxml")
        page_nums = int(soup.find('span', attrs={'class': 'span totalNum'}).text)
        position_df = pd.DataFrame()
        for i in range(1, page_nums):  # 爬取25页职位信息
            print("-----正在爬取第%d页-----" % i)
            post_data = {
                'first': 'true',
                'pn': i,
                'kd': self.key_word
            }
            # if (i % 10) == 0:
            print('<--新会话-->')
            time.sleep(np.random.randint(0, 1))  # 间隔0-1s
            s = requests.Session()
            s.get(self.get_url, headers=self.get_headers)
            p = s.post(self.post_rul, data=post_data, headers=self.post_headers)
            p_json = json.loads(p.content)
            show_id = p_json['content']['showId']  # 具体信息页面id-1
            job_info = p_json['content']['positionResult']['result']  # 职位简要信息
            rp, rq = [], []
            for j in range(15):
                if (i == 1) and (j == 0):
                    position_df = pd.DataFrame(columns=job_info[j].keys())
                position_df.loc[position_df.shape[0]] = job_info[j]
                position_id = job_info[j]['positionId']  # 具体信息页面Id-2
                detail_url = self.detail_url % (position_id, show_id)
                time.sleep(np.random.randint(0, 1))  # 间隔0~1s
                print("第%d个职位" % (j+1))
                r = s.get(detail_url, headers=self.detail_headers)
                text_tuple = self.__job_detail_crawl(r)
                rp.extend(text_tuple[0])
                rq.extend(text_tuple[1])
            self.__save_to_txt(rp, rq)  # 存储工作要求详情, 读写一页
        self.__save_to_csv(position_df)  # 存储工作信息
        print("一共爬取了%d条岗位信息" % self.__job_count)

    def generate_wordcloud(self):
        """
        绘制词云
        """
        f_rp = open(self.key_word + '_responsibility.txt', 'r', encoding='utf-8').read()
        f_rq = open(self.key_word + '_requirement.txt', 'r', encoding='utf-8').read()
        cut_text_rp = " ".join(jieba.cut(f_rp))
        cut_text_rq = " ".join(jieba.cut(f_rq))
        cut_text_rq = re.sub(r'\+\+', 'pp', cut_text_rq)
        print("正在生成词云...")
        word_cloud_rp = WordCloud(
            scale=5,
            font_path='C:/Windows/Fonts/simfang.ttf',
            background_color="white", width=1000, height=1000
        ).generate(cut_text_rp)
        word_cloud_rq = WordCloud(
            scale=5,
            font_path='C:/Windows/Fonts/simfang.ttf',
            background_color="white", width=1000, height=1000
        ).generate(cut_text_rq)

        plt.subplot(121)
        plt.imshow(word_cloud_rp, interpolation='bilinear')
        plt.title(self.key_word + "工作职责")
        plt.axis('off')

        plt.subplot(122)
        plt.imshow(word_cloud_rq, interpolation='bilinear')
        plt.title(self.key_word + "岗位需求")
        plt.axis('off')

        plt.show()

    def __job_detail_crawl(self, r):
        soup = BeautifulSoup(r.content, 'lxml')
        # job_detail = None
        try:
            job_detail = soup.find('div', attrs={'class': 'job-detail'}).find_all('p')
        except AttributeError:
            print('警告！发生重定向。')
            return [], []
        self.__job_count += 1
        info_id = 0
        respon_list, reques_list = [], []
        for d in job_detail:
            txt = d.text
            if len(txt) == 5:
                info_id += 1
                continue
            else:
                if info_id == 1:
                    respon_list.append(txt)
                else:
                    reques_list.append(txt)
        return respon_list, reques_list  # 工作职责信息， 任职要求信息

    def __save_to_txt(self, rp, rq):
        # 创建文件，若存在则清空内容
        with open(self.key_word + '_responsibility.txt', 'w', encoding='utf-8', ) as f:
            f.close()
        with open(self.key_word + '_requirement.txt', 'w', encoding='utf-8') as f:
            f.close()

        with open(self.key_word + '_responsibility.txt', 'a+', encoding='utf-8', ) as f:  # 存储工作职责
            for p in rp:
                f.write(p)
            f.close()
        with open(self.key_word + '_requirement.txt', 'a+', encoding='utf-8') as f:  # 存储任职要求
            for q in rq:
                f.write(q)
            f.close()

    def __save_to_csv(self, df):
        df.to_csv(self.key_word + "_job_info.csv", encoding='gb18030', index=False)

    def handle_data(self):
        position_df = pd.read_csv(self.key_word + '_job_info.csv', encoding='gb18030')
        unused_col = ['explain', 'plus', 'gradeDescription', 'promotionScoreExplain']
        position_df.drop(columns=unused_col, inplace=True)
        unimportant_col = ['businessZones', 'subwayline', 'stationname', 'linestaion',
                           'positionId', 'companyId', 'companyFullName', 'companyLogo', 'createTime', 'formatCreateTime', 'district',
                           'lastLogin', 'publisherId', 'industryLables']
        position_df.drop(columns=unimportant_col, inplace=True)

        position_df['welfare'] = position_df.apply(lambda x: x['companyLabelList'] + x['positionAdvantage'], axis=1)
        position_df['label'] = position_df.apply(lambda x: x['skillLables'] + x['positionLables'], axis=1)
        position_df['salary'] = position_df['salary'].map(lambda x: re.compile('([0-9]+)k').findall(x))
        position_df['salary_min'] = position_df.apply(lambda x: x['salary'][0], axis=1).astype('int64')
        position_df['salary_max'] = position_df.apply(lambda x: x['salary'][-1], axis=1).astype('int64')
        position_df['salary_ave'] = position_df.apply(lambda x: (x['salary_min'] + x['salary_max']) / 2, axis=1)
        position_df.drop(columns=['companyLabelList', 'positionAdvantage', 'salary'], inplace=True)

        def salary_cat(x):
            if x <= 20:
                return "20k以下"
            elif (x >= 20) and (x <= 30):
                return "20k~30k"
            else:
                return "30k以上"

        position_df['薪资等级'] = position_df['salary_ave'].map(salary_cat)

        plt.subplot(221)
        plt.hist(position_df['salary_ave'])
        plt.title(self.key_word + '岗位月薪分布')
        plt.xlabel('月薪（k）')
        plt.ylabel('职位数量（个）')

        label = " ".join([lab for lab in position_df['label']])
        cut_text = " ".join(jieba.cut(label))
        word_cloud = WordCloud(
            scale=5,
            font_path='C:/Windows/Fonts/simfang.ttf',
            background_color="white", width=1000, height=1000
        ).generate(cut_text)

        plt.subplot(222)
        plt.imshow(word_cloud, interpolation='bilinear')
        plt.title(self.key_word + '应用关键字')
        plt.axis('off')

        plt.subplot(223)
        sns.countplot(x=position_df['education'], hue=position_df['薪资等级'])
        plt.xlabel('最低学历要求')
        plt.ylabel('职位数量（个）')
        plt.title(self.key_word + '岗位学历要求以及薪资')

        plt.subplot(224)
        sns.countplot(x=position_df['workYear'], hue=position_df['薪资等级'])
        plt.xlabel('工作经验')
        plt.ylabel('职位数量（个）')
        plt.title(self.key_word + '岗位工作经验以及薪资')

        plt.show()


if __name__ == '__main__':
    user_word = input("输入搜索关键字： ")
    job_search = JobSearch(user_word)
    job_search.job_info_crawl()
    job_search.generate_wordcloud()
    job_search.handle_data()