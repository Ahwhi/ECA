import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)


def clean_text(text):
    # ===== 1단계: 카페 인기글 블록 이후 전부 제거 =====
    text = re.sub(r'전체글.*', '', text, flags=re.DOTALL)

    # ===== 2단계: "님의 게시글 더보기" 앞 닉네임 포함 제거 =====
    text = re.sub(r'\n.{1,30}\n님의 게시글 더보기', '', text)
    text = re.sub(r'.{1,30}님의 게시글 더보기', '', text)

    # ===== 3단계: 동영상 플레이어 UI 블록 제거 =====
    text = re.sub(
        r'0초\s*\n0초\s*\n100%.*?(?:더 알아보기|디버그 정보 다운로드)\s*\n?',
        '', text, flags=re.DOTALL
    )
    video_noise_patterns = [
        r'^재생 \(space/k\)\s*$', r'^재생\s*$', r'^음소거 \(m\)\s*$', r'^음소거\s*$',
        r'^전체 화면 \(f\)\s*$', r'^실시간\s*$', r'^설정\s*$',
        r'^자막 추가\s*$', r'^자막 설정\s*$', r'^글자 크기\s*$', r'^배경색\s*$',
        r'^사용 안함\s*$', r'^자막\s*$', r'^재생 속도\s*$',
        r'^0\.5x\s*$', r'^1\.0x \(기본\)\s*$', r'^1\.5x\s*$', r'^2\.0x\s*$',
        r'^1080p\s*$', r'^720p\s*$', r'^480p\s*$', r'^270p\s*$', r'^HD\s*$',
        r'^해상도\s*$', r'^라이선스\s*$', r'^subject\s*$', r'^author\s*$',
        r'^광고 후 계속됩니다\.\s*$', r'^다음 동영상\s*$',
        r'^죄송합니다\. 문제가 발생했습니다\. 다시 시도해 주세요\.\s*$',
        r'^도움말\s*$', r'^음소거 상태입니다\.\s*$',
        r'^고화질 재생이 가능한 영상입니다\.\s*$',
        r'^설정에서 해상도를 변경해보세요\.\s*$',
        r'^더 알아보기\s*$', r'^디버그 정보 다운로드\s*$',
        r'^\d{2}:\d{2}\s*$', r'^\d:\d{2}:\d{2}\s*$',
        r'^/\s*$', r'^\d+%\s*$', r'^\d+초\s*$',
    ]
    for pat in video_noise_patterns:
        text = re.sub(pat, '', text, flags=re.MULTILINE)

    # ===== 4단계: 유니코드 공백 제거 =====
    text = text.replace('\u200b', '')
    text = text.replace('\u00a0', ' ')
    text = text.replace('\u200c', '')
    text = text.replace('\u200d', '')
    text = text.replace('\ufeff', '')

    # ===== 5단계: (규칙) 공지 블록 + ※ 줄 제거 =====
    text = re.sub(r'\(규칙\)\n(?:.+\n){0,5}', '', text)
    text = re.sub(r'^※\s*.{5,80}$', '', text, flags=re.MULTILINE)

    # ===== [수정] 6단계: URL 처리 =====
    # http:///edac/12345 → https://cafe.naver.com/edac/12345 복원
    text = re.sub(r'https?:///edac/(\d+)', r'https://cafe.naver.com/edac/\1', text)
    # 그 외 https?:/// 잔재 제거
    text = re.sub(r'https?:///\S*', '', text)
    # 기존 naver 링크 제거
    text = re.sub(r'https?://naver\.me/\S+', '', text)
    text = re.sub(r'https?://m\.cafe\.naver\.com/\S+', '', text)
    text = re.sub(r'naver\.me\s*', '', text)
    text = re.sub(r'cafe\.naver\.com\s*', '', text)

    # ===== [신규] 7단계: [출처] 카페 UI 블록 제거 =====
    # "[출처]\n글제목 ([스에아]스타 에디터 아카데미...)\n| 작성자 XXX\nURL"
    text = re.sub(
        r'\[출처\]\n.{0,100}\([^)]*스에아[^)]*\)\n\| 작성자[^\n]*\n[^\n]*\n?',
        '', text
    )
    # 남은 "([스에아]스타 에디터 아카데미-스타크래프트 리마스터 대표 카페)" 라벨
    text = re.sub(r'\(\[스에아\][^)]*\)', '', text)
    text = re.sub(r'\[스에아\][^\n]*', '', text)

    # ===== [신규] 8단계: ,숫자 단독줄 제거 (조회수/추천수 잔재) =====
    # 예: ",151" ",070" ",260" → 숫자 앞 콤마가 붙은 단독줄
    text = re.sub(r'^\s*,\d+\s*$', '', text, flags=re.MULTILINE)

    # ===== 기존 noise 문자열 제거 =====
    noise = [
        "이전글", "다음글", "목록", "TOP", "전체보기", "페이징 이동",
        "URL 복사", "URL이 복사되었습니다. 원하는 곳에 붙여 넣으세요.",
        "카페 캘린더 레이어",
        "이 게시글을 카페 캘린더에서 제외하시겠습니까?",
        "이 게시글을 카페 캘린더에서 제외하시겠습",
        "이 게시글을 카페 캘린더에서", "이 게시글을",
        "카페 캘린더에서 제외하시겠습니까?",
        "이 게시글을 카페 캘린더로 보내시겠습니까?",
        "카페 캘린더로 보내시겠습니까?", "레이어팝업 닫기",
        "공유", "신고", "글쓰기", "새로고침", "답글쓰기", "등록순", "최신순",
        "구독", "1:1 채팅", "카페매니저", "카페스탭", "VIP 회원",
        "인기멤버", "감사회원", "우수회원I", "우수회원II",
        "카페회원I", "카페회원II", "카페회원III",
        "이 멤버의 글을 구독탭에서 볼 수 있습니다.",
        "이 멤버의 글을 탭에서 볼 수 있습니다.",
        "이 글을 '좋아요'한 멤버 리스트", "이 글을 ''한 멤버 리스트",
        "클린봇", "이 악성 댓글을 감지합니다.", "이 악성 을 감지합니다.",
        "새로운 댓글이 추가될 때 알림을 보내드립니다.",
        "댓글 알림 설정이 해제되었습니다.",
        "알림 새로운 이 추가될 때 알림을 보내드립니다.",
        "알림 설정", "댓글알림", "댓글을 입력하세요",
        "질문/답변 게시판", "강좌/팁 게시판", "연구/칼럼 게시판",
        "유즈맵 제작 강좌/팁", "자유＆잡담 게시판", "내가 만든 유즈맵",
        "Lua자료실", "유틸리티툴 게시판", "신고게시판(폐지)", "게시판(폐지)",
        "인강으로 배우는 eps", "유머＆정보 게시판", "유머＆잡담 게시판",
        "*.lua 자료실", "유틸리티/작업툴",
        "첨부파일 모아보기", "첨부파일",
        "내PC 저장", "네이버 MYBOX 저장", "네이버 MYBOX에 저장",
        "파일 다운로드", "내 컴퓨터 저장", "null 파일 다운로드", "null",
        "URL 복사", "스크랩", "말머리", "이 카페 인기글",
        "대한민국 모임의 시작, 네이버 카페",
    ]
    for n in noise:
        text = text.replace(n, "")

    # ===== 기존 정규식 패턴 제거 =====
    text = re.sub(r'\d{4}\.\d{2}\.\d{2}\.\s*\d{2}:\d{2}', '', text)
    text = re.sub(r'조회\s*[\d\.]+만?', '', text)
    text = re.sub(r'좋아요\s*\d+', '', text)
    text = re.sub(r'^댓글\s*\n?\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[(공지|중요|필독|조언|기초|트리거|EUD|스티커)\]', '', text)
    text = re.sub(r'^\s*>\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    for word in ['확인', '취소', '좋아요', '댓글', '등록', '알림', '답', '공지', '필독']:
        text = re.sub(rf'^{word}\s*$', '', text, flags=re.MULTILINE)

    # ===== 9단계: 간로 단독줄 제거 =====
    text = re.sub(r'\n간로\s*\n', '\n', text)
    text = re.sub(r'\n간로\s*$', '', text)

    # ===== 마무리: 공백/줄바꿈 정리 =====
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)

    return text.strip()


def remove_title_dup(text):
    """제목: XXX 바로 다음에 XXX가 반복되는 패턴 제거"""
    lines = text.split('\n')
    if len(lines) < 3:
        return text
    if not lines[0].startswith('제목:'):
        return text
    title_val = lines[0][3:].strip()  # "제목: " 제거
    # lines[1]은 빈줄, lines[2]가 제목 반복인지 확인
    if len(lines) > 2 and lines[1] == '' and lines[2].strip() == title_val:
        lines.pop(2)
        # lines[2]가 빈줄이면 하나 더 제거
        if len(lines) > 2 and lines[2] == '':
            lines.pop(2)
    return '\n'.join(lines)


def remove_author_nickname(text):
    """
    제목줄 바로 다음에 오는 작성자 닉네임 단독줄 제거.
    조건: 제목 → 빈줄 → 닉네임(2~15자, 한글/영문/숫자/일부특수문자) → 빈줄 → 본문
    false positive 방지: 다음줄이 빈줄일 때만 제거
    """
    lines = text.split('\n')
    if len(lines) < 5:
        return text
    if not lines[0].startswith('제목:'):
        return text
    if lines[1] != '':
        return text
    candidate = lines[2].strip()
    # 닉네임 조건: 2~15자, 한글/영문/숫자/밑줄/점/하이픈/공백만 허용, 다음줄이 빈줄
    if (2 <= len(candidate) <= 15
            and re.match(r'^[가-힣A-Za-z0-9_ .\-]+$', candidate)
            and len(lines) > 3 and lines[3] == ''):
        lines.pop(2)  # 닉네임줄 제거
        # 남은 빈줄 하나 제거
        if len(lines) > 2 and lines[2] == '':
            lines.pop(2)
    return '\n'.join(lines)


def remove_rank_label(text):
    """닉네임 뒤에 단독으로 오는 회원등급 라벨(I, II, III) 제거"""
    return re.sub(r'\n[IVX]{1,3}\n', '\n', text)


def fix_tokenized_code(text):
    """
    BeautifulSoup이 스마트에디터 코드블록을 토큰 단위로 줄바꿈한 것을 복원.
    패턴: 연속으로 짧은 토큰(≤10자)이 줄마다 하나씩 오는 구간을 한 줄로 합침.
    단, 코드 맥락이므로 공백으로 join (줄바꿈 제거).
    """
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        # 토큰줄 판별: 10자 이하, 코드에 나오는 문자들로만 구성
        if (0 < len(s) <= 10
                and re.match(r'^[a-zA-Z0-9가-힣_.()\[\]{},;+\-*/<>=!&|"\'\\@#$%^~?:]+$', s)):
            # 연속 토큰들을 수집
            token_group = [s]
            j = i + 1
            while j < len(lines):
                ns = lines[j].strip()
                if (0 < len(ns) <= 10
                        and re.match(r'^[a-zA-Z0-9가-힣_.()\[\]{},;+\-*/<>=!&|"\'\\@#$%^~?:]+$', ns)):
                    token_group.append(ns)
                    j += 1
                else:
                    break
            if len(token_group) >= 4:
                # 4개 이상 연속 토큰 → 한 줄로 합침
                result.append(' '.join(token_group))
                i = j
            else:
                result.append(line)
                i += 1
        else:
            result.append(line)
            i += 1
    return '\n'.join(result)


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

                # 조립 후 추가 정제
                text = remove_title_dup(text)
                text = remove_author_nickname(text)
                text = remove_rank_label(text)
                text = fix_tokenized_code(text)

                # 최종 공백 정리
                text = re.sub(r'\n{3,}', '\n\n', text)
                text = text.strip()

                results.append({
                    "title": title,
                    "text": text,
                    "url": url,
                    "source": os.path.basename(filepath)
                })
            except Exception:
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