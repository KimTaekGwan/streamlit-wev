import streamlit as st
import pandas as pd
import hashlib
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 메인 앱에서 함수 가져오기
from main import load_users, save_users, check_login

# 페이지 설정
st.set_page_config(
    page_title="비밀번호 변경 - 청소 구역 배치 시스템", page_icon="🔑", layout="wide"
)

# 페이지 제목을 한글로 표시
st.title("비밀번호 변경")


def main():
    # 로그인 확인
    if not check_login():
        return

    username = st.session_state.user["username"]

    with st.form("change_password_form"):
        st.write(f"사용자: {username}")
        current_password = st.text_input("현재 비밀번호", type="password")
        new_password = st.text_input("새 비밀번호", type="password")
        new_password_confirm = st.text_input("새 비밀번호 확인", type="password")

        submit = st.form_submit_button("비밀번호 변경")

        if submit:
            # 사용자 정보 로드
            users_df = load_users()
            user_idx = users_df[users_df["username"] == username].index[0]

            # 현재 비밀번호 확인
            hashed_current = hashlib.sha256(current_password.encode()).hexdigest()

            if hashed_current != users_df.loc[user_idx, "password"]:
                st.error("현재 비밀번호가 일치하지 않습니다.")
            elif not new_password:
                st.error("새 비밀번호를 입력하세요.")
            elif new_password != new_password_confirm:
                st.error("새 비밀번호가 일치하지 않습니다.")
            elif current_password == new_password:
                st.error("새 비밀번호가 현재 비밀번호와 같습니다.")
            else:
                # 비밀번호 변경
                hashed_new = hashlib.sha256(new_password.encode()).hexdigest()
                users_df.loc[user_idx, "password"] = hashed_new
                save_users(users_df)
                st.success("비밀번호가 변경되었습니다.")


if __name__ == "__main__":
    main()
