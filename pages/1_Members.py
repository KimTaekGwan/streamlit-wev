import streamlit as st
import pandas as pd
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 메인 앱에서 함수 가져오기
from apps.test.main import load_members, save_members, check_login

# 페이지 설정
st.set_page_config(
    page_title="팀원 관리 - 청소 구역 배치 시스템", page_icon="👥", layout="wide"
)

# 페이지 제목을 한글로 표시
st.title("팀원 관리")


def main():
    # 로그인 확인
    if not check_login():
        return

    members_df = load_members()

    # 원본 데이터 복사본 만들기 (비교용)
    if "original_members" not in st.session_state:
        st.session_state.original_members = members_df.copy()

    # 팀원 상태 변경
    st.subheader("팀원 상태 관리")

    # 헤더 추가
    header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
    with header_col1:
        st.write("**이름**")
    with header_col2:
        st.write("**활성 상태**")
    with header_col3:
        st.write("**작업**")

    st.divider()  # 구분선 추가

    for i, row in members_df.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(row["이름"])
        with col2:
            members_df.at[i, "활성"] = st.checkbox(
                "활성", value=row["활성"], key=f"member_{i}"
            )
        with col3:
            # 삭제 확인 상태 추적을 위한 세션 상태 변수
            if f"confirm_delete_{i}" not in st.session_state:
                st.session_state[f"confirm_delete_{i}"] = False

            # 삭제 버튼 또는 확인 버튼 표시
            if not st.session_state[f"confirm_delete_{i}"]:
                if st.button("삭제", key=f"delete_{i}"):
                    st.session_state[f"confirm_delete_{i}"] = True
                    st.rerun()
            else:
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button(
                        "확인",
                        key=f"confirm_{i}",
                        type="primary",
                        use_container_width=True,
                    ):
                        members_df = members_df.drop(i)
                        save_members(members_df)
                        st.success(f"{row['이름']}님이 삭제되었습니다.")
                        st.session_state[f"confirm_delete_{i}"] = False
                        st.rerun()
                with confirm_col2:
                    if st.button("취소", key=f"cancel_{i}", use_container_width=True):
                        st.session_state[f"confirm_delete_{i}"] = False
                        st.rerun()

    # 변경사항 감지
    has_changes = not members_df.equals(st.session_state.original_members)

    # 변경사항이 있을 때만 저장 버튼 활성화
    save_disabled = not has_changes
    if st.button("변경사항 저장", disabled=save_disabled, key="save_members"):
        save_members(members_df)
        st.session_state.original_members = members_df.copy()  # 원본 데이터 업데이트
        st.success("팀원 정보가 저장되었습니다.")

    # 새 팀원 추가
    st.subheader("새 팀원 추가")
    new_member = st.text_input("새 팀원 이름")
    if st.button("팀원 추가") and new_member:
        if new_member not in members_df["이름"].values:
            new_row = pd.DataFrame({"이름": [new_member], "활성": [True]})
            members_df = pd.concat([members_df, new_row], ignore_index=True)
            save_members(members_df)
            st.success(f"{new_member}님이 추가되었습니다.")
            st.rerun()
        else:
            st.error("이미 존재하는 팀원입니다.")


if __name__ == "__main__":
    main()
