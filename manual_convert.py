import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANUAL_DIR = os.path.join(BASE_DIR, "data", "manual")
SAVE_PATH = os.path.join(BASE_DIR, "data", "raw", "manual_data.jsonl")

os.makedirs(MANUAL_DIR, exist_ok=True)

EXTS = {".txt", ".eps"}

results = []
for fname in os.listdir(MANUAL_DIR):
    ext = os.path.splitext(fname)[1].lower()
    if ext in EXTS:
        fpath = os.path.join(MANUAL_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            title = os.path.splitext(fname)[0].replace("_", " ")
            results.append({
                "title": title,
                "content": content,
                "comments": [],
                "url": ""
            })
            print(f"✅ {fname}: {len(content)}자")

with open(SAVE_PATH, "w", encoding="utf-8") as f:
    for item in results:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"\n🎉 총 {len(results)}개 변환 완료!")