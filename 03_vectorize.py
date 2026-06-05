import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
CHROMA_DIR = os.path.join(BASE_DIR, "chromadb_store")

print("📦 임베딩 모델 로딩 중...")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("✅ 모델 로딩 완료!")

client = chromadb.PersistentClient(path=CHROMA_DIR)

try:
    client.delete_collection("eud_docs")
except:
    pass
collection = client.create_collection("eud_docs")

docs = []
with open(os.path.join(PROCESSED_DIR, "eud_docs.jsonl"), "r", encoding="utf-8") as f:
    for line in f:
        try:
            docs.append(json.loads(line))
        except:
            pass

print(f"📄 문서 {len(docs)}개 로딩 완료")
print("🔢 벡터화 중...")

texts = [doc["text"][:1000] for doc in docs]
embeddings = model.encode(texts, show_progress_bar=True)

# ChromaDB 최대 배치 5461 이하로 나눠서 저장
CHROMA_BATCH = 5000
total = len(docs)
for start in range(0, total, CHROMA_BATCH):
    end = min(start + CHROMA_BATCH, total)
    collection.add(
        ids=[str(i) for i in range(start, end)],
        embeddings=embeddings[start:end].tolist(),
        documents=texts[start:end],
        metadatas=[{
            "title": docs[i]["title"],
            "url":   docs[i]["url"],
            "source": docs[i]["source"]
        } for i in range(start, end)]
    )
    print(f"  저장 완료: {end}/{total}")

print(f"\n🎉 벡터화 완료! {total}개 문서 → ChromaDB 저장됨")
print(f"   저장 위치: {CHROMA_DIR}")