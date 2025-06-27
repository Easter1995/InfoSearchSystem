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
    extracted_info = json.load(f)

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

def get_extracted_info(doc_id):
    doc_key = str(doc_id)
    if doc_key in extracted_info:
        return extracted_info[doc_key]
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
    rate_file.write(f"QUERY: {data['query']}, RATE:{data['rate']}, TIME: {timestamp}\n")
    rate_file.flush()
    return jsonify({"success": True, "message": "Rating saved successfully"}), 200

# 信息抽取

@app.route('/api/extract/<int:doc_id>', methods=['GET'])
def get_extraction(doc_id):
    try:
        basic_info = get_info(doc_id)
        extracted = get_extracted_info(doc_id)
        
        if extracted:
            return jsonify({
                "doc_id": doc_id,
                "basic_info": basic_info,
                "extracted_info": extracted,
                "success": True
            })
        else:
            return jsonify({
                "doc_id": doc_id,
                "basic_info": basic_info,
                "error": "No extraction data found for this document",
                "success": False
            }), 404
            
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/extract/search', methods=['GET'])
def search_by_extraction():
    query = request.args.get('q', '').lower()
    info_type = request.args.get('type', 'all')  # all, persons, organizations, locations, keywords
    
    if not query.strip():
        return jsonify({"error": "Query cannot be empty"}), 400
    
    results = []
    
    for doc_id, extracted in extracted_info.items():
        match_score = 0
        match_details = {}
        
        # 根据类型搜索
        if info_type == 'all' or info_type == 'persons':
            if 'persons' in extracted:
                matches = [p for p in extracted['persons'] if query in p.lower()]
                if matches:
                    match_score += len(matches)
                    match_details['persons'] = matches
        
        if info_type == 'all' or info_type == 'organizations':
            if 'organizations' in extracted:
                matches = [o for o in extracted['organizations'] if query in o.lower()]
                if matches:
                    match_score += len(matches)
                    match_details['organizations'] = matches
        
        if info_type == 'all' or info_type == 'locations':
            if 'locations' in extracted:
                matches = [l for l in extracted['locations'] if query in l.lower()]
                if matches:
                    match_score += len(matches)
                    match_details['locations'] = matches
        
        if info_type == 'all' or info_type == 'keywords':
            if 'keywords' in extracted:
                matches = [k for k in extracted['keywords'] if query in k.lower()]
                if matches:
                    match_score += len(matches) * 0.5  # 关键词权重稍低
                    match_details['keywords'] = matches[:10]  # 限制关键词数量
        
        if match_score > 0:
            try:
                basic_info = get_info(int(doc_id))
                results.append({
                    "doc_id": int(doc_id),
                    "match_score": round(match_score, 2),
                    "match_details": match_details,
                    "basic_info": basic_info
                })
            except Exception as e:
                continue
    
    # 按匹配分数排序
    results.sort(key=lambda x: x['match_score'], reverse=True)
    
    return jsonify({
        "query": query,
        "type": info_type,
        "total": len(results),
        "results": results[:50],
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/api/extract/stats', methods=['GET'])
def extraction_stats():
    stats = {
        "total_documents": len(extracted_info),
        "info_types": {
            "persons": {"count": 0, "unique": set()},
            "organizations": {"count": 0, "unique": set()},
            "locations": {"count": 0, "unique": set()},
            "keywords": {"count": 0, "unique": set()}
        }
    }
    
    for doc_id, extracted in extracted_info.items():
        for info_type in stats["info_types"]:
            if info_type in extracted and extracted[info_type]:
                stats["info_types"][info_type]["count"] += len(extracted[info_type])
                stats["info_types"][info_type]["unique"].update(extracted[info_type])

    for info_type in stats["info_types"]:
        unique_count = len(stats["info_types"][info_type]["unique"])
        stats["info_types"][info_type]["unique_count"] = unique_count
        del stats["info_types"][info_type]["unique"]
    
    return jsonify(stats)

@app.route('/api/extract/rate', methods=['POST'])
def save_extraction_rate():
    data = request.json
    if not data or 'doc_id' not in data or 'evaluation' not in data:
        return jsonify({"error": "Missing required fields: doc_id, evaluation"}), 400
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    extracted_rate_file.write(f"DOC_ID: {data['doc_id']}, ")
    extracted_rate_file.write(f"EVALUATION: {data['evaluation']}, ")
    if 'comments' in data:
        extracted_rate_file.write(f"COMMENTS: {data['comments']}, ")
    extracted_rate_file.write(f"TIME: {timestamp}\n")
    return jsonify({"success": True, "message": "Rating saved successfully"}), 200

if __name__ == '__main__':
    print("Search begins...")
    app.run(host='127.0.0.1', port=5000, debug=True)