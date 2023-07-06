import csv
import requests
from lxml import etree


headers = {
   'Referer': 'http://music.163.com',
   'Host': 'music.163.com',
   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
   'User-Agent': 'Chrome/10'
  }

# 得到指定歌手 热门前50的歌曲ID，歌曲名
def get_songs(artist_id):
   page_url = 'https://music.163.com/artist?id=' + artist_id
   # 获取对应HTML
   res = requests.request('GET', page_url, headers=headers)
   # XPath解析 前50的热门歌曲
   html = etree.HTML(res.text)
   href_xpath = "//*[@id='hotsong-list']//a/@href"
   name_xpath = "//*[@id='hotsong-list']//a/text()"
   hrefs = html.xpath(href_xpath)
   names = html.xpath(name_xpath)
   # 设置热门歌曲的ID，歌曲名称
   song_ids = []
   song_names = []
   for href, name in zip(hrefs, names):
       song_ids.append(href[9:])
       song_names.append(name)
   return song_ids, song_names

# 用户输入歌手ID
artist_id = input("请输入歌手ID：")

# 获取歌手排名前50的歌曲ID
song_ids, song_names = get_songs(artist_id)

# 将结果保存到CSV文件
with open('music_id.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['index_label', 'name', 'id'])
    for i, (name, song_id) in enumerate(zip(song_names, song_ids)):
        writer.writerow([i+1, name, song_id])