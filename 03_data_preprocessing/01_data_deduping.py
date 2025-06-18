import sys
import json

def dedupe_jsonl(input_path: str, output_path: str):
    seen_inputs = set()
    seen_outputs = set()

    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                # 유효하지 않은 JSON은 건너뜁니다
                continue

            inp = rec.get('input', '')
            out = rec.get('output', '')

            # input 또는 output이 이전에 등장했다면 건너뜁니다
            if inp in seen_inputs or out in seen_outputs:
                continue

            seen_inputs.add(inp)
            seen_outputs.add(out)
            fout.write(json.dumps(rec, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <input.jsonl> <output.jsonl>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    dedupe_jsonl(input_file, output_file)
    print(f">> 완료: 중복 제거된 파일이 '{output_file}'에 생성되었습니다.")
