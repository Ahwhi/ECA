# ECA - EPS Code Assistant

스타크래프트 EUD/EPS 맵 제작 전문 AI 어시스턴트.
스타 에디터 아카데미(에닥) 네이버 카페의 실제 데이터를 기반으로 EUD/EPS 관련 질문에 답변합니다.

🔗 **서비스 주소**: https://huggingface.co/spaces/ahwhi/ECA

> 처음 접속 시 서버가 슬립 상태일 수 있어 로딩에 1~2분 소요될 수 있습니다.

---

## 기술 스택

### 데이터 수집
- **Selenium + undetected-chromedriver**: 네이버 카페 동적 페이지 크롤링 (iframe 구조 처리)
- **BeautifulSoup**: HTML 파싱 및 본문/댓글 추출
- **Naver Cafe API**: 특정 유저 글 목록 수집 (`CafeMemberNetworkArticleListV3`)
- 게시판 5개 + 핵심 유저 5명의 글 전량 수집, 총 **5,313개** 문서

### RAG 파이프라인
- **Sentence Transformers** (`paraphrase-multilingual-MiniLM-L12-v2`): 한/영 멀티링구얼 임베딩
- **ChromaDB**: 로컬 벡터 데이터베이스, 유사도 기반 문서 검색
- **RAG (Retrieval-Augmented Generation)**: 질문 벡터화 → 관련 문서 Top-3 검색 → LLM 컨텍스트 주입

### LLM & 백엔드
- **Groq API** (`llama-3.1-8b-instant`): 빠른 추론, 무료 플랜 사용
- **FastAPI + Uvicorn**: REST API 서버 (`/chat`, `/version` 엔드포인트)
- **Python-dotenv**: 환경변수 기반 API 키 관리

### 프론트엔드
- **순수 HTML/CSS/JS**: 별도 프레임워크 없이 구현
- ChatGPT/Claude 스타일 채팅 UI (다크 네온그린 테마)
- 마크다운/코드블록 렌더링, 버전 표시, 타이핑 애니메이션

### 배포
- **HuggingFace Spaces** (Docker SDK): 무료 클라우드 호스팅
- **Dockerfile** 기반 컨테이너 배포

---

## 학습 데이터

| 출처 | 수량 |
|------|------|
| 질문/답변 게시판 | 1,000개 |
| 강좌/팁 게시판 | 1,000개 |
| 연구/칼럼 게시판 | 215개 |
| Lua자료실 | 53개 |
| 유틸리티툴 게시판 | 356개 |
| 유저 크롤링 (5명) | 2,635개 |
| 수동 입력 (카페북 등) | 54개 |
| **합계** | **5,313개** |

- 출처: 스타 에디터 아카데미 네이버 카페 (club_id: 17046257)
- 글 본문 + 댓글 포함 학습
- 노이즈 제거 (UI 텍스트, 날짜, 조회수 등) 전처리 적용

---

## 프로젝트 구조

```
ECA/
├── 00_clean.py          # 데이터 초기화
├── 01_crawler.py        # 네이버 카페 크롤러
├── 02_preprocess.py     # 전처리 (노이즈 제거, 포맷 변환)
├── 03_vectorize.py      # ChromaDB 벡터화
├── 04_rag_chat.py       # 로컬 터미널 테스트용 (Ollama)
├── app.py               # FastAPI 서버 (배포용)
├── manual_convert.py    # 수동 데이터(txt) → jsonl 변환
├── static/
│   └── index.html       # 프론트엔드 UI
├── requirements.txt
├── Dockerfile
├── data/                # .gitignore 처리 (직접 크롤링 필요)
│   ├── raw/             # 크롤링 원본
│   ├── processed/       # 전처리 결과
│   └── manual/          # 수동 입력 txt 파일
└── chromadb_store/      # .gitignore 처리 (직접 벡터화 필요)
```

---

## 로컬 실행 방법

### 1. 필수 환경
- Python 3.11
- Chrome 브라우저 (크롤링 시)
- 네이버 계정 (카페 접근 권한)
- Groq API 키 ([발급](https://console.groq.com))

### 2. 설치

```bash
git clone https://github.com/Ahwhi/ECA.git
cd ECA
pip install -r requirements.txt
pip install selenium undetected-chromedriver beautifulsoup4
```

### 3. 환경변수 설정

`.env` 파일 생성:
```
GROQ_API_KEY=your_groq_api_key_here
```

### 4. 데이터 수집 파이프라인

```bash
# 기존 데이터 초기화 (선택)
py -3.11 00_clean.py

# 크롤링 (게시판/유저 설정은 01_crawler.py 상단에서 조정)
py -3.11 01_crawler.py

# 수동 데이터 추가 (선택) - data/manual/ 폴더에 .txt 파일 넣고 실행
py -3.11 manual_convert.py

# 전처리
py -3.11 02_preprocess.py

# 벡터화
py -3.11 03_vectorize.py
```

### 5. 서버 실행

```bash
py -3.11 app.py
```

브라우저에서 `http://localhost:7860` 접속

### 6. 터미널 테스트 (Ollama 사용 시)

```bash
# Ollama 설치 후 모델 다운로드
ollama pull qwen2.5-coder:7b

py -3.11 04_rag_chat.py
```

---

## 크롤러 설정

`01_crawler.py` 상단에서 조정:

```python
TEST_MODE = False      # True: 테스트 (소량), False: 전체 수집
RUN_BOARDS = True      # 게시판 크롤링 ON/OFF
RUN_USERS = True       # 유저 크롤링 ON/OFF
MAX_ARTICLES = 1000    # 게시판당 최대 수집량
```

유저 추가 시 프로필 URL에서 memberKey 추출:
```python
USERS = [
    {"name": "닉네임", "user_id": "프로필URL의_memberKey값"},
]
```

---

## 수동 데이터 추가 방법

카페북, 첨부파일 등 크롤링이 어려운 콘텐츠는 수동으로 추가 가능:

1. `data/manual/` 폴더에 `.txt` 파일 저장
2. 파일명이 제목으로 사용됨 (예: `EPS기술강의_1강.txt`)
3. 실행:

```bash
py -3.11 manual_convert.py
py -3.11 02_preprocess.py
py -3.11 03_vectorize.py
```

---

## 운영 비용

| 항목 | 비용 |
|------|------|
| HuggingFace Spaces 호스팅 | 무료 |
| Groq API (llama-3.1-8b-instant) | 무료 (하루 100만 토큰) |
| ChromaDB | 무료 |
| **합계** | **0원** |

> Groq 무료 플랜은 하루 토큰 한도가 있어 대용량 트래픽 발생 시 한도 초과될 수 있습니다.
> 한도 초과 시 서비스에서 안내 메시지가 표시되며, 매일 자정(UTC)에 초기화됩니다.

---

## 버전 히스토리

| 버전 | 내용 |
|------|------|
| v0.01 | 최초 배포, 게시판 데이터 2,624개 |
| v0.02 | 유저 크롤링 추가, 데이터 5,313개, 모델 llama-3.3-70b → 8b |
| v0.03 | Rate limit 오류 처리, 버전 표시 UI 추가 |
