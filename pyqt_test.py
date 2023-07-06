import requests
import pandas as pd
import time
import random
import jieba.analyse
import logging
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QLineEdit, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap

headers = {
    'Referer': 'https://music.163.com/',
    'Host': 'music.163.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/58.0.3029.110 Safari/537.3'
}


def search_singer_id(name):
    search_url = 'https://music.163.com/api/search/get/web?csrf_token='
    search_data = {
        's': name,
        'type': '100'
    }

    try:
        response = requests.post(search_url, headers=headers, data=search_data)
        result = response.json()
        if result['code'] == 200:
            if len(result['result']['artists']) > 0:
                return result['result']['artists'][0]['id']
            else:
                return None
        else:
            logging.error('Search error, error code: %s', result['code'])
            return None
    except Exception as e:
        logging.error('Search error, error info: %s', e)
        return None


def scrape_comment(url, name):
    headers = {
        'Referer': 'https://music.163.com/',
        'Host': 'music.163.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    comments_json = response.json()
    comments = comments_json['hotComments']
    data = []
    for comment in comments:
        dic = {}
        dic['name'] = name
        dic['content'] = comment['content']
        dic['time'] = comment['time']
        data.append(dic)
    return data


def sentiment(comment):
    url = 'https://aip.baidubce.com/rpc/2.0/nlp/v1/sentiment_classify'
    access_token = '24.8b9a9292b6f7a6d77c06a17c3b1c4a28.2592000.1664456979.282335-24653366'
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'text': comment,
        'access_token': access_token
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        if 'items' in result:
            sentiment = result['items'][0]['sentiment']
            if sentiment == 0:
                return 'negative'
            elif sentiment == 1:
                return 'neutral'
            else:
                return 'positive'
        else:
            logging.error('Sentiment analysis result is invalid')
            return None
    except Exception as e:
        logging.error('Sentiment analysis error, error info: %s', e)
        return None


class MusicApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'NetEase Cloud Music Comment Analysis'
        self.left = 100
        self.top = 100
        self.width = 350
        self.height = 250
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.label = QLabel(self)
        self.label.setText("Please enter the singer's name:")
        self.label.move(20, 20)

        self.textbox = QLineEdit(self)
        self.textbox.move(20, 50)
        self.textbox.resize(200, 25)

        self.button = QPushButton('Start analysis', self)
        self.button.setToolTip('Click to start analysis')
        self.button.move(20, 90)
        self.button.clicked.connect(self.on_button_click)

        self.statusBar().showMessage('Ready')

        self.show()

    def on_button_click(self):
        singer_name = self.textbox.text()
        if singer_name.strip() == "":
            QMessageBox.warning(self, "Error", "Singer's name cannot be empty")
            return
        self.statusBar().showMessage('Analysis in progress.')