import pandas as pd
import requests
import logging
import time
import random

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'}
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')


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
    df = pd.read_csv('music_id.csv', header=0)  # 对上个保存的歌曲的ID的csv的内容提取，header= 0：第一行作为column
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
        url = f'http://music.163.com/api/v1/resource/comments/R_SO_4_{row["id"]}?limit=20&offset=0'  # 本文只爬取首页（第一页）的热评
        data1 = scrape_comment(url, name)
        data_comment.extend(data1)
        df1 = pd.DataFrame(data_comment)
        df1.to_csv('hotComments.csv', encoding='utf-8-sig')  # 是utf-8-sig 而不是utf-8
        logging.info('scraping id %s', index)
        time.sleep(random.random())  # 文明爬虫


if __name__ == '__main__':
    main()
