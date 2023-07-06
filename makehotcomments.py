import csv
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time
import random

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')


def search_singer_id(singer_name):
    key_ids = {1001: "华语男歌手", 1002: "华语女歌手", 1003: "华语组合或乐队", 2001: "欧美男歌手", 2002: "欧美女歌手", 2003: "欧美组合或乐队",
               6001: "日本男歌手", 6002: "日本女歌手", 6003: "日本组合或乐队", 7001: "韩国男歌手", 7002: "韩国女歌手", 7003: "韩国组合或乐队",
               4001: "其他男歌手", 4002: "其他女歌手", 4003: "其他组合或乐队"}

    initials = [65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 0]

    base_url = "https://music.163.com/discover/artist/cat?id={}&initial={}"

    for id in key_ids.keys():
        for initial in initials:
            try:
                url = base_url.format(str(id), str(initial))
                response = requests.get(url, headers=headers)
                response.encoding = "utf-8"
                soup = BeautifulSoup(response.text, "html.parser")
                ul = soup.find("ul", class_="m-cvrlst m-cvrlst-5 f-cb")
                a_s = ul.find_all("a", class_="nm nm-icn f-thide s-fc0")
                for a in a_s:
                    if a.text == singer_name:
                        singer_id = a['href'].split('=')[1]
                        return singer_id
            except Exception as e:
                print(e)
                continue
    # 如果没有找到对应的歌手姓名，则返回None
    return None


def scrape_comment(url, name):
    logging.info('scraping comments %s', url)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return parse_comment(response.json(), name)  # 网易云热评API返回的是json格式
        else:
            logging.error('invaild status_code %s while scraping %s', response.status_code, url)
    except Exception:
        logging.error('can not scraping %s', url)


def parse_comment(html, name):
    data = []
    jobs = html['hotComments']
    for job in jobs:
        dic = {}
        dic['nickname'] = job['user']['nickname']
        dic['userid'] = job['user']['userId']
        dic['content'] = job['content'].replace('\n', '')  # 对换行符进行替换
        dic['likecount'] = job['likedCount']
        dic['time'] = stampToTime(job['time'])  # 时间戳的转换
        dic['name'] = name
        data.append(dic)
    return data


def stampToTime(stamp):
    '''
    获得是13位的时间戳，需要转化成时间字符串
    将ms(毫秒)转成s(秒)  stamp/1000
    将10位的符合python的时间戳转化成时间元组,localtime()：北京时间
    将时间元组用strftime转化成时间字符串

    '''
    timeStamp = float(stamp / 1000)
    timeArray = time.localtime(timeStamp)
    date = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return date


def main():
    # 用户需要输入歌手姓名
    singer_name = input("请输入歌手姓名：")
    singer_id = search_singer_id(singer_name)
    if singer_id is None:
        print("未找到该歌手，请确认输入的姓名是否正确")
        return

    url = f"https://music.163.com/api/v1/artist/{singer_id}"
    response = requests.get(url, headers=headers)
    data = response.json()['hotSongs']
    music_data = []
    for d in data:
        dic = {}
        dic['name'] = d['name']
        dic['id'] = d['id']
        music_data.append(dic)
    df = pd.DataFrame(music_data)

    data_comment = []
    for index, row in df.iterrows():  # 数据框中的行 进行迭代的一个生成器，它返回每行的索引及一个包含行本身的对象。
        name = row['name']
        '''
        网易云音乐获取热评的API
        limit：返回数据条数(每页获取的数量)，默认为20，可以自行更改
        offset：偏移量(翻页)，offset需要是limit的倍数
        type：搜索的类型
        http://music.163.com/api/v1/resource/comments/R_SO_4_{歌曲ID}?limit=20&offset=0
        '''
        url = f'http://music.163.com/api/v1/resource/comments/R_SO_4_{row["id"]}?limit=20&offset=0'  # 只爬取首页（第一页）的热评
        data1 = scrape_comment(url, name)
        data_comment.extend(data1)
        df1 = pd.DataFrame(data_comment)
        df1.to_csv('hotComments.csv', encoding='utf-8-sig')  # 是utf-8-sig 而不是utf-8
        logging.info('scraping id %s', index)
        time.sleep(random.random())  # 文明爬虫


if __name__ == '__main__':
    main()