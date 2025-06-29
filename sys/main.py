import json
import re
import nltk
import numpy as np
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from nltk.stem.wordnet import WordNetLemmatizer
from stop_words import get_stop_words
from spellchecker import SpellChecker

app = Flask(__name__)
CORS(app)

nltk.download('wordnet')
stop_words = set(get_stop_words('en'))
lem = WordNetLemmatizer()
spell = SpellChecker()

with open('json/key_words.json', 'r') as f:
    key_words = json.load(f)

with open('json/text_vector.json', 'r') as f:
    text_vector = json.load(f)

with open('json/reverse_index.json', 'r') as f:
    reverse_index = json.load(f)

with open('json/extracted_info.json', 'r') as f:
    extracted_info_list = json.load(f)
    extracted_info = {}
    for item in extracted_info_list:
        if 'extracted' in item and 'url' in item:
            # URL -> doc_id
            url_id = item['url'].strip()
            extracted_info[url_id] = item['extracted']

rate_file = open('rate.txt', 'a')
extracted_rate_file = open('extraction_rate.txt', 'a')

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

def get_extracted_info(url_id):
    if url_id in extracted_info:
        return extracted_info[url_id]
    return None

def correct_spelling(words):
    corrected = []
    correction_info = {}
    for w in words:
        if w not in key_words and len(w) > 3:
            if w not in spell:
                correct_w = spell.correction(w)
                # 修正后在关键词列表中才采用
                if correct_w != w and correct_w in key_words:
                    corrected.append(correct_w)
                    correction_info[w] = correct_w
                else:
                    corrected.append(w)
            else:
                corrected.append(w)
        else:
            corrected.append(w)
    return corrected, correction_info
            
def handle_query(message):
    # 预处理 
    line = re.sub("[^a-zA-Z]", " ", message)
    line = line.lower()
    words = line.split()
    words = [lem.lemmatize(w) for w in words if not w in stop_words]
    
    # 拼写纠正
    words, correction_info = correct_spelling(words)

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
    
    return ret_list, correction_info

# 信息检索
@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    if not query.strip():
        return jsonify({"error": "Query cannot be empty"}), 400
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results, corrections = handle_query(query)
    return jsonify({
        "total": len(results),
        "timestamp": timestamp,
        "results": results,
        "corrections": corrections,
        "has_corrections": len(corrections) > 0
    })

@app.route('/api/rate', methods=['POST'])
def save_rate():
    data = request.json
    if not data or 'query' not in data or 'rate' not in data:
        return jsonify({"error": "Missing fields"}), 400
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rate_file.write(f"QUERY: {data['query']}, RATE: {data['rate']}, TIME: {timestamp}\n")
    rate_file.flush()
    return jsonify({"success": True, "message": "Rating saved successfully"}), 200

# 信息抽取
@app.route('/api/extract', methods=['GET'])
def get_extraction():
    doc_id = request.args.get('url')
    if not doc_id:
        return jsonify({"error": "Missing 'url' parameter"}), 400
    try:
        # basic_info = get_info(doc_id)
        extracted = get_extracted_info(doc_id)
        
        if extracted:
            return jsonify({
                "doc_id": doc_id,
                # "basic_info": basic_info,
                "extracted_info": extracted,
                "success": True
            })
        else:
            return jsonify({
                "doc_id": doc_id,
                # "basic_info": basic_info,
                "error": "No extraction data found for this document",
                "success": False
            }), 404
            
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/extract/rate', methods=['POST'])
def save_extraction_rate():
    data = request.json
<<<<<<< HEAD
    if not data or 'doc_id' not in data or 'rate' not in data:
        return jsonify({"error": "Missing required fields: doc_id, rate"}), 400
=======
    # print(data)
    if not data or 'doc_id' not in data or 'evaluation' not in data:
        return jsonify({"error": "Missing required fields: doc_id, evaluation"}), 400
>>>>>>> 075b71c7e9fe11431192d9b300608a743e087041
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        doc_info = get_info(data['doc_id'])
        movie_title = doc_info['title']
    except:
        movie_title = f"Document {data['doc_id']}"
    extracted_rate_file.write(f"MOVIE: {movie_title}, RATE: {data['rate']}, TIME: {timestamp}\n")
    extracted_rate_file.flush()
    return jsonify({"success": True, "message": "Rating saved successfully"}), 200

if __name__ == '__main__':
    print("Search begins...")
    app.run(host='127.0.0.1', port=5000, debug=True)