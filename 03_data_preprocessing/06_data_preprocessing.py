import os
import json
import re

# 1) 입력/출력 파일 경로 설정
INPUT_FILE  = "./02_data_preprocessing/07_api_scripts.jsonl"
OUTPUT_FILE = "./02_data_preprocessing/08_preprocessed_scripts.jsonl"

def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    seen_outputs = set()
    with open(INPUT_FILE, "r", encoding="utf-8") as fin, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as fout:

        for line in fin:
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            # 원본 input/output 가져오기
            original_input = rec.get("input", "")
            output = rec.get("output", "")

            # 2-3) output 중복 체크: 이미 등장했다면 건너뜀
            if output in seen_outputs:
                continue
            seen_outputs.add(output)

            # 4) 라인별 공백 정리 (여러 공백을 단일 공백으로 축소, 양끝 공백 제거)
            cleaned_output = re.sub(r"\s+", " ", output).strip()
            cleaned_input  = re.sub(r"\s+", " ", original_input).strip()

            # 5) "\n\n--\n\n"을 공백으로 치환 (input에도 적용)
            cleaned_output = cleaned_output.replace("\n\n--\n\n", " ")
            cleaned_input  = cleaned_input.replace("\n\n--\n\n", " ")

            # 6) "\n\n"을 공백으로 치환 (input에도 적용)
            cleaned_output = cleaned_output.replace("\n\n", " ")
            cleaned_input  = cleaned_input.replace("\n\n", " ")

            # 7) '"'를 "'"로 치환 (input에도 적용)
            cleaned_output = cleaned_output.replace('"', "'")
            cleaned_input  = cleaned_input.replace('"', "'")

            # 최종 공백 정리 (다시 한 번 다중 공백 축소)
            cleaned_output = re.sub(r"\s+", " ", cleaned_output).strip()
            cleaned_input  = re.sub(r"\s+", " ", cleaned_input).strip()

            # 8) 새로운 레코드 작성 및 저장
            new_rec = {
                "input": cleaned_input,
                "output": cleaned_output
            }
            fout.write(json.dumps(new_rec, ensure_ascii=False) + "\n")

    print(f">> 완료: '{OUTPUT_FILE}' 생성됨")

if __name__ == "__main__":
    main()
