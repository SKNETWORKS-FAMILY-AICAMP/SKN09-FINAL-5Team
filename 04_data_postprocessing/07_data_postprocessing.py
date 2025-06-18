import json
import os

# 원본 파일 경로
input_file_path = "./data/08_preprocessed_scripts.jsonl"
# 클린된 파일을 저장할 경로 (새 파일)
output_file_path = "./data/09_postprocessed_scripts.jsonl"

print(f"--- 데이터셋 파일 유효성 검사 및 클리닝 시작: {input_file_path} ---")

valid_lines_count = 0
invalid_lines_count = 0

# 'errors="ignore"'를 사용하여 인코딩 오류가 있는 바이트를 무시하고 파일을 읽습니다.
# 이렇게 하면 UnicodeDecodeError를 피하고, 이후 JSON 파싱 단계에서 유효성 검사를 수행합니다.
with open(input_file_path, 'r', encoding='utf-8', errors='ignore') as infile, \
     open(output_file_path, 'w', encoding='utf-8') as outfile: # 출력 파일은 항상 UTF-8로 깨끗하게 작성
    for line_num, line in enumerate(infile, 1):
        try:
            # 각 줄이 유효한 JSON인지 시도
            # .strip()을 사용하여 앞뒤 공백 및 개행 문자를 제거합니다.
            json_obj = json.loads(line.strip())
            # 유효한 JSON이면 새 파일에 다시 쓰기
            # ensure_ascii=False는 한글과 같은 비-ASCII 문자를 그대로 UTF-8로 저장하게 합니다.
            outfile.write(json.dumps(json_obj, ensure_ascii=False) + '\n')
            valid_lines_count += 1
        except json.JSONDecodeError as e:
            # JSON 디코딩 오류 발생 시
            print(f"경고: {input_file_path} 파일의 {line_num}번째 줄에서 JSON 파싱 오류 발생: {e}")
            print(f"  오류 줄 내용 (일부): {line.strip()[:200]}...") # 오류 줄의 일부를 출력
            invalid_lines_count += 1
        except Exception as e:
            # 기타 예상치 못한 오류 발생 시
            print(f"경고: {input_file_path} 파일의 {line_num}번째 줄에서 알 수 없는 오류 발생: {e}")
            print(f"  오류 줄 내용 (일부): {line.strip()[:200]}...")
            invalid_lines_count += 1

print(f"\n--- 데이터셋 클리닝 완료 ---")
print(f"총 유효한 줄 수: {valid_lines_count}")
print(f"총 유효하지 않은 줄 수 (건너뜀): {invalid_lines_count}")
print(f"클린된 파일이 다음 위치에 저장되었습니다: {output_file_path}")

# 다음으로 데이터셋을 로드할 때 이 클린된 파일을 사용하도록 경로를 업데이트합니다.
# 이 줄이 Jupyter 환경에서 FINETUNE_DATA_PATH 변수를 업데이트합니다.
try:
    # FINETUNE_DATA_PATH가 정의되어 있지 않을 수 있으므로 전역 변수로 선언
    global FINETUNE_DATA_PATH
except NameError:
    # FINETUNE_DATA_PATH가 정의되지 않은 경우 초기화 (Jupyter 환경에서 필요)
    pass # 이미 Jupyter Notebook에서는 변수 선언 시 자동으로 전역 범위가 됩니다.
FINETUNE_DATA_PATH = output_file_path
print(f"FINETUNE_DATA_PATH 변수가 '{FINETUNE_DATA_PATH}'로 업데이트되었습니다.")
