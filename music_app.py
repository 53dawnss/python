import tkinter as tk
import pandas as pd
from tkinter import messagebox
from bs4 import BeautifulSoup
import requests
import re
import os
import subprocess

class MusicApp:
    def __init__(self, master):
        self.master = master
        self.master.title('网易云音乐热评分析')

        # 创建标签和输入框
        self.label = tk.Label(master, text='请输入歌手名字：')
        self.label.pack(side=tk.LEFT, padx=10, pady=10)
        self.entry = tk.Entry(master)
        self.entry.pack(side=tk.LEFT, padx=10, pady=10)

        # 创建按钮
        self.button = tk.Button(master, text='搜索', command=self.search)
        self.button.pack(side=tk.LEFT, padx=10, pady=10)

        # 创建表格
        self.columns = ['歌曲名称', '歌手名称', '评论内容']
        self.df = pd.DataFrame(columns=self.columns)
        self.table = tk.Label(master, text=self.df.to_string(index=False))
        self.table.pack(side=tk.LEFT, padx=10, pady=10)

    def search(self):
        # 获取用户输入的歌手名字
        artist = self.entry.get()
        if not artist:
            messagebox.showerror('错误', '请输入歌手名字！')
            return

        # 获取歌手的 ID
        artist_id = self.search_singer_id(artist)
        if not artist_id:
            messagebox.showerror('错误', '未能找到该歌手！')
            return

        # 获取歌手的热门歌曲
        songs = self.get_songs(artist_id)
        if not songs:
            messagebox.showerror('错误', '未能获取热门歌曲！')
            return

        # 获取热评数据
        hot_comments = []
        for song in songs:
            hot_comments.extend(self.get_hot_comments(song['id']))
        if not hot_comments:
            messagebox.showerror('错误', '未能获取热评数据！')
            return

        # 在界面上显示热评数据
        self.df = pd.DataFrame(hot_comments, columns=self.columns)
        self.table.config(text=self.df.to_string(index=False))

    def search_singer_id(self, artist):
        url = f'https://music.163.com/#/search/m/?s={artist}&type=100'
        headers = {
            'Referer': 'https://music.163.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            artist_id = soup.find('a', {'class': 'nm nm-ic f-thide s-fc0'})['href'][len('/artist?id='):]
            return artist_id
        except:
            return None

    def get_songs(self, artist_id):
        url = f'https://music.163.com/artist?id={artist_id}'
        headers = {
            'Referer': 'https://music.163.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            songs = []
            song_list = soup.find('ul', {'class': 'f-hide'})
            for song in song_list.find_all('a'):
                song_name = song.text
                song_id = song['href'][len('/song?id='):]
                songs.append({'name': song_name, 'id': song_id})
            return songs
        except:
            return None

    def get_hot_comments(self, song_id):
        cmd = ['python', 'from_songid_to_hotcomment.py', song_id]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:
            output = result.stdout.decode('utf-8')
            hot_comments = []
            for line in output.split('\n'):
                match = re.match(r'(.+)\t(.+)\t(.+)', line)
                if match:
                    song_name = match.group(1)
                    artist_name = match.group(2)
                    comment = match.group(3)
                    hot_comments.append({'歌曲名称': song_name, '歌手名称': artist_name, '评论内容': comment})
            return hot_comments
        else:
            error = result.stderr.decode('utf-8')
            messagebox.showerror('错误', f'获取歌曲 {song_id} 的热评数据时出现错误：{error}')
            return []

root = tk.Tk()
app = MusicApp(root)
root.mainloop()