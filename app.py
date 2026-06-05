from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
import uvicorn
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHROMA_DIR = "./chromadb_store"
MODEL_NAME = "llama-3.1-8b-instant"
VERSION = "v0.04"

print("🚀 ECA 로딩 중...")
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_collection("eud_docs")
groq_client = Groq(api_key=GROQ_API_KEY)
print("✅ 로딩 완료!")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    message: str
    history: list = []

def search_docs(query, n=3):
    embedding = embedding_model.encode([query])[0].tolist()
    results = collection.query(query_embeddings=[embedding], n_results=n)
    docs = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        docs.append({"text": doc, "title": meta["title"], "url": meta["url"]})
    return docs

@app.get("/version")
def version():
    return {"version": VERSION}

@app.post("/chat")
def chat(req: ChatRequest):
    docs = search_docs(req.message)
    context = ""
    for i, doc in enumerate(docs):
        context += f"[참고{i+1}] {doc['title']}\n{doc['text'][:800]}\n\n"

    system_prompt = """당신은 스타크래프트 EUD/EPS 맵 제작 전문 AI 어시스턴트 ECA입니다.
스타 에디터 아카데미 커뮤니티 데이터를 기반으로 답변합니다.

규칙:
1. 질문에만 정확하게 답변하세요. 묻지 않은 내용은 추가하지 마세요.
2. 참고 자료에 있는 내용만 답변하세요. 없으면 "해당 내용은 데이터에 없어서 잘 모르겠지만, 열심히 답변할게요."라고 한 후 최선을 다해 답변하세요.
3. 인사나 잡담에는 짧게 답하고 EUD/EPS 질문을 유도하세요.
4. 코드는 반드시 코드블록으로 작성하세요.
5. 불필요한 설명, 예시, 부연은 하지 마세요. 핵심만 답변하세요.
6. 구현하지 않은 함수와 변수는 구현 혹은 선언하고 한꺼번에 답변하세요.
7. 코드를 작성할때, 사용자의 별다른 조건이 없으면 Eud Editor3에서 사용하는 epScript언어로 가정하고 답변하세요.
8. 코드를 작성할때 사용할 변수는 코드 블럭에 포함해서 꼭 선언하세요."""

    messages = [{"role": "system", "content": system_prompt}]
    for h in req.history:
        messages.append({"role": "user", "content": h[0]})
        messages.append({"role": "assistant", "content": h[1]})
    messages.append({
        "role": "user",
        "content": f"[참고 자료]\n{context}\n\n[질문]\n{req.message}"
    })

    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=1024,
            temperature=0.3
        )
        answer = response.choices[0].message.content
    except Exception as e:
        err = str(e)
        if "rate_limit_exceeded" in err or "429" in err:
            answer = "⚠️ 현재 API 사용량 한도를 초과했어요. 잠시 후 다시 시도해주세요. (보통 자정에 초기화돼요)"
        else:
            answer = "⚠️ 오류가 발생했어요. 잠시 후 다시 시도해주세요."

    sources = "\n\n---\n📚 참고 문서\n"
    for doc in docs:
        sources += f"- {doc['title']} ({doc['url']})\n"

    return {"answer": answer + sources}

@app.get("/")
def index():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)