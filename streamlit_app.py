import asyncio
import time
from datetime import datetime
from uuid import UUID

import streamlit as st

from app.adapter.db.sqlite import SQLiteRepository
from app.adapter.llm.langchain_client import LangchainLLM
from app.logging import configure_logging, get_logger
from app.service.generate_deck import generate_deck

# --- 기본 설정 ---
logger = get_logger(__name__)
configure_logging(level="INFO", compact=True)


# --- UI 헬퍼 함수 ---

def setup_sidebar():
    """사이드바 UI 컴포넌트를 설정합니다."""
    with st.sidebar:
        st.header("⚙️ Settings")
        st.subheader("🤖 AI Model")
        model_name = st.selectbox(
            "Select Model",
            ["gpt-4o-mini", "gpt-5-nano", "gpt-5-mini"],
            index=2,
            help="콘텐츠 생성을 위한 AI 모델을 선택하세요.",
            key="model_selection",
        )
        model_info = {
            "gpt-4o-mini": "⚡️ 빠르고 효율적이며, 균형이 좋습니다",
            "gpt-5-nano": "🔥 속도에 최적화된 최신 모델입니다",
            "gpt-5-mini": "💼 전문가 수준의 신뢰성 있는 모델입니다",
        }
        st.caption(model_info.get(model_name, ""))
        st.info(f"**선택된 모델:** {model_name}")

        st.divider()

        st.subheader("💾 Storage")
        st.info("**저장소:** SQLite")  # SQLite로 고정
        db_path = st.text_input("Database Path", value="decks.db", key="db_path")

        st.divider()
        st.markdown("### 📝 사용 방법")
        st.markdown(
            """
        1. 발표 주제를 입력하세요.
        2. '덱 생성' 버튼을 클릭하세요.
        3. 생성된 슬라이드를 확인하세요.
        4. '최근 덱' 목록에서 이전 덱을 불러오세요.
        """
        )
    return model_name, db_path

def show_creation_view(repo: SQLiteRepository, model_name: str):
    """새로운 덱을 생성하는 UI를 표시합니다."""
    st.header("📋 새로운 덱 생성")
    with st.form("deck_form"):
        prompt = st.text_area(
            "발표 주제",
            placeholder="예: Samsung vs Hynix 메모리 반도체 기술 비교 분석 프레젠테이션",
            height=100,
            help="만들고 싶은 프레젠테이션에 대해 설명해주세요.",
        )
        submitted = st.form_submit_button("🚀 덱 생성", type="primary")

        if submitted and prompt.strip():
            if len(prompt.strip()) < 5:
                st.error("주제는 5자 이상이어야 합니다.")
            elif len(prompt.strip()) > 5000:
                st.error("주제는 5000자 미만이어야 합니다.")
            else:
                generate_presentation(prompt.strip(), repo, model_name)

def show_deck_view(deck_id: str, repo: SQLiteRepository):
    """선택된 덱의 내용을 표시합니다."""
    if st.button("⬅️ 새로 만들기 화면으로 돌아가기"):
        del st.session_state["view_deck_id"]
        st.rerun()

    display_deck_content(deck_id, repo)

def display_recent_decks(repo: SQLiteRepository):
    """데이터베이스에서 최근에 생성된 덱을 표시합니다."""
    st.header("📊 최근 덱")
    st.subheader("🗄️ 저장된 덱 목록")
    try:
        stored_decks = asyncio.run(repo.list_all_decks(limit=10))
        if stored_decks:
            for deck in stored_decks:
                with st.container():
                    deck_id = deck['deck_id']
                    st.write(f"**{deck['title']}**")
                    st.caption(
                        f"ID: `{deck_id[:8]}...` | 슬라이드: {deck['slide_count']} | 상태: {deck['status']}"
                    )

                    if st.button("덱 보기", key=f"view_stored_{deck_id}", type="secondary"):
                        st.session_state["view_deck_id"] = deck_id
                        st.rerun()
                    st.divider()
        else:
            st.write("저장된 덱이 없습니다.")
    except Exception as e:
        st.error(f"저장된 덱을 불러오는데 실패했습니다: {e}")
        logger.error("저장된 덱 로딩 오류", error=str(e))


# --- 핵심 로직 함수 ---

def generate_presentation(prompt: str, repo: SQLiteRepository, model_name: str):
    """프레젠테이션 생성 과정을 처리하고 진행 상태를 표시합니다."""
    progress_bar = st.progress(0, "초기화 중...")
    status_text = st.empty()
    status_text.text("🔧 초기화 중...")

    try:
        llm = LangchainLLM(model=model_name)
        status_text.text("🤖 AI 생성을 시작합니다...")
        progress_bar.progress(20)

        start_time = time.time()

        def update_progress(step: str, progress: int):
            progress_bar.progress(min(progress, 100), text=f"🤖 [{model_name}] {step}")

        deck_id = asyncio.run(generate_deck(prompt, llm, repo, update_progress))
        generation_time = time.time() - start_time

        progress_bar.progress(100, "✅ 생성 완료!")
        status_text.empty()

        st.success(f"🎉 **{model_name}**을 사용하여 {generation_time:.2f}초 만에 덱을 생성했습니다!")
        st.info(f"**덱 ID:** `{deck_id}`")

        # 새로 생성된 덱을 즉시 볼 수 있도록 세션 상태 설정
        st.session_state["view_deck_id"] = str(deck_id)
        st.rerun()

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ 생성 실패: {str(e)}")

def display_deck_content(deck_id: str, repo: SQLiteRepository):
    """덱의 전체 내용과 모든 슬라이드를 가져와 표시합니다."""
    try:
        deck_data = asyncio.run(repo.get_deck(UUID(deck_id)))
        if not deck_data:
            st.warning("덱을 찾을 수 없습니다.")
            return

        st.header(f"📑: {deck_data.get('deck_title', '생성된 프레젠테이션')}")

        with st.expander("덱 정보", expanded=False):
            col1, col2, col3 = st.columns(3)
            col1.metric("상태", deck_data.get("status", "unknown"))
            col2.metric("슬라이드 수", len(deck_data.get("slides", [])))
            created_at = deck_data.get("created_at")
            col3.metric(
                "생성일",
                created_at.strftime("%Y-%m-%d %H:%M")
                if isinstance(created_at, datetime)
                else "N/A",
            )
            st.write(f"**대상 청중:** {deck_data.get('audience', 'N/A')}")
            st.write(f"**핵심 메시지:** {deck_data.get('core_message', 'N/A')}")

        slides = deck_data.get("slides", [])
        if slides:
            for i, slide in enumerate(slides):
                slide_plan = slide.get("plan", {})
                slide_title = slide_plan.get("slide_title", f"슬라이드 {i+1}")

                with st.expander(f"슬라이드 {i+1}: {slide_title}", expanded=i == 0):
                    slide_content = slide.get("content", {})
                    html_content = slide_content.get("html_content", "")
                    if html_content:
                        st.components.v1.html(html_content, height=600, scrolling=False)
                    else:
                        st.warning("이 슬라이드에 대한 시각적 콘텐츠가 없습니다.")

                    with st.popover("슬라이드 상세 정보 보기"):
                        st.write("**슬라이드 계획:**")
                        st.json(slide_plan, expanded=False)
                        st.write("**원본 콘텐츠 데이터:**")
                        st.json(slide_content, expanded=False)
        else:
            st.info("이 덱에는 슬라이드가 없습니다.")

    except Exception as e:
        st.error(f"덱을 표시하는 중 오류 발생: {str(e)}")
        logger.error(f"덱 표시 오류 {deck_id=}", error=str(e))


# --- 메인 앱 ---

def main():
    """Streamlit 앱을 실행하는 메인 함수"""
    st.set_page_config(page_title="DeckFlow", page_icon="🎯", layout="wide")
    st.title("🎯 DeckFlow")
    st.markdown("_AI 기반 프레젠테이션 생성기_")

    model_name, db_path = setup_sidebar()
    repo = SQLiteRepository(db_path)

    col1, col2 = st.columns([2, 1])

    with col1:
        if "view_deck_id" in st.session_state:
            show_deck_view(st.session_state["view_deck_id"], repo)
        else:
            show_creation_view(repo, model_name)

    with col2:
        display_recent_decks(repo)


if __name__ == "__main__":
    main()