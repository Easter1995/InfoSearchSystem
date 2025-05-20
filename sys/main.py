import json
import re
import nltk
import numpy as np
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from nltk.stem.wordnet import WordNetLemmatizer
from stop_words import get_stop_words

app = Flask(__name__)
CORS(app)

nltk.download('wordnet')
stop_words = set(get_stop_words('en'))
lem = WordNetLemmatizer()

with open('json/key_words.json', 'r') as f:
    key_words = json.load(f)

with open('json/text_vector.json', 'r') as f:
    text_vector = json.load(f)

with open('json/reverse_index.json', 'r') as f:
    reverse_index = json.load(f)

rate_file = open('rate.txt', 'a')

def get_info(v):
    with open(f'IMDB/source/{v}.txt', 'r') as f:
        lines = f.readlines()
        return {
                'title': lines[0].strip(),
                'rate': lines[1].strip().replace('rate: ', ''),
                'director': lines[2].strip(),
                'writers': lines[3].strip(),
                'stars': lines[4].strip(),
                'summary': lines[5].strip() if len(lines) > 5 else "",
                'url': lines[6].strip().replace('url: ', '') if len(lines) > 6 else ""
            }

def handle_query(message):
    # 预处理 
    line = re.sub("[^a-zA-Z]", " ", message)
    line = line.lower()
    words = line.split()
    words = [lem.lemmatize(w) for w in words if not w in stop_words]
    
    # 查询向量
    query_vec = []
    for i in range(500):
        if key_words[i] in words:
            query_vec.append(1)
        else:
            query_vec.append(0)

    ret_info = {}
    sort_sim = {}
    for w in words:
        if w in key_words:
            if w in reverse_index:
                for id in reverse_index[w]:
                    doc_id = int(id)
                    if doc_id not in ret_info:  
                        # 计算相似度
                        doc_vec = text_vector[doc_id - 1]
                        query_np = np.array(query_vec)
                        doc_np = np.array(doc_vec)
                        query_magn = np.linalg.norm(query_np)
                        doc_magn = np.linalg.norm(doc_np)
                        if query_magn > 0 and doc_magn > 0:
                            dot_product = np.dot(query_np, doc_np)
                            cos_sim = dot_product / (query_magn * doc_magn)
                        else:
                            cos_sim = 0
                        ret_info[doc_id] = {
                            'sim': round(cos_sim, 4),
                            'match': ""
                        }
                        sort_sim[doc_id] = cos_sim
                    if w not in ret_info[doc_id]['match']:
                        ret_info[doc_id]['match'] += " "+ w
    sort_sim = list(sort_sim.items())
    sort_sim.sort(key=lambda x: x[1], reverse=True)
    
    ret_list = []
    for doc_id in sort_sim:
        result = ret_info[doc_id[0]]
        result.update(get_info(doc_id[0]))
        ret_list.append(result)
    return ret_list

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    if not query.strip():
        return jsonify({"error": "查询不能为空"}), 400
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = handle_query(query)
    return jsonify({
        "total": len(results),
        "timestamp": timestamp,
        "results": results
    })

@app.route('/api/rate', methods=['POST'])
def save_rate():
    data = request.json
    if not data or 'query' not in data or 'rate' not in data:
        return jsonify({"error": "缺少必要的字段"}), 400
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rate_file.write(f"查询: {data['query']}, 评分: {data['rate']}, 时间: {timestamp}\n")
    rate_file.flush()
    return jsonify({"success": True, "message": "评价已记录"})

if __name__ == '__main__':
    print("启动搜索...")
    app.run(host='127.0.0.1', port=5000, debug=True)