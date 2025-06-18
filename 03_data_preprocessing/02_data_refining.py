import os
import json
import re

# === 정제 함수 ===
def clean_text(text: str) -> str:
    # 1. 줄바꿈 제거
    text = text.replace("\n", " ")
    # 2. 따옴표 제거
    text = text.replace('\\"', '').replace('"', '')
    # 3. 대괄호 및 소괄호 안 텍스트 제거
    text = re.sub(r"\s?\[[^\]]*\]\s?", "", text)
    text = re.sub(r"\s?\([^\)]*\)\s?", "", text)
    # 4. 해시태그 제거
    text = re.sub(r"#\S+", "", text)
    # 5. 불필요 기호 제거
    for ch in [':',';','|','│','※','“','(',')','[',']','-','_','<','>']:
        text = text.replace(ch, '')
    # 6. 영어 소문자 → 대문자
    text = re.sub(r"[a-z]", lambda m: m.group(0).upper(), text)
    # 7. 다중 공백 정리
    text = re.sub(r"\s+", " ", text).strip()
    return text

# === 메인 순차 실행 ===
def main():
    # 파일 경로 설정
    INPUT_FILE      = "./02_data_preprocessing/01_youtube_scripts.jsonl"
    DEDUP_INPUT     = "./02_data_preprocessing/02_dedup_input.jsonl"
    DEDUP_OUTPUT    = "./02_data_preprocessing/03_dedup_output.jsonl"
    REFINED_FILE    = "./02_data_preprocessing/04_refined_scripts.jsonl"
    FINAL_FILE      = "./02_data_preprocessing/05_cleaned_scripts.jsonl"

    os.makedirs(os.path.dirname(FINAL_FILE), exist_ok=True)

    # 1. input 중복 제거 (맨 처음만 남김)
    seen_inputs = set()
    with open(INPUT_FILE, 'r', encoding='utf-8') as fin, \
         open(DEDUP_INPUT, 'w', encoding='utf-8') as f1:
        for line in fin:
            rec = json.loads(line)
            inp = rec.get('input', '')
            if inp in seen_inputs:
                continue
            seen_inputs.add(inp)
            f1.write(line)

    # 2. output 중복 제거 (맨 처음만 남김)
    seen_outputs = set()
    with open(DEDUP_INPUT, 'r', encoding='utf-8') as fin, \
         open(DEDUP_OUTPUT, 'w', encoding='utf-8') as f2:
        for line in fin:
            rec = json.loads(line)
            out = rec.get('output', '')
            if out in seen_outputs:
                continue
            seen_outputs.add(out)
            f2.write(line)

    # 3. 정제 함수 실행 (clean_text 적용)
    with open(DEDUP_OUTPUT, 'r', encoding='utf-8') as fin, \
         open(REFINED_FILE, 'w', encoding='utf-8') as f3:
        for line in fin:
            rec = json.loads(line)
            rec['input']  = clean_text(rec.get('input', ''))
            rec['output'] = clean_text(rec.get('output', ''))
            f3.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # 4. 모든 input 내용을 빈 문자열로 설정
    with open(REFINED_FILE, 'r', encoding='utf-8') as fin, \
         open(FINAL_FILE, 'w', encoding='utf-8') as fout:
        for line in fin:
            rec = json.loads(line)
            rec['input'] = ""
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f">> 완료: 최종 파일 생성됨 -> {FINAL_FILE}")

if __name__ == '__main__':
    main()
