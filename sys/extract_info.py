import os
import json
import re
import spacy

nlp = spacy.load("en_core_web_sm")  # 下载模型：python -m spacy download en_core_web_sm

DATA_DIR = 'IMDB\source'
OUTPUT_FILE = 'json\extracted_info.json'

def extract_info_from_text(lines):
    info = {}
    try:
        info['title'] = lines[0].strip()
        info['rate'] = lines[1].strip().replace('rate: ', '')
        info['director'] = lines[2].strip()
        info['writers'] = [w.strip() for w in lines[3].split('/') if w.strip()]
        info['stars'] = [s.strip() for s in lines[4].split('/') if s.strip()]
        info['summary'] = lines[5].strip() if len(lines) > 5 else ""
        info['url'] = lines[6].strip().replace('url: ', '') if len(lines) > 6 else ""
    except IndexError:
        print("数据格式错误：", lines)
        return None

    # 从简介中抽关键词和实体
    doc = nlp(info['summary'])
    
    # 关键词（从名词、动词、形容词中挑选前N个）
    keywords = [token.lemma_ for token in doc if token.pos_ in ['NOUN', 'VERB', 'ADJ'] and not token.is_stop]
    keywords = list(set(keywords))[:10]

    # 实体识别
    persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    locations = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]]

    info['extracted'] = {
        'keywords': keywords,
        'persons': list(set(persons)),
        'organizations': list(set(orgs)),
        'locations': list(set(locations))
    }
    return info

def process_all_documents():
    extracted_data = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.txt'):
            with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
                lines = f.readlines()
                info = extract_info_from_text(lines)
                if info:
                    extracted_data.append(info)
    return extracted_data

def main():
    all_data = process_all_documents()
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"抽取完成，共处理 {len(all_data)} 篇文档。结果已保存至 {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
