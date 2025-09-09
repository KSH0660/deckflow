#!/usr/bin/env python3
"""
테스트 중에 생성된 불완전한 덱들을 정리하는 스크립트
"""

import requests

API_BASE = "http://localhost:8000/api"


def cleanup_test_decks():
    """테스트용 덱들을 정리합니다."""

    # 모든 덱 목록 조회
    print("🔍 덱 목록 조회 중...")
    response = requests.get(f"{API_BASE}/decks?limit=100")
    if response.status_code != 200:
        print(f"❌ 덱 목록 조회 실패: {response.status_code}")
        return

    decks = response.json()
    print(f"📊 총 {len(decks)}개 덱 발견")

    # 정리 대상 덱 필터링
    cleanup_candidates = []
    for deck in decks:
        # 테스트 제목이거나 generating 상태에 멈춘 덱들
        if (
            "test" in deck["title"].lower()
            or "Create a test presentation" in deck["title"]
            or (deck["status"] == "generating" and deck["slide_count"] == 0)
        ):
            cleanup_candidates.append(deck)

    print(f"🎯 정리 대상: {len(cleanup_candidates)}개")

    if not cleanup_candidates:
        print("✅ 정리할 덱이 없습니다.")
        return

    # 정리 대상 확인
    print("\n📋 정리할 덱 목록:")
    for deck in cleanup_candidates:
        print(
            f"  - {deck['deck_id'][:8]}... | {deck['status']} | {deck['title'][:50]}..."
        )

    # 사용자 확인
    confirm = (
        input(f"\n❓ {len(cleanup_candidates)}개 덱을 삭제하시겠습니까? (y/N): ")
        .strip()
        .lower()
    )
    if confirm != "y":
        print("❌ 취소되었습니다.")
        return

    # 덱 삭제 실행
    success_count = 0
    for deck in cleanup_candidates:
        try:
            print(f"🗑️  삭제 중: {deck['deck_id'][:8]}... ({deck['title'][:30]}...)")
            delete_response = requests.delete(f"{API_BASE}/decks/{deck['deck_id']}")
            if delete_response.status_code == 200:
                success_count += 1
                print("   ✅ 삭제 완료")
            else:
                print(f"   ❌ 삭제 실패: {delete_response.status_code}")
        except Exception as e:
            print(f"   ❌ 오류: {e}")

    print(f"\n🎉 정리 완료: {success_count}/{len(cleanup_candidates)}개 덱 삭제")


if __name__ == "__main__":
    cleanup_test_decks()
