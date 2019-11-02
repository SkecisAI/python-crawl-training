import re
import time
import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
    'Host': 'wallpapershome.com'
}
size = '1920x1080'
save_path = 'wallpapers_src/'
start = time.time()


def handle_name(line):
    sep = '-'
    m = re.match('(.*)/(.*).html$', line)
    name = m.group(2)
    name = name.split('-')
    name.insert(-2, size)
    name = sep.join(name)
    return name


for i in range(68, 1502):  # 72
    wallpaper_name = []
    url = "https://wallpapershome.com/?page=" + str(i+1)
    r = requests.get(url, headers=headers)
    print("状态响应码:", r.status_code)
    soup = BeautifulSoup(r.content, 'lxml')
    wallpaper_list = soup.find('div', class_='pics')
    for j in range(12):
        wallpaper_name.append(handle_name(wallpaper_list.contents[j].a.get('href')))
    print("正在下载第" + str(i+1) + "个页面")
    cost = time.time() - start
    print("已运行时间:" + str(cost) + '秒')
    for j in range(12):
        src_url = 'https://wallpapershome.com/images/wallpapers/' + wallpaper_name[j] + '.jpg'
        with open(save_path+wallpaper_name[j]+'.jpg', 'wb') as f:
            img = requests.get(src_url).content
            f.write(img)
            print('+', end='')
            f.close()
    print('\n')