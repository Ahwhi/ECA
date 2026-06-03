import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

def clean_text(text):
    noise = [
        "이전글", "다음글", "목록", "URL 복사", "URL이 복사되었습니다. 원하는 곳에 붙여 넣으세요.",
        "카페 캘린더 레이어", "레이어팝업 닫기", "확인", "취소",
        "좋아요", "댓글", "공유", "신고", "글쓰기", "TOP",
        "이 카페 인기글", "페이징 이동", "전체보기", "새로고침",
        "클린봇", "댓글알림", "등록순", "최신순", "답글쓰기",
        "구독", "1:1 채팅", "카페매니저", "카페스탭", "VIP 회원",
        "이 멤버의 글을 구독탭에서 볼 수 있습니다.",
        "이 게시글을 카페 캘린더에서 제외하시겠습니까?",
        "이 게시글을 카페 캘린더에서 제외하시겠습",
        "이 게시글을 카페 캘린더에서",
        "이 게시글을",
        "카페 캘린더에서 제외하시겠습니까?",
        "질문/답변 게시판", "강좌/팁 게시판", "연구/칼럼 게시판",
        "Lua자료실", "유틸리티툴 게시판",
        "말머리", "인기멤버", "감사회원", "우수회원I", "우수회원II",
        "카페회원I", "카페회원II", "카페회원III",
        "조회", "URL 복사", "스크랩",
    ]
    for n in noise:
        text = text.replace(n, "")

    # 날짜 패턴 제거 (2026.06.03. 05:20 형태)
    text = re.sub(r'\d{4}\.\d{2}\.\d{2}\.\s*\d{2}:\d{2}', '', text)
    # 조회수 패턴 제거
    text = re.sub(r'조회\s*\d+', '', text)
    # 댓글수 패턴 제거
    text = re.sub(r'댓글\s*\d+', '', text)
    # 연속 공백/줄바꿈 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

def process_file(filepath):
    results = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                title = obj.get("title", "").strip()
                content = clean_text(obj.get("content", ""))
                comments = obj.get("comments", [])
                url = obj.get("url", "")

                if len(content) < 50:
                    continue

                text = f"제목: {title}\n\n{content}"

                if comments:
                    comment_text = "\n".join([f"- {c}" for c in comments if len(c) > 5])
                    if comment_text:
                        text += f"\n\n[댓글]\n{comment_text}"

                results.append({
                    "title": title,
                    "text": text,
                    "url": url,
                    "source": os.path.basename(filepath)
                })
            except:
                pass
    return results

all_docs = []
for fname in os.listdir(RAW_DIR):
    if fname.endswith(".jsonl"):
        fpath = os.path.join(RAW_DIR, fname)
        docs = process_file(fpath)
        all_docs.extend(docs)
        print(f"✅ {fname}: {len(docs)}개 처리")

out_path = os.path.join(PROCESSED_DIR, "eud_docs.jsonl")
with open(out_path, "w", encoding="utf-8") as f:
    for doc in all_docs:
        f.write(json.dumps(doc, ensure_ascii=False) + "\n")

print(f"\n🎉 전처리 완료! 총 {len(all_docs)}개 → {out_path}")