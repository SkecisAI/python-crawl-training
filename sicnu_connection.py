import re
import os
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
        self.learn_headers = {
            'Host': '202.115.194.60',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
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
        self.s = requests.Session()  # 开启会话
        self.url = self.__get_real_url()  # 获取真实url
        r = self.s.get(self.url, headers=self.headers)
        soup = BeautifulSoup(r.content, 'lxml')
        post_tuple = self.__get_post_data(soup)
        self.__set_post_data(post_tuple)
        self.__get_validate_code()  # 获取验证码
        if not self.__post() :  # 提交表单，登录
            return 'failed'
        else:
            self.__get_student_info()  # 获取学生总体成绩信息
            self.__get_score()  # 获取最后一次考试成绩单
            self.__get_learn_progress()  # 获取学习进度
            input("按任意键结束...")
            return 'success'

    def __get_learn_progress(self):
        self.__set_headers(self.learn_headers, self.index_url)
        learn_url = "http://202.115.194.60/" + self.rnd + "/ScoreQuery/wp_MyLearnProgress_Query.aspx"
        learn_request = self.s.get(learn_url, headers=self.learn_headers)
        soup = BeautifulSoup(learn_request.content, 'lxml')
        learn_table = soup.find_all('table', attrs={'class': 'table4'})  # 多个表
        learn_progress_dict = {}
        term_dict = {7: '大一（上）', 8: '大一（下）',
                     9: '大二（上）', 10: '大二（下）',
                     11: '大三（上）', 12: '大三（下）',
                     14: '大四（上）', 15: '大四（下）'}
        term_dict2 = {'大一（上）': [], '大一（下）': [],
                      '大二（上）': [], '大二（下）': [],
                      '大三（上）': [], '大三（下）': [],
                      '大四（上）': [], '大四（下）': []}
        print("*******                          我的学习进度（已考核）                        *******")
        for each_table in learn_table:
            table_content = each_table.find_all('tr')
            for i in range(3):
                table_content.pop(0)
            for each_tr in table_content[:-1]:
                grade_text = ''
                term = '无'
                for j in range(7, 16):  # 连接所有成绩所在列， 判断是第几个学期
                    term_grade = each_tr.find_all('td')[j].text
                    grade_text += term_grade
                    if (term_grade.strip() != '') and (j != 13):
                        term = term_dict[j]
                grade = re.search(r'[0-9]{2}', ''.join(grade_text))
                if not grade:
                    continue
                else:
                    grade = grade.group(0)
                credit = re.search(r'[0-9](.[0-9])?', each_tr.find_all('td')[16].text).group(0)
                gpa = re.search(r'[0-9](.[0-9])?', each_tr.find_all('td')[17].text).group(0)
                sub_name = each_tr.find_all('td')[2].text.strip()
                learn_progress_dict[sub_name] = [grade, credit, gpa, term]
                term_dict2[term].append([sub_name, grade, credit, gpa])
        print('-'*20, "展示方式（教务处顺序）:")
        print("     科目                                               成绩  学分  绩点")
        for k in learn_progress_dict.keys():
            print('- {0:{4}<25}\t{1:<2}\t{2:<3}\t{3:<3}'.format(k,
                                                                learn_progress_dict[k][0],
                                                                learn_progress_dict[k][1],
                                                                learn_progress_dict[k][2],
                                                                chr(12288)), '   ', learn_progress_dict[k][3])
        print('-' * 100)
        while True:
            show_type = input("是否要按学期分类（0-否 1-是）, 输入0或1：")
            if show_type in ['0', '1']:
                break
        if show_type == '1':
            for k in term_dict2:
                print('-'*75)
                print('-          ', k, '(科目 成绩  学分  绩点)          -')
                print('-'*75)
                for v in term_dict2[k]:
                    print('-- {0:{4}<25}\t{1:<2}\t{2:<3}\t{3:<3}'.format(v[0], v[1], v[2], v[3], chr(12288)))

    def __get_score(self):
        self.__set_headers(self.score_headers, self.index_url)
        score_url = "http://202.115.194.60/" + self.rnd + "/ScoreQuery/wp_MyElectCourseScore_Query.aspx"
        score_request = self.s.get(score_url, headers=self.score_headers)
        soup = BeautifulSoup(score_request.content, 'lxml')
        score_page = soup.find('table', attrs={'class': 'table4'})
        score_page_info = score_page.find_all('tr')
        print("**********                         学期成绩总览                  **********")
        score_page_info.pop(0)
        score_info_dict = {}
        for row in score_page_info:
            score_info_dict[row.find_all('td')[6].text.strip()] = re.search(r'[0-9]{2}', row.find_all('td')[12].text).group(0)  # 注意去除空格
        for k in score_info_dict.keys():
            print('- {0:{2}<20}\t{1:<2}'.format(k, score_info_dict[k], chr(12288)))
        print('-' * 100)

    def __get_student_info(self):
        self.__set_headers(self.login_headers, self.url)
        index_request = self.s.get(self.index_url, headers=self.login_headers)
        soup = BeautifulSoup(index_request.content, 'lxml')
        student_name = soup.find('span', attrs={'class': 'user_role'}).text.strip()
        print(' '*35, student_name)  # 学生信息

        self.__set_headers(self.student_headers, self.index_url)
        student_url = "http://202.115.194.60/" + self.rnd + "/Index/wp_StudentIndex.aspx"
        student_request = self.s.get(student_url, headers=self.student_headers)
        soup = BeautifulSoup(student_request.content, 'lxml')
        student_page = soup.find('table', attrs={'class': 'table4'})
        student_page_info = student_page.find_all('tr')
        print('-' * 100)
        print("**********                         学生成绩总览                  **********")
        student_info_dict = {'平均成绩': float(student_page_info[1].find_all('td')[1].text),
                             '平均绩点': float(student_page_info[1].find_all('td')[2].text),
                             '总学分': int(student_page_info[6].find_all('td')[1].text)}
        for k in student_info_dict.keys():
            print('- ', k, ':', student_info_dict[k])
        print('-' * 100)

    def __post(self):
        self.__set_headers(self.post_headers, self.url)
        response = self.s.post(self.url, data=self.post_data, headers=self.post_headers, allow_redirects=True)
        try:
            sid = response.headers['Set-Cookie'].split('&')[-1].split(';')[0].split('=')[-1]
        except KeyError:
            self.count += 1
            print("***ERROR***: 识别错误, 重新连接......   No. " + str(self.count) + " 次重试")
            return False  # 识别错误则返回，进行下一次尝试
        print('-' * 100)
        print(">>>>>>>>>>>>>>>>>>>>               Nice!!  识别成功 ^_^              <<<<<<<<<<<<<<<<<<<<")
        print('-' * 100)
        print("   ##         ####        #####       #####    #######        ##       ##    ##        ##")
        print("   ##       ##    ##    ##          ##         ##             ##       ##    ## ##     ##")
        print("   ##      ##      ##  ##   #####  ##   #####  #######  ########       ##    ##   ##   ##")
        print("   ##       ##    ##    ##  ## ##   ##  ## ##  ##       ##    ##       ##    ##     ## ##")
        print("   #######    ####       ######      ######    #######  ########       ##    ##       ###")
        print('-' * 100)
        self.index_url = "http://202.115.194.60/" + self.rnd + "/Index.aspx?sid=" + sid
        return True

    def __get_validate_code(self):
        img_url = "http://202.115.194.60/" + self.rnd + "/CheckCode.aspx"
        img = self.s.get(img_url, stream=True)
        with open('validate_code.png', 'wb') as fv:
            fv.write(img.content)
            fv.close()
        code_img = Image.open('validate_code.png')
        print("识别验证码中...  ", end='')
        validate_code = recog_code.handle_img(code_img)
        if not validate_code:
            print("Error: 图片切割失败x_x  重新连接......")
        else:
            print("验证码为：", validate_code)
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
    if os.path.exists('user_info.json'):
        user_json = open("user_info.json").read()
        tbUserName = json.loads(user_json)['user_id']
        tbPassWord = json.loads(user_json)['user_pwd']
        print("最后一次成功登录的账号信息（请核对）：", '*学号*', tbUserName, '*密码*', tbPassWord)
        print("若想更换账号信息，请在安装文件夹中找到“user_info.json”， *按格式*打开修改账号信息（切勿乱改，复原即可）")
    else:
        print("你是*第一次*使用本程序（或没有成功登录过），需输入你的账号信息，若登录成功则之后不会再询问。")
        print('-'*50)
        tbUserName = input("输入你的学号：")
        tbPassWord = input("输入你的密码(确保周围无人)：")
    user_data = {
        "user_id": tbUserName,
        "user_pwd": tbPassWord
    }
    print('-'*100)
    my_connection = MyConnect(tbUserName, tbPassWord)
    while True:
        res = my_connection.connect()
        if res == 'failed':
            if my_connection.count >= 35:
                print(">>>>>>>      重试次数已达上限！！！  1.你的账号信息是否有误，请回想一下！！！  2.再次运行程序    <<<<<<<")
                input("按回车(Enter)退出程序... ...")
                break
            continue
        else:
            with open('user_info.json', 'w') as f:  # 存储为json文件
                json.dump(user_data, f)
                f.close()
            break
