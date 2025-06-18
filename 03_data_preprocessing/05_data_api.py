import os
import json
import re
import requests
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────
# 1) 환경변수 로드
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY 환경 변수를 먼저 설정하세요.")


# ──────────────────────────────────────────────────────
# 2) 한국어 판별 함수
def is_korean(text: str) -> bool:
    """문장에 완성된 한글이 하나라도 포함되었으면 True 반환"""
    return bool(re.search(r"[가-힣]", text))


# ──────────────────────────────────────────────────────
# 3) 요약 및 번역 함수 (최대 2000 tokens)
def summarize_and_translate(text: str, is_korean_text: bool) -> str:
    """
    - is_korean_text == False: 한국어로 번역 후 2000 tokens 이하로 요약, 원문 어투 유지
    - is_korean_text == True: 그대로 한국어 2000 tokens 이하로 요약, 원문 어투 유지
    """
    if is_korean_text:
        prompt = f"""
너는 지금부터 모든 이공계 분야에 정통한 박사야.
다음 한국어 내용을 이해한 후에, 사람에게 직접 설명하듯이 원문의 어투를 최대한 유지하면서 2000 tokens 이내로 생성해줘.
생성할 내용은 공학, 이학, 의학, 약학, 물리학, 화학, 생물학, 지구과학, 천체학, 우주학, 항공학, 수생학, 지질학, 
공룡학, 동물학, 인류학, 심리학, 뇌과학, 인지과학, 컴퓨터 과학, 전자공학, 화학공학, 데이터 과학, 인공지능 등 
매우 넓은 범위에서의 과학/기술/학문 분야 주제에 집중해야하고, 특정 인물에 대한 명칭은 전부 제외해줘.

\"\"\"{text}\"\"\"
"""
    else:
        prompt = f"""
너는 지금부터 모든 이공계 분야에 정통한 박사야.
다음 내용을 이해한 후에, 한국어로 번역하고 사람에게 직접 설명하듯이 원문의 어투를 최대한 유지하면서 2000 tokens 이내로 생성해줘.
생성할 내용은 공학, 이학, 의학, 약학, 물리학, 화학, 생물학, 지구과학, 천체학, 우주학, 항공학, 수생학, 지질학, 
공룡학, 동물학, 인류학, 심리학, 뇌과학, 인지과학, 컴퓨터 과학, 전자공학, 화학공학, 데이터 과학, 인공지능 등 
매우 넓은 범위에서의 과학/기술/학문 분야 주제에 집중해야하고, 특정 인물에 대한 명칭은 전부 제외해줘.

\"\"\"{text}\"\"\"
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }
    body = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
    resp.raise_for_status()
    summary = resp.json()["choices"][0]["message"]["content"].strip()
    return summary


# ──────────────────────────────────────────────────────
# 4) Input 생성 함수 (48 tokens 이하)
def generate_input_prompt(summary: str) -> str:
    """
    요약된 output을 바탕으로,
    최대 48 tokens 이내의 한국어 반말(질문, 요청, 지시, 명령) 형태의 input을 생성
    """
    prompt = f"""
너는 지금부터 모든 이공계 분야에 정통한 박사야.
다음 한국어 내용을 이해한 후에, 매우 넓은 범위에서의 과학/기술/학문 분야 주제 핵심 단어에 집중해서 48 tokens 이내의 하나의 한국어 문장으로 생성해줘.
생성할 문장은 질문, 요청, 지시, 명령 형태 중 하나의 반말이어야하고, 순서대로 겹치지 않도록 바꿔가면서 생성해야 해.

요약:
\"\"\"{summary}\"\"\"
"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }
    body = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
    resp.raise_for_status()
    generated = resp.json()["choices"][0]["message"]["content"].strip()

    # 최대 48 tokens(단어)로 제한
    tokens = generated.split()
    if len(tokens) > 48:
        generated = " ".join(tokens[:48])
    return generated


# ──────────────────────────────────────────────────────
# 5) 전체 파이프라인 실행
def main():
    INPUT_FILE = "./02_data_preprocessing/06_filtered_scripts.jsonl"
    OUTPUT_FILE = "./02_data_preprocessing/07_api_scripts.jsonl"
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(INPUT_FILE, "r", encoding="utf-8") as fin, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as fout:

        for idx, line in enumerate(fin, start=1):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            output_text = rec.get("output", "").strip()
            if not output_text:
                continue

            # 5-1) 한국어 여부 판단
            korean_flag = is_korean(output_text)

            # 5-2) 요약 & (필요 시) 번역
            try:
                summary = summarize_and_translate(output_text, korean_flag)
            except Exception as e:
                print(f"[ERROR] Line {idx} 요약/번역 실패: {e}")
                continue

            # 5-3) input 생성 (48 tokens 이하)
            try:
                new_input = generate_input_prompt(summary)
            except Exception as e:
                print(f"[ERROR] Line {idx} input 생성 실패: {e}")
                continue

            # 5-4) 최종 레코드 작성
            new_rec = {
                "input": new_input,
                "output": summary
            }
            fout.write(json.dumps(new_rec, ensure_ascii=False) + "\n")
            print(f"[SAVE] Line {idx} 처리 완료")

    print(f">> 완료: '{OUTPUT_FILE}'에 저장되었습니다.")


if __name__ == "__main__":
    main()
