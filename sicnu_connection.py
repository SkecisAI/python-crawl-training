import re
import json
import requests
import recog_code
from PIL import Image
from bs4 import BeautifulSoup


class MyConnect:
    def __init__(self, name, password):
        self.s = None
        self.count = 1
        self.name = name
        self.rnd = ''
        self.url = ''
        self.index_url = ''
        self.pwd = password
        self.headers = {
            'Host': '202.115.194.60',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'
        }
        self.post_headers = {
            'Host': '202.115.194.60',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
            'Origin': 'http://202.115.194.60',
            'Referer': self.url
        }
        self.login_headers = {
            'Host': '202.115.194.60',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'Origin': 'http://202.115.194.60',
            'Referer': self.url
        }
        self.student_headers = {
            'Host': '202.115.194.60',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'Origin': 'http://202.115.194.60',
            'Referer': self.index_url
        }
        self.score_headers = {
            'Host': '202.115.194.60',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'Origin': 'http://202.115.194.60',
            'Referer': self.index_url
        }
        self.post_data = {
            '__LASTFOCUS': '',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': None,
            '__VIEWSTATEGENERATOR': None,
            '__EVENTVALIDATION': None,
            'tbUserName': None,
            'tbPassWord': None,
            'txtCode': None,
            'btnLogin': ''
        }

    def __set_headers(self, headers, url):
        headers['Referer'] = url

    def __get_rnd(self, u):
        """
        获取url上的随机数
        """
        m = re.match('(.*)/(.*)/default.aspx$', u)
        self.rnd = m.group(2)

    def __get_real_url(self):
        url = "http://202.115.194.60/default.aspx"
        r = self.s.get(url, headers=self.headers)
        self.__get_rnd(r.url)
        # 构造真实url
        url = "http://202.115.194.60/" + self.rnd + "/default.aspx"
        return url

    def connect(self):
        self.s = requests.Session()
        self.url = self.__get_real_url()
        r = self.s.get(self.url, headers=self.headers)
        soup = BeautifulSoup(r.content, 'lxml')
        post_tuple = self.__get_post_data(soup)
        self.__set_post_data(post_tuple)
        self.__get_validate_code()
        if not self.__post():
            return 'failed'
        else:
            self.__get_student_info()
            self.__get_score()
            return 'success'

    def __get_score(self):
        self.__set_headers(self.score_headers, self.index_url)
        score_url = "http://202.115.194.60/" + self.rnd + "/ScoreQuery/wp_MyElectCourseScore_Query.aspx"
        score_request = self.s.get(score_url, headers=self.score_headers)
        soup = BeautifulSoup(score_request.content, 'lxml')
        score_page = soup.find('table', attrs={'class': 'table4'})
        score_page_info = score_page.find_all('tr')
        print("***  学期成绩总览  ***")
        score_page_info.pop(0)
        score_info_dict = {}
        for row in score_page_info:
            score_info_dict[row.find_all('td')[6].text.strip()] = re.search(r'[0-9]{2}', row.find_all('td')[12].text).group(0)  # 注意去除空格
        for k in score_info_dict.keys():
            print('- ', k, ':', score_info_dict[k])
        print('-'*30)
        input("按任意键结束...")

    def __get_student_info(self):
        self.__set_headers(self.login_headers, self.url)
        index_request = self.s.get(self.index_url, headers=self.login_headers)
        soup = BeautifulSoup(index_request.content, 'lxml')
        student_name = soup.find('span', attrs={'class': 'user_role'}).text.strip()
        print(student_name)  # 学生信息

        self.__set_headers(self.student_headers, self.index_url)
        student_url = "http://202.115.194.60/" + self.rnd + "/Index/wp_StudentIndex.aspx"
        student_request = self.s.get(student_url, headers=self.student_headers)
        soup = BeautifulSoup(student_request.content, 'lxml')
        student_page = soup.find('table', attrs={'class': 'table4'})
        student_page_info = student_page.find_all('tr')
        print('-' * 30)
        print("***  学生成绩总览  ***")
        student_info_dict = {'平均成绩': float(student_page_info[1].find_all('td')[1].text),
                             '平均绩点': float(student_page_info[1].find_all('td')[2].text),
                             '总学分': int(student_page_info[6].find_all('td')[1].text)}
        for k in student_info_dict.keys():
            print('- ', k, ':', student_info_dict[k])
        print('-' * 30)

    def __post(self):
        self.__set_headers(self.post_headers, self.url)
        response = self.s.post(self.url, data=self.post_data, headers=self.post_headers, allow_redirects=True)
        sid = ''
        try:
            sid = response.headers['Set-Cookie'].split('&')[-1].split(';')[0].split('=')[-1]
        except KeyError:
            self.count += 1
            print("***Error***: 验证码识别错误, 重新连接-------第 " + str(self.count) + " 次重试")
            return False                   # 识别错误则返回，进行下一次尝试
        print("  Nice!!  识别成功！！")
        print('-'*30)
        print("    成功登录  ^_^")
        print('-'*30)
        self.index_url = "http://202.115.194.60/" + self.rnd + "/Index.aspx?sid=" + sid
        return True

    def __get_validate_code(self):
        img_url = "http://202.115.194.60/" + self.rnd + "/CheckCode.aspx"
        img = self.s.get(img_url, stream=True)
        with open('validate_code.png', 'wb') as f:
            f.write(img.content)
            f.close()
        code_img = Image.open('validate_code.png')
        print("识别验证码中...  ", end='')
        validate_code = recog_code.handle_img(code_img)
        if not validate_code:
            print("Error: 验证码切割失败x_x  重新连接... ...")
        else:
            print("识别出的验证码为：", validate_code)
            self.post_data['txtCode'] = validate_code

    def __set_post_data(self, post_data):
        self.post_data['__VIEWSTATE'] = post_data[0]
        self.post_data['__VIEWSTATEGENERATOR'] = post_data[1]
        self.post_data['__EVENTVALIDATION'] = post_data[2]
        self.post_data['tbUserName'] = self.name
        self.post_data['tbPassWord'] = self.pwd

    def __get_post_data(self, soup):
        hid_input = soup.find_all('input', type='hidden')
        post_list = ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION']
        val = []
        # 获取表单数据
        for input_ele in hid_input:
            if input_ele.get('name') in post_list:
                val.append(input_ele.get('value'))
        _view_state = val[0]
        _view_state_generator = val[1]
        _event_validation = val[2]
        return _view_state, _view_state_generator, _event_validation


if __name__ == "__main__":
    user_json = open("user_info.json").read()
    tbUserName = json.loads(user_json)['user_id']
    tbPassWord = json.loads(user_json)['user_pwd']
    # tbUserName = input("输入你的学号：")
    # tbPassWord = input("输入你的密码(确保周围无人)：")
    my_connection = MyConnect(tbUserName, tbPassWord)
    while True:
        res = my_connection.connect()
        if res == 'failed':
            continue
        else:
            break