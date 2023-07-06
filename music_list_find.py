import logging
import requests
from pyquery import PyQuery as pq
import pandas as pd
import random
import time

# headers需要填上，否则无法正常爬取
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'}
# 设置日志的格式、输出级别
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')


def scrape_index(url):
    response = requests.get(url, headers=headers)
    logging.info('scrape index %s...', url)  # 不需要再url前加%，而是,
    try:
        if response.status_code == 200:
            return parse_index(response.text)  # 传到parse_index 方法中获取歌单url列表
        else:
            logging.error('invaild status is %s while scraping url %s', response.status_code, url)
    except Exception:
        logging.error('error occurred while scraping %s', url, exc_info=True)  # exc_info=True：会将异常异常信息添加到日志消息中


def parse_index(html):
    doc = pq(html)  # 用pyquery进行解析
    a = doc('#m-pl-container .dec .s-fc0')  # #对应div .对应class
    a1 = a.items()  # 对于返回值是多个元素，然后对每个元素做处理，需要调用items方法，返回的generator类型，可以通过for 循环去取值
    return a1


def scrape_detail(url):
    while True: # 添加一个循环
        response = requests.get(url, headers=headers)
        logging.info('尝试爬取歌单url %s...', url)
        try:
            if response.status_code == 200:
                data = response.json() # 将response.json()赋值给一个变量
                if 'result' in data and data['code'] == 200: # 判断是否有result键和code等于200
                    logging.info('成功获取歌单url')
                    return parse_detail(data)  # API获取的内容返回的是json格式
                else: # 如果没有result键或code不等于200
                    logging.info('服务器忙碌，稍后继续爬取') # 记录一条警告信息
                    time.sleep(5 + random.random()) # 等待一段时间
                    continue # 继续循环
            else:
                logging.error('invaild status is %s while scraping url %s', response.status_code, url)
                break # 跳出循环
        except Exception:
            logging.error('在爬取歌单%s时发生错误', url, exc_info=True)
            break # 跳出循环


'''
热评获取API:http://music.163.com/api/v1/resource/comments/R_SO_4_{歌曲ID}?limit=20&offset=0
所以获取歌曲的ID就可以得到热评
'''


def parse_detail(html):
    list_02 = []
    jobs = html['result']['tracks']
    for j in jobs:
        dic = {}
        dic['name'] = j['name']  # 创建 字典
        dic['id'] = j['id']
        list_02.append(dic)
    return list_02


def get_list(category): # 添加一个参数category，表示歌单目录的类别
    list_01 = []
    url = 'https://music.163.com/discover/playlist/?order=hot&cat={category}&limit=35&offset={page}'.format(category=category) # 将url中的"华语"替换为category
    for page in range(0, 35, 35):  # 跑一页试试，如果跑全部，改为 range(0,1295,35)
        url1 = url.format(page=page)
        list = []
        for i in scrape_index(url1):  # generator 遍历之后的i的类型仍然是qyquery类型
            i_url = i.attr('href')  # attr 方法来获取属性
            '''
            获取歌单和评论均用了网易云音乐get请求的API，快速高效！
            网易云歌单API
            https://music.163.com/api/playlist/detail?id={歌单ID}
            热评获取API
            http://music.163.com/api/v1/resource/comments/R_SO_4_{歌曲ID}?limit=20&offset=0
            '''
            detail_url = f'https://music.163.com/api{i_url.replace("?", "/detail?")}'  # 获取的url还需要替换一下符合API要求的格式
            list.append(detail_url)
        list_01.extend(list)  # extend 对列表合并
        time.sleep(5 + random.random())  # 文明爬虫
    return list_01


def save_date(list, category): # 添加一个参数category，表示歌单目录的类别
    df1 = pd.DataFrame(list)
    df2 = pd.concat([df, df1])
    df3 = df2.drop_duplicates(subset=None, keep='first', inplace=False)
    df3.to_csv('music_163_{category}.csv'.format(category=category), index_label="index_label", encoding='utf-8-sig')  # 将文件名也改为category相关的，避免覆盖之前的数据


df = pd.DataFrame(columns=('name', 'id'))


def main():
    category = input('请输入想要爬取的歌单目录类别：') # 添加一个输入语句，让用户输入想要爬取的歌单目录类别
    detail_list = []
    url_01 = get_list(category) # 将类别作为参数传递给get_list函数
    for l in url_01:
        logging.info('当前url为 %s', l)
        detail_list_part = scrape_detail(l)
        detail_list.extend(detail_list_part)  # 列表合并，得到最后的完整歌单信息列表
        time.sleep(5 + random.random())
    save_date(detail_list, category) # 将类别也传递给save_date函数


if __name__ == '__main__':
    main()