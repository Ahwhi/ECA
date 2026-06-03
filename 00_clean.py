import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIRS = [
    os.path.join(BASE_DIR, "data", "raw"),
    os.path.join(BASE_DIR, "data", "processed"),
    os.path.join(BASE_DIR, "chromadb_store"),
]

print("🗑️  데이터 초기화 중...")
for d in DIRS:
    if os.path.exists(d):
        shutil.rmtree(d)
        os.makedirs(d)
        print(f"  ✅ {d} 비움")
    else:
        os.makedirs(d)
        print(f"  ✅ {d} 생성")

print("\n🎉 초기화 완료! 이제 크롤러 실행하면 돼요.")