import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
import random
from PIL import Image
import io
import hashlib
import webbrowser

# 데이터 폴더 생성
if not os.path.exists("data"):
    os.makedirs("data")

# 사용자 데이터 파일 경로
MEMBERS_FILE = "data/members.csv"
AREAS_FILE = "data/cleaning_areas.csv"
ASSIGNMENTS_FILE = "data/assignments.csv"
USERS_FILE = "data/users.csv"


# 데이터 초기화
def initialize_data():
    # 멤버 데이터 초기화
    if not os.path.exists(MEMBERS_FILE):
        members = [
            "김택관",
            "Debbie",
            "권지민",
            "김나희",
            "김진산",
            "박지현",
            "서수현",
            "위진희",
            "이건",
            "이서혁",
            "이은비",
            "정다은",
            "정성우",
            "조재웅",
            "조재원",
            "최용석",
            "한세호",
            "한유진",
        ]
        members_df = pd.DataFrame({"이름": members, "활성": [True] * len(members)})
        members_df.to_csv(MEMBERS_FILE, index=False, encoding="utf-8-sig")

    # 청소 구역 데이터 초기화
    if not os.path.exists(AREAS_FILE):
        areas = [
            {"구역명": "바닥쓸기(빗자루)", "필요인원": 4},
            {"구역명": "바닥닦기(대걸래)", "필요인원": 4},
            {"구역명": "분리수거(통 세척 및 정수기 물받이)", "필요인원": 2},
            {"구역명": "휴지통 비우기", "필요인원": 2},
            {
                "구역명": "공용 테이블 닦기(탕비실,회의실) + 수납장 먼지털기",
                "필요인원": 1,
            },
            {"구역명": "공용 휴지 및 탕비실, 냉장고 물건 채우기", "필요인원": 1},
            {"구역명": "창문 닦기 및 바닥 부착물 제거", "필요인원": 4},
        ]
        areas_df = pd.DataFrame(areas)
        areas_df.to_csv(AREAS_FILE, index=False, encoding="utf-8-sig")

    # 배치 기록 초기화
    if not os.path.exists(ASSIGNMENTS_FILE):
        assignments_df = pd.DataFrame(columns=["날짜", "구역", "담당자"])
        assignments_df.to_csv(ASSIGNMENTS_FILE, index=False, encoding="utf-8-sig")

    # 사용자 계정 초기화
    if not os.path.exists(USERS_FILE):
        # 기본 관리자 계정 생성 (ID: admin, PW: admin1234)
        admin_password = hashlib.sha256("admin1234".encode()).hexdigest()
        users_df = pd.DataFrame(
            {"username": ["admin"], "password": [admin_password], "is_admin": [True]}
        )
        users_df.to_csv(USERS_FILE, index=False, encoding="utf-8-sig")


# 데이터 로드
def load_members():
    return pd.read_csv(MEMBERS_FILE, encoding="utf-8-sig")


def load_areas():
    return pd.read_csv(AREAS_FILE, encoding="utf-8-sig")


def load_assignments():
    return pd.read_csv(ASSIGNMENTS_FILE, encoding="utf-8-sig")


def load_users():
    return pd.read_csv(USERS_FILE, encoding="utf-8-sig")


# 데이터 저장
def save_members(members_df):
    members_df.to_csv(MEMBERS_FILE, index=False, encoding="utf-8-sig")


def save_areas(areas_df):
    areas_df.to_csv(AREAS_FILE, index=False, encoding="utf-8-sig")


def save_assignments(assignments_df):
    assignments_df.to_csv(ASSIGNMENTS_FILE, index=False, encoding="utf-8-sig")


def save_users(users_df):
    users_df.to_csv(USERS_FILE, index=False, encoding="utf-8-sig")


# 자동 배치 생성
def generate_assignment():
    members_df = load_members()
    areas_df = load_areas()

    # 활성 상태인 멤버만 선택
    active_members = members_df[members_df["활성"] == True]["이름"].tolist()

    # 이전 배치 기록 확인해서 최근에 같은 일을 하지 않도록 하기
    assignments_df = load_assignments()
    recent_assignments = {}

    if not assignments_df.empty:
        # 최근 날짜의 배치만 가져오기
        latest_date = assignments_df["날짜"].max()
        recent_df = assignments_df[assignments_df["날짜"] == latest_date]

        for _, row in recent_df.iterrows():
            recent_assignments[row["담당자"]] = row["구역"]

    # 랜덤 배치를 위한 멤버 복사 및 섞기
    available_members = active_members.copy()
    random.shuffle(available_members)

    # 이전에 같은 구역을 담당했던 사람은 가능하면 다른 구역으로 배치
    def get_best_member(area_name, num_needed):
        best_members = []
        for _ in range(num_needed):
            if not available_members:
                break

            # 이전에 같은 구역을 담당하지 않았던 사람을 우선적으로 선택
            not_assigned_before = [
                m for m in available_members if recent_assignments.get(m) != area_name
            ]

            if not_assigned_before:
                selected = not_assigned_before[0]
            else:
                selected = available_members[0]

            best_members.append(selected)
            available_members.remove(selected)

        return best_members

    # 각 구역에 인원 배치
    new_assignments = []
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _, area in areas_df.iterrows():
        area_name = area["구역명"]
        num_needed = area["필요인원"]

        assigned_members = get_best_member(area_name, num_needed)

        for member in assigned_members:
            new_assignments.append(
                {"날짜": current_date, "구역": area_name, "담당자": member}
            )

    # 남은 인원이 있으면 무작위로 배치
    if available_members:
        area_order = areas_df["구역명"].tolist()
        area_index = 0

        for member in available_members:
            new_assignments.append(
                {
                    "날짜": current_date,
                    "구역": area_order[area_index % len(area_order)],
                    "담당자": member,
                }
            )
            area_index += 1

    # 새 배치 저장
    new_assignments_df = pd.DataFrame(new_assignments)
    all_assignments = pd.concat([assignments_df, new_assignments_df], ignore_index=True)
    save_assignments(all_assignments)

    return new_assignments_df


# 배치표 내보내기
def export_assignment_to_excel(assignment_df):
    # 결과를 보기 좋게 정렬
    assignment_df = assignment_df.sort_values("구역")

    # 피벗 테이블 생성
    pivot_df = pd.pivot_table(
        assignment_df, index=["구역"], values=["담당자"], aggfunc=lambda x: ", ".join(x)
    )

    # 엑셀 파일 생성
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pivot_df.to_excel(writer, sheet_name="청소구역배치")
        assignment_df.to_excel(writer, sheet_name="전체배치목록", index=False)

    return output.getvalue()


# 로그인 확인
def check_login():
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        login()
        return False
    return True


# 로그인 페이지
def login():
    st.title("청소 구역 배치 시스템 - 로그인")

    with st.form("login_form"):
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        submit = st.form_submit_button("로그인")

        if submit:
            # 사용자 확인
            users_df = load_users()
            user_row = users_df[users_df["username"] == username]

            if not user_row.empty:
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                if user_row.iloc[0]["password"] == hashed_password:
                    st.session_state.user = {
                        "username": username,
                        "is_admin": user_row.iloc[0]["is_admin"],
                    }
                    st.success("로그인 성공!")
                    st.rerun()
                else:
                    st.error("비밀번호가 일치하지 않습니다.")
            else:
                st.error("존재하지 않는 아이디입니다.")

    # 계정 생성 안내
    # st.info("기본 관리자 계정: admin / admin1234")


# 앱 UI
def main():
    st.set_page_config(
        page_title="청소 구역 배치 시스템", page_icon="🏠", layout="wide"
    )

    # 데이터 초기화
    initialize_data()

    # 로그인 확인
    if not check_login():
        return

    # 로그인 된 경우 메인 페이지 표시
    st.title("청소 구역 배치 시스템")
    st.write(f"{st.session_state.user['username']}님 환영합니다.")

    # 사이드바 메뉴
    st.sidebar.title("메뉴")

    # 로그아웃 버튼
    if st.sidebar.button("로그아웃"):
        st.session_state.user = None
        st.rerun()

    # 홈 화면 내용
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("현재 등록된 팀원")
        members_df = load_members()
        active_members = members_df[members_df["활성"] == True]
        st.write(f"활성 팀원 수: {len(active_members)}")
        st.dataframe(active_members[["이름"]])

    with col2:
        st.subheader("현재 등록된 청소 구역")
        areas_df = load_areas()
        st.write(f"청소 구역 수: {len(areas_df)}")
        st.dataframe(areas_df)

    # 시스템 사용 안내
    st.markdown(
        """
    ## 시스템 사용 방법
    1. 왼쪽 사이드바에서 원하는 기능을 선택하세요.
    2. **팀원 관리**: 팀원 추가, 삭제, 활성화 상태 변경
    3. **청소 구역 관리**: 청소 구역 추가, 삭제, 필요 인원 변경
    4. **배치 생성**: 팀원들을 청소 구역에 자동으로 배치 생성
    5. **배치 기록**: 이전에 생성한 배치 기록 확인
    """
    )


if __name__ == "__main__":
    main()
