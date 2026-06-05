import time
import json
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "data", "raw")

BOARDS = [
    {"name": "질문답변",   "club_id": "17046257", "menu_id": "12"},
    {"name": "강좌팁",     "club_id": "17046257", "menu_id": "15"},
    {"name": "연구칼럼",   "club_id": "17046257", "menu_id": "33"},
    {"name": "Lua자료실",  "club_id": "17046257", "menu_id": "229"},
    {"name": "유틸리티툴", "club_id": "17046257", "menu_id": "20"},
]

USERS = [
    {"name": "맛있는 빙수", "user_id": "KggGRL--m4a28j3uXd7gvR-UEevzwge-RrkqJZN988I"},
    {"name": "Artanis",     "user_id": "hWpGswcDorhRgesdQnm2KoHlhV6WYHirufoukvMy-3M"},
    {"name": "갈대",        "user_id": "t_GfKGGw_V1LHpvClKJoDGrdVtaLhS3P50vI9Y_5Aww"},
    {"name": "Dtime",       "user_id": "f1IIk3vZb6HwA9oWI-fxG0dQHwFQnBP4SsPzgXfJ20M"},
    {"name": "버터쿠키",    "user_id": "DGJd9EeMNeJUF2hsgJkRQAZgu8kLN7aJRJM_m54ELns"},
]

TEST_MODE = False
TEST_MAX_PAGES = 2
TEST_MAX_ARTICLES = 3
MAX_ARTICLES = 10000

RUN_BOARDS = True
RUN_USERS = True

def make_driver():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-images")
    options.add_argument("--blink-settings=imagesEnabled=false")
    driver = uc.Chrome(options=options, version_main=148)
    driver.set_page_load_timeout(20)
    return driver

def naver_login(driver):
    print("🔐 네이버 로그인 페이지 열기...")
    driver.get("https://naver.com")
    time.sleep(2)
    print("=" * 50)
    print("👆 열린 Chrome 창에서 직접 로그인해주세요!")
    print("   로그인 완료 후 여기서 Enter 누르세요")
    print("=" * 50)
    input("로그인 완료 후 Enter ▶ ")
    print("✅ 로그인 확인!")
    return True

def enter_iframe(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "cafe_main"))
        )
        return True
    except:
        return False

def get_article_ids_from_board(driver, club_id, menu_id, ids_cache_path=None, max_pages=999):
    article_ids = []
    actual_max = TEST_MAX_PAGES if TEST_MODE else max_pages

    for page in range(1, actual_max + 1):
        url = (
            f"https://cafe.naver.com/f-e/cafes/{club_id}/menus/{menu_id}"
            f"?page={page}"
        )
        driver.get(url)
        time.sleep(2)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.article"))
            )
        except:
            print(f"  {page}페이지: 글 없음 → 종료")
            break

        links = driver.find_elements(By.CSS_SELECTOR, "a.article")
        if not links:
            print(f"  {page}페이지: 글 없음 → 종료")
            break

        found = 0
        for link in links:
            href = link.get_attribute("href") or ""
            aid = None
            if f"menuid={menu_id}" not in href:
                continue
            if "articleid=" in href:
                aid = href.split("articleid=")[1].split("&")[0]
            elif "/articles/" in href:
                part = href.split("/articles/")[1].split("?")[0].split("/")[0]
                if part.isdigit():
                    aid = part
            if aid and aid not in article_ids:
                article_ids.append(aid)
                found += 1

        print(f"  {page}페이지: {found}개 발견 (누적 {len(article_ids)}개)")

        if ids_cache_path:
            with open(ids_cache_path, "w", encoding="utf-8") as f:
                for aid in article_ids:
                    f.write(aid + "\n")

        if found == 0:
            break
        time.sleep(0.5)

    return article_ids

def get_user_article_ids(driver, club_id, user_id, ids_cache_path=None):
    article_ids = []
    actual_max = TEST_MAX_PAGES if TEST_MODE else 999

    cookies = {c['name']: c['value'] for c in driver.get_cookies()}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"https://cafe.naver.com/f-e/cafes/{club_id}/members/{user_id}",
    }

    for page in range(1, actual_max + 1):
        url = (
            f"https://apis.naver.com/cafe-web/cafe-mobile/CafeMemberNetworkArticleListV3"
            f"?search.cafeId={club_id}&search.memberKey={user_id}"
            f"&search.perPage=15&search.page={page}&requestFrom=A"
        )

        try:
            res = requests.get(url, cookies=cookies, headers=headers, timeout=10)
            data = res.json()
            articles = data.get("message", {}).get("result", {}).get("articleList", [])
        except Exception as e:
            print(f"  {page}페이지: API 오류 → {e}")
            break

        if not articles:
            print(f"  {page}페이지: 글 없음 → 종료")
            break

        found = 0
        for article in articles:
            aid = str(article.get("articleid", ""))
            if aid and aid not in article_ids:
                article_ids.append(aid)
                found += 1

        print(f"  {page}페이지: {found}개 발견 (누적 {len(article_ids)}개)")

        if ids_cache_path:
            with open(ids_cache_path, "w", encoding="utf-8") as f:
                for aid in article_ids:
                    f.write(aid + "\n")

        if found == 0:
            break
        time.sleep(0.2)

    return article_ids

def get_article_content(driver, club_id, article_id):
    url = f"https://cafe.naver.com/f-e/cafes/{club_id}/articles/{article_id}"
    try:
        driver.get(url)
    except:
        pass
    time.sleep(1)

    if not enter_iframe(driver, timeout=10):
        return None

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                ".ArticleContainerWrap, .article_wrap"))
        )
    except:
        pass

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.switch_to.default_content()

    title_el = (
        soup.select_one(".title_text") or
        soup.select_one("h3.title") or
        soup.select_one(".se-title-text")
    )
    title = title_el.get_text(strip=True) if title_el else ""

    content_el = (
        soup.select_one(".ArticleContainerWrap") or
        soup.select_one(".article_wrap") or
        soup.select_one(".se-main-container") or
        soup.select_one(".article_container") or
        soup.select_one("#tbody")
    )
    content = content_el.get_text(separator="\n", strip=True) if content_el else ""

    comments = []
    for sel in [".comment_text_box", ".text_comment", ".CommentItem .text"]:
        els = soup.select(sel)
        if els:
            comments = [e.get_text(strip=True) for e in els if e.get_text(strip=True)]
            break

    if not title and not content:
        return None

    return {
        "article_id": article_id,
        "title": title,
        "content": content,
        "comments": comments,
        "url": url
    }

def crawl_board(driver, board, global_done_ids=None):
    name = board["name"]
    club_id = board["club_id"]
    menu_id = board["menu_id"]
    save_path = os.path.join(SAVE_DIR, f"board_{name}.jsonl")
    ids_cache_path = save_path + ".ids"

    done_ids = set()
    if os.path.exists(save_path):
        with open(save_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    done_ids.add(str(json.loads(line)["article_id"]))
                except:
                    pass

    if global_done_ids:
        done_ids = done_ids | global_done_ids

    print(f"\n📋 [{name}] 글 목록 수집 중...")

    if os.path.exists(ids_cache_path):
        with open(ids_cache_path, "r", encoding="utf-8") as f:
            article_ids = [line.strip() for line in f if line.strip()]
        print(f"  📂 캐시에서 {len(article_ids)}개 ID 불러옴")
    else:
        article_ids = get_article_ids_from_board(driver, club_id, menu_id, ids_cache_path)

    new_ids = [aid for aid in article_ids if aid not in done_ids]
    limit = TEST_MAX_ARTICLES if TEST_MODE else MAX_ARTICLES
    new_ids = new_ids[:limit]

    if TEST_MODE:
        print(f"  🧪 테스트 모드: {limit}개만 수집")
    print(f"  전체 {len(article_ids)}개 중 {len(new_ids)}개 수집 시작")

    with open(save_path, "a", encoding="utf-8") as f:
        for i, aid in enumerate(new_ids):
            try:
                data = get_article_content(driver, club_id, aid)
                if data and data["content"]:
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
                    if global_done_ids is not None:
                        global_done_ids.add(aid)
                    print(f"  [{i+1}/{len(new_ids)}] ✅ {data['title'][:40]}")
                    print(f"         본문 {len(data['content'])}자 / 댓글 {len(data['comments'])}개")
                else:
                    print(f"  [{i+1}/{len(new_ids)}] ⚠️  내용 없음 (id={aid})")
            except Exception as e:
                print(f"  [{i+1}/{len(new_ids)}] ❌ 오류: {e}")
            time.sleep(0.3)

    if os.path.exists(ids_cache_path):
        os.remove(ids_cache_path)
        print(f"  🗑️  ID 캐시 파일 삭제")

    print(f"✅ [{name}] 완료! → {save_path}")

def crawl_user(driver, user, global_done_ids=None):
    name = user["name"]
    save_path = os.path.join(SAVE_DIR, f"user_{name}.jsonl")
    ids_cache_path = save_path + ".ids"

    done_ids = set()
    if os.path.exists(save_path):
        with open(save_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    done_ids.add(str(json.loads(line)["article_id"]))
                except:
                    pass

    if global_done_ids:
        done_ids = done_ids | global_done_ids

    print(f"\n👤 [{name}] 유저 글 수집 중...")

    if os.path.exists(ids_cache_path):
        with open(ids_cache_path, "r", encoding="utf-8") as f:
            article_ids = [line.strip() for line in f if line.strip()]
        print(f"  📂 캐시에서 {len(article_ids)}개 ID 불러옴")
    else:
        article_ids = get_user_article_ids(driver, "17046257", user["user_id"], ids_cache_path)

    new_ids = [aid for aid in article_ids if aid not in done_ids]
    limit = TEST_MAX_ARTICLES if TEST_MODE else 9999
    new_ids = new_ids[:limit]

    if TEST_MODE:
        print(f"  🧪 테스트 모드: {limit}개만 수집")
    print(f"  전체 {len(article_ids)}개 중 {len(new_ids)}개 수집 시작")

    with open(save_path, "a", encoding="utf-8") as f:
        for i, aid in enumerate(new_ids):
            try:
                data = get_article_content(driver, "17046257", aid)
                if data and data["content"]:
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
                    if global_done_ids is not None:
                        global_done_ids.add(aid)
                    print(f"  [{i+1}/{len(new_ids)}] ✅ {data['title'][:40]}")
                    print(f"         본문 {len(data['content'])}자 / 댓글 {len(data['comments'])}개")
                else:
                    print(f"  [{i+1}/{len(new_ids)}] ⚠️  내용 없음 (id={aid})")
            except Exception as e:
                print(f"  [{i+1}/{len(new_ids)}] ❌ 오류: {e}")
            time.sleep(0.3)

    if os.path.exists(ids_cache_path):
        os.remove(ids_cache_path)
        print(f"  🗑️  ID 캐시 파일 삭제")

    print(f"✅ [{name}] 완료! → {save_path}")

# ==================== 메인 ====================
if __name__ == "__main__":
    print(f"{'🧪 테스트 모드' if TEST_MODE else '🚀 본격 수집 모드'}")
    print(f"  게시판: {'ON' if RUN_BOARDS else 'OFF'} / 유저: {'ON' if RUN_USERS else 'OFF'}")

    driver = make_driver()
    global_done_ids = set()

    try:
        naver_login(driver)

        if RUN_BOARDS:
            for board in BOARDS:
                crawl_board(driver, board, global_done_ids)

        if RUN_USERS:
            for user in USERS:
                crawl_user(driver, user, global_done_ids)

    except KeyboardInterrupt:
        print("\n⏹️ 중단됨 (수집된 데이터와 ID 캐시는 저장되어 있어요)")
    finally:
        driver.quit()
        print("\n🏁 크롤링 완료!")