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

entity_index = {
    'persons': {},
    'organizations': {}, 
    'locations': {},
    'keywords': {}
}

def build_entity_index():
    for url_id, extracted in extracted_info.items():
        for entity_type in entity_index:
            if entity_type in extracted:
                for item in extracted[entity_type]:
                    item_lower = item.lower()
                    if item_lower not in entity_index[entity_type]:
                        entity_index[entity_type][item_lower] = []
                    entity_index[entity_type][item_lower].append(url_id)

build_entity_index()

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

def validate_request(required_fields, data):
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            return False, f"Missing required field: {field}"
    return True, None

def search_entity_matches(query, entity_type, extracted_data):
    if entity_type in extracted_data:
        matches = [item for item in extracted_data[entity_type] if query in item.lower()]
        if matches:
            # 关键词的权重设为0.5，其他类型为1.0
            weight = 0.5 if entity_type == 'keywords' else 1.0
            return matches, len(matches) * weight
    return [], 0

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
    rate_file.write(f"QUERY: {data['query']}, RATE:{data['rate']}, TIME: {timestamp}\n")
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

@app.route('/api/extract/search', methods=['GET'])
def search_by_extraction():
    query = request.args.get('q', '').lower()
    info_type = request.args.get('type', 'all')
    
    if not query.strip():
        return jsonify({"error": "Query cannot be empty"}), 400
    
    results = []
    entity_types = ['persons', 'organizations', 'locations', 'keywords']
    
    try:
        matching_docs = {}
        types_to_search = [info_type] if info_type in entity_types else entity_types
        
        # 根据查询在倒排索引中搜索
        for entity_type in types_to_search:
            for entity, doc_ids in entity_index[entity_type].items():
                if query in entity:
                    weight = 0.5 if entity_type == 'keywords' else 1.0
                    
                    for doc_id in doc_ids:
                        if doc_id not in matching_docs:
                            matching_docs[doc_id] = {
                                'score': 0,
                                'details': {}
                            }
                        
                        matching_docs[doc_id]['score'] += weight
                        
                        if entity_type not in matching_docs[doc_id]['details']:
                            matching_docs[doc_id]['details'][entity_type] = []
                        
                        if entity not in matching_docs[doc_id]['details'][entity_type]:
                            matching_docs[doc_id]['details'][entity_type].append(entity)
        
        # 处理匹配结果
        for doc_id, match_info in matching_docs.items():
            try:
                basic_info = get_info(int(doc_id))
                if 'keywords' in match_info['details']:
                    match_info['details']['keywords'] = match_info['details']['keywords'][:10]
                results.append({
                    "doc_id": int(doc_id),
                    "match_score": round(match_info['score'], 2),
                    "match_details": match_info['details'],
                    "basic_info": basic_info
                })
            except Exception as e:
                print(f"处理文档 {doc_id} 时出错: {str(e)}")
                continue

        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return jsonify({
            "query": query,
            "type": info_type,
            "total": len(results),
            "results": results[:50],  # 限制返回结果数量
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500
    
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
    # print(data)
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