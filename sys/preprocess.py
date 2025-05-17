import json
import re
import nltk

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem.wordnet import WordNetLemmatizer
from stop_words import get_stop_words

nltk.download('wordnet')

# 停用词
stop_words = set(get_stop_words('en'))
new_words = ['writers', 'director', 'stars']
stop_words = stop_words.union(new_words)
# 还原基本词型
lem = WordNetLemmatizer()

# 分词
corpus = []
raw_corpus = []
clean_corpus = []

for i in range(1, 251):
    with open(f'IMDB/source/{i}.txt', 'r') as f:
        lines = f.readlines()
        line = lines[0] + lines[2] + lines[3] + lines[4] + lines[5]
        line = re.sub('[^a-zA-Z]', ' ', line)               # 只保留字母
        line = re.sub('&lt;/?.*?&gt', ' &lt;&gt; ', line)   # 去掉标签
        line = line.lower()                                 # 全部小写
        raw_text = line.split()
        clean_line = [lem.lemmatize(word) for word in raw_text if not word in stop_words]
        clean_corpus.append(clean_line)
        raw_text = [lem.lemmatize(word) for word in raw_text]
        clean_line = ' '.join(clean_line)
        raw_corpus.append(raw_text)
        corpus.append(clean_line)

vectorizer = TfidfVectorizer()          # 初始化向量器
X = vectorizer.fit_transform(corpus)    # 建立词汇表

data = {
  'word': vectorizer.get_feature_names_out(),     # 词汇表中的所有词
  'tfidf': X.toarray().sum(axis=0).tolist()       # 对每一列（每个词）求和，得到该词在所有文档中的总 TF–IDF 值
}
df = pd.DataFrame(data)
df.sort_values(by="tfidf", ascending=False, inplace=True) # 降序排序
key_words = df.head(500)['word'].to_list()                # 选取前500词
with open('json/key_words.json', 'w') as f:
    f.write(json.dumps(key_words))

# 关键词构建向量空间模型
text_vector = []
for i in range(250):
    text_vector.append([])
    for j in range(500):
        if key_words[j] in clean_corpus[i]:
            text_vector[i].append(1)
        else:
            text_vector[i].append(0)
with open('json/text_vector.json', 'w') as f:
    f.write(json.dumps(text_vector))

# 建立倒排序索引表
reverse_index = {}
for i in range(1, 251):
    for j in range(len(raw_corpus[i - 1])):
        word = raw_corpus[i - 1][j]
        if word in key_words:
            if not reverse_index.get(word):
                reverse_index[word] = {}
            word_index = reverse_index[word]
            if not word_index.get(i):
                word_index[i] = []
            word_index[i].append(j) # word为第i篇文章的第j个词
            reverse_index[word] = word_index
with open('json/reverse_index.json', 'w') as f:
    f.write(json.dumps(reverse_index))