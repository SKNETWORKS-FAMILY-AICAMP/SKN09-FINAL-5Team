import json
import re

# Function to check if a string contains any Korean characters
def is_all_english(text):
    # Returns True if no Korean character (Hangul syllables) is present
    return not bool(re.search(r'[\uac00-\ud7a3]', text))

file_path = "./02_data_preprocessing/06_filtered_scripts.jsonl"

# List to store line numbers with English-only outputs
english_only_lines = []

with open(file_path, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, start=1):
        try:
            data = json.loads(line)
            output_text = data.get("output", "")
            if output_text and is_all_english(output_text):
                english_only_lines.append(idx)
        except json.JSONDecodeError:
            continue

# Print the line numbers
print("영문만 있는 output들이 발견된 line numbers:")
for line_num in english_only_lines:
    print(line_num)
