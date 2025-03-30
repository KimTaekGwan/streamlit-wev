import streamlit as st
import pandas as pd
import hashlib
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 메인 앱에서 함수 가져오기
from apps.test.main import load_users, save_users, check_login

# 페이지 설정
st.set_page_config(
    page_title="관리자 설정 - 청소 구역 배치 시스템", page_icon="⚙️", layout="wide"
)

# 페이지 제목을 한글로 표시
st.title("관리자 설정")


def main():
    # 로그인 확인
    if not check_login():
        return

    # 관리자 권한 확인
    if not st.session_state.user.get("is_admin", False):
        st.error("관리자 권한이 필요합니다.")
        st.stop()

    # 탭 생성
    tab1, tab2 = st.tabs(["계정 관리", "시스템 설정"])

    with tab1:
        st.subheader("계정 관리")

        # 사용자 정보 로드
        users_df = load_users()

        # 기존 사용자 목록 표시
        st.write("기존 사용자 목록")

        # 헤더 추가
        header_col1, header_col2, header_col3 = st.columns([3, 2, 1])
        with header_col1:
            st.write("**아이디**")
        with header_col2:
            st.write("**권한**")
        with header_col3:
            st.write("**작업**")

        st.divider()  # 구분선 추가

        # 각 사용자 표시
        for i, row in users_df.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.write(row["username"])

            with col2:
                # 현재 로그인한 사용자는 관리자 권한 변경 불가
                if row["username"] == st.session_state.user["username"]:
                    st.write("관리자" if row["is_admin"] else "일반")
                else:
                    users_df.at[i, "is_admin"] = st.checkbox(
                        "관리자 권한", value=row["is_admin"], key=f"user_admin_{i}"
                    )

            with col3:
                # 현재 로그인한 사용자는 삭제 불가
                if row["username"] == st.session_state.user["username"]:
                    st.write("-")
                else:
                    # 삭제 확인 상태 추적을 위한 세션 상태 변수
                    if f"confirm_delete_user_{i}" not in st.session_state:
                        st.session_state[f"confirm_delete_user_{i}"] = False

                    # 삭제 버튼 또는 확인 버튼 표시
                    if not st.session_state[f"confirm_delete_user_{i}"]:
                        if st.button("삭제", key=f"delete_user_{i}"):
                            st.session_state[f"confirm_delete_user_{i}"] = True
                            st.rerun()
                    else:
                        confirm_col1, confirm_col2 = st.columns(2)
                        with confirm_col1:
                            if st.button(
                                "확인",
                                key=f"confirm_user_{i}",
                                type="primary",
                                use_container_width=True,
                            ):
                                users_df = users_df.drop(i)
                                save_users(users_df)
                                st.success(
                                    f"'{row['username']}' 계정이 삭제되었습니다."
                                )
                                st.session_state[f"confirm_delete_user_{i}"] = False
                                st.rerun()
                        with confirm_col2:
                            if st.button(
                                "취소", key=f"cancel_user_{i}", use_container_width=True
                            ):
                                st.session_state[f"confirm_delete_user_{i}"] = False
                                st.rerun()

        # 변경사항 감지를 위한 원본 데이터 복사
        if "original_users" not in st.session_state:
            st.session_state.original_users = users_df.copy()

        # 변경사항 감지
        has_changes = not users_df.equals(st.session_state.original_users)

        # 변경사항이 있을 때만 저장 버튼 활성화
        save_disabled = not has_changes
        if st.button("변경사항 저장", disabled=save_disabled, key="save_users"):
            save_users(users_df)
            st.session_state.original_users = users_df.copy()  # 원본 데이터 업데이트
            st.success("사용자 정보가 저장되었습니다.")

        # 새 사용자 추가
        st.subheader("새 사용자 추가")

        with st.form("add_user_form"):
            new_username = st.text_input("아이디")
            new_password = st.text_input("비밀번호", type="password")
            new_password_confirm = st.text_input("비밀번호 확인", type="password")
            is_admin = st.checkbox("관리자 권한 부여")

            submit = st.form_submit_button("사용자 추가")

            if submit:
                # 유효성 검사
                if not new_username:
                    st.error("아이디를 입력하세요.")
                elif not new_password:
                    st.error("비밀번호를 입력하세요.")
                elif new_password != new_password_confirm:
                    st.error("비밀번호가 일치하지 않습니다.")
                elif new_username in users_df["username"].values:
                    st.error("이미 존재하는 아이디입니다.")
                else:
                    # 새 사용자 추가
                    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
                    new_row = pd.DataFrame(
                        {
                            "username": [new_username],
                            "password": [hashed_password],
                            "is_admin": [is_admin],
                        }
                    )
                    users_df = pd.concat([users_df, new_row], ignore_index=True)
                    save_users(users_df)
                    st.success(f"{new_username} 계정이 추가되었습니다.")
                    st.rerun()

    with tab2:
        st.subheader("시스템 설정")
        st.info("향후 추가 예정인 기능입니다.")


if __name__ == "__main__":
    main()
