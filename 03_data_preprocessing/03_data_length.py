import os
import json

# === 설정 ===
INPUT_FILE    = "./02_data_preprocessing/07_api_scripts.jsonl" # 05_cleaned_scripts
FILTERED_FILE = "./02_data_preprocessing/08_temp_scripts.jsonl" # 06_filtered_scripts
MIN_LENGTH    = 900  # output 길이 기준

def print_output_lengths(path):
    """각 라인의 output 길이를 원본 그대로 계산해 출력합니다."""
    with open(path, 'r', encoding='utf-8') as fin:
        for idx, line in enumerate(fin, start=1):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            output = rec.get('output', '')
            print(f"Line {idx}: output length = {len(output)}")

def filter_by_length(input_path, output_path, min_len):
    """output 길이가 min_len 이상인 레코드만 남기고 나머지는 버립니다.
       데이터는 전혀 수정하지 않고, 원본 JSON 라인을 그대로 출력합니다."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:
        for line in fin:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            output = rec.get('output', '')
            if len(output) < min_len:
                continue
            # 길이 조건을 만족하는 경우, 원본 라인 그대로 기록
            fout.write(line)

if __name__ == "__main__":
    # 1) 모든 라인의 output 길이 출력
    print_output_lengths(INPUT_FILE)
    # 2) 길이가 MIN_LENGTH 이상인 레코드만 필터링
    filter_by_length(INPUT_FILE, FILTERED_FILE, MIN_LENGTH)
    print(f">> 완료: output 길이 ≥ {MIN_LENGTH}인 레코드가 '{FILTERED_FILE}'에 저장되었습니다.")
