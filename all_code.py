import csv
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time
import random
import matplotlib.pyplot as plt
import pandas as pd
import jieba
import jieba.analyse
import numpy as np
from PIL import Image
from wordcloud import WordCloud
from pyplotz.pyplotz import PyplotZ
from snownlp import SnowNLP

plt.rcParams['font.sans-serif'] = ['SimHei'] # 设置中文显示字体
plt.rcParams['axes.unicode_minus'] = False # 防止负号显示异常
pltz = PyplotZ()
pltz.enable_chinese()

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


# 定义一个函数来计算评论的情感倾向，返回消极、中性或积极
def sentiment_analysis(content):
    s = SnowNLP(content)
    score = s.sentiments # 得到一个0到1之间的分数，越接近1表示越积极
    if score < 0.4:
        return '消极'
    elif score > 0.6:
        return '积极'
    else:
        return '中性'


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
    '''
    读取刚刚爬好的热评文件
    df1 = pd.read_csv('hotComments_06.csv',index_col = 0)
    RROR: Buffer overflow caught -缓冲区溢出
    发现也是因为csv文件中单个item内有\r，即回车符
    解决方法：lineterminator=”\n”：让\n作为换行符即可
    '''
    df3 = pd.read_csv('hotComments_01.csv', index_col=0, lineterminator='\n')

    #  空格的影响会导致打字内容一样，但却被判为不一样
    # 用strip()方法去除开头或则结尾的空格
    df3['content'] = df3['content'].apply(lambda x: x.strip())

    # 有些句子中有\r，因为我们以\n作为换行符，所以这些\r不属于文本，需要去掉
    df3['content'] = df3['content'].apply(lambda x: x.replace('\r', ''))

    '''
    jieba库中基于 TextRank 算法的关键词抽取
    详情见官方文档：https://github.com/fxsjy/jieba
    '''
    segments = []
    for index, row in df3.iterrows():
        content = row['content']
        words = jieba.analyse.textrank(content, topK=3, withWeight=False, allowPOS=('ns', 'n', 'vn', 'v'))
        for w in words:  # 对分词好后的words进行提取，并且关联一个1，方便进行计数
            segments.append({'word': w, 'counts': 1})
    df_w = pd.DataFrame(segments)

    df_w.to_csv('jieba_01.csv', index=False, encoding='utf-8-sig')
    # wordcloud库制作云词
    # 将我们之前做的分词列表合并成字符串，以空格连接方便制作云词
    text = ' '.join(df_w['word'])
    '''
    word_cloud_example.png是一张作为蒙版的图片，需要转换成numy数组才可以用
    利用PIL模块读取我们的png文件并转换为numpy数组，作为WordCloud的mask参数传入
    '''
    mask_cir = np.array(Image.open('word_cloud_example.png'))
    wordc = WordCloud(
        background_color='white',
        mask=mask_cir,
        font_path='SimHei.ttf',  # 中文显示的方法，baidu载一个SimHei.ttf字体包即可让云词显示中文
        max_words=1000
    ).generate(text)
    plt.imshow(wordc)
    plt.axis('off')  # 关闭坐标轴，更加美观

    plt.savefig('word_cloud_result.jpg', dpi=600, bbox_inches='tight',
                pil_kwargs={"quality": 95})  # bbox_inches='tight'，可以达到去除空白的效果
    pltz.title(singer_name + '评论词云统计') # 在这里加上歌手名字
    plt.show()
    # 对每条评论应用这个函数，并将结果保存在一个新的列中
    df3['sentiment'] = df3['content'].apply(sentiment_analysis)

    # 统计每种情感倾向的频率，并绘制直方图
    freq = df3['sentiment'].value_counts()
    plt.bar(freq.index, freq.values)
    pltz.title(singer_name + '评论情感倾向频率直方图')
    plt.savefig('sentiment_freq.png', dpi=100)
    plt.savefig('sentiment_analysis.jpg', dpi=600, bbox_inches='tight',
                pil_kwargs={"quality": 95})  # bbox_inches='tight'，可以达到去除空白的效果
    plt.show()


if __name__ == '__main__':
    main()


