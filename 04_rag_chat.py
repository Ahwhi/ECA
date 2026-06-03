import chromadb
from sentence_transformers import SentenceTransformer
import ollama

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chromadb_store")

print("🚀 EUD AI 로딩 중...")

# 모델 & DB 로딩
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_collection("eud_docs")

print("✅ 준비 완료! 질문을 입력하세요 (종료: q)")
print("=" * 50)

def ask(question):
    # 1. 질문 벡터화
    q_embedding = model.encode([question])[0].tolist()

    # 2. 관련 문서 검색
    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=3
    )

    # 3. 컨텍스트 구성
    context = ""
    for i, (doc, meta) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0]
    )):
        context += f"[참고{i+1}] {meta['title']}\n{doc}\n\n"

    # 4. Ollama에 질문
    prompt = f"""당신은 스타크래프트 EUD 맵 제작 전문 AI입니다.
아래 참고 자료를 바탕으로 질문에 답변해주세요.
참고 자료에 없는 내용은 모른다고 하세요.

[참고 자료]
{context}

[질문]
{question}

[답변]"""

    print("\n🤖 답변 생성 중...\n")
    response = ollama.chat(
        model="qwen2.5-coder:7b",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response["message"]["content"]
    print(f"💬 {answer}")
    print("\n📚 참고 문서:")
    for meta in results["metadatas"][0]:
        print(f"  - {meta['title']} ({meta['source']})")
    print("=" * 50)

# 채팅 루프
while True:
    question = input("\n❓ 질문: ").strip()
    if question.lower() in ["q", "quit", "exit", "종료"]:
        print("👋 종료합니다.")
        break
    if not question:
        continue
    ask(question)