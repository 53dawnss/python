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

'''
读取刚刚爬好的热评文件
df1 = pd.read_csv('hotComments_06.csv',index_col = 0)
ERROR: Buffer overflow caught -缓冲区溢出
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

plt.savefig('word_cloud_result.jpg', dpi=600, bbox_inches='tight', pil_kwargs={"quality": 95})  # bbox_inches='tight'，可以达到去除空白的效果
plt.show()

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

# 对每条评论应用这个函数，并将结果保存在一个新的列中
df3['sentiment'] = df3['content'].apply(sentiment_analysis)

# 统计每种情感倾向的频率，并绘制直方图
freq = df3['sentiment'].value_counts()
plt.bar(freq.index, freq.values)
pltz.title('评论情感倾向频率直方图')
plt.savefig('sentiment_freq.png', dpi=100)
plt.savefig('sentiment_analysis.jpg', dpi=600, bbox_inches='tight', pil_kwargs={"quality": 95})  # bbox_inches='tight'，可以达到去除空白的效果
plt.show()