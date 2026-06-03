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

# ChromaDB 초기화
client = chromadb.PersistentClient(path=CHROMA_DIR)

# 기존 컬렉션 있으면 삭제 후 재생성
try:
    client.delete_collection("eud_docs")
except:
    pass
collection = client.create_collection("eud_docs")

# 문서 로딩
docs = []
with open(os.path.join(PROCESSED_DIR, "eud_docs.jsonl"), "r", encoding="utf-8") as f:
    for line in f:
        try:
            docs.append(json.loads(line))
        except:
            pass

print(f"📄 문서 {len(docs)}개 로딩 완료")
print("🔢 벡터화 중...")

# 배치로 임베딩
texts = [doc["text"][:1000] for doc in docs]  # 너무 길면 앞 1000자만
embeddings = model.encode(texts, show_progress_bar=True)

# ChromaDB에 저장
collection.add(
    ids=[str(i) for i in range(len(docs))],
    embeddings=embeddings.tolist(),
    documents=texts,
    metadatas=[{
        "title": doc["title"],
        "url": doc["url"],
        "source": doc["source"]
    } for doc in docs]
)

print(f"\n🎉 벡터화 완료! {len(docs)}개 문서 → ChromaDB 저장됨")
print(f"   저장 위치: {CHROMA_DIR}")