import re
import getpass
import requests
from PIL import Image
from bs4 import BeautifulSoup


tbUserName = input("输入学号：")
tbPassWord = input("输入密码：")
headers = {
    'Host': '202.115.194.60',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'
}


# 获取url上的随机数
def handle_url(u):
    m = re.match('(.*)/(.*)/default.aspx$', u)
    name = m.group(2)
    return name


s = requests.Session()
url = "http://202.115.194.60/default.aspx"
r = s.get(url, headers=headers)
rnd = handle_url(r.url)
# 构造真实url
url = "http://202.115.194.60/" + rnd + "/default.aspx"
r = s.get(url, headers=headers)
soup = BeautifulSoup(r.content, 'lxml')
hid_input = soup.find_all('input', type='hidden')
post_list = ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION']
val = []
for input_ele in hid_input:
    if input_ele.get('name') in post_list:
        val.append(input_ele.get('value'))
_view_state = val[0]
_view_state_generator = val[1]
_event_validation = val[2]

# 获取验证码图片
img_url = "http://202.115.194.60/" + rnd + "/CheckCode.aspx"
img = s.get(img_url, stream=True)
with open('code.jpg', 'wb') as f:
    f.write(img.content)
# 手动输入验证码
code_img = Image.open('code.jpg')
code_img.show()
validate_code = input("验证码: ")
# 提交数据
post_data = {
    '__LASTFOCUS': '',
    '__EVENTTARGET': '',
    '__EVENTARGUMENT': '',
    '__VIEWSTATE': _view_state,
    '__VIEWSTATEGENERATOR': _view_state_generator,
    '__EVENTVALIDATION': _event_validation,
    'tbUserName': tbUserName,
    'tbPassWord': tbPassWord,
    'txtCode': validate_code,
    'btnLogin': ''
}

# 登陆教务系统
post_headers = {
    'Host': '202.115.194.60',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
    'Origin': 'http://202.115.194.60',
    'Referer': url
}

response = s.post(url, data=post_data, headers=post_headers, allow_redirects=True)
sid = response.headers['Set-Cookie'].split('&')[-1].split(';')[0].split('=')[-1]
index_url = "http://202.115.194.60/" + rnd + "/Index.aspx?sid=" + sid
login_headers = {
    'Host': '202.115.194.60',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    'Origin': 'http://202.115.194.60',
    'Referer': url
}
# 访问首页
index_request = s.get(index_url, headers=login_headers)
soup = BeautifulSoup(index_request.content, 'lxml')
student_name = soup.find('span', attrs={'class': 'user_role'}).text.strip()
print(student_name)
# 学生首页
student_headers = {
    'Host': '202.115.194.60',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    'Origin': 'http://202.115.194.60',
    'Referer': index_url
}
student_url = "http://202.115.194.60/" + rnd + "/Index/wp_StudentIndex.aspx"
student_request = s.get(student_url, headers=student_headers)
soup = BeautifulSoup(student_request.content, 'lxml')
student_page = soup.find('table', attrs={'class': 'table4'})
student_page_info = student_page.find_all('tr')

print('-'*20)
print("***学生成绩总览***:")
student_info_dict = {'平均成绩': float(student_page_info[1].find_all('td')[1].text),
                     '平均绩点': float(student_page_info[1].find_all('td')[2].text),
                     '总学分': int(student_page_info[6].find_all('td')[1].text)}
for k in student_info_dict.keys():
    print(k, ':', student_info_dict[k])
print('-'*20)
# 学期成绩
score_headers = {
    'Host': '202.115.194.60',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    'Origin': 'http://202.115.194.60',
    'Referer': index_url
}
score_url = "http://202.115.194.60/"+rnd+"/ScoreQuery/wp_MyElectCourseScore_Query.aspx"
score_request = s.get(score_url, headers=score_headers)
soup = BeautifulSoup(score_request.content, 'lxml')
score_page = soup.find('table', attrs={'class': 'table4'})
score_page_info = score_page.find_all('tr')
print("***学期成绩总览***:")
score_page_info.pop(0)
score_info_dict = {}
for row in score_page_info:
    score_info_dict[row.find_all('td')[6].text.strip()] = re.search(r'[0-9]{2}', row.find_all('td')[12].text).group(0)  # 注意去除空格
for k in score_info_dict.keys():
    print(k, ':', score_info_dict[k])
input("按任意键结束...")