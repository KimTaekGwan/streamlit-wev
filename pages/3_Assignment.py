import streamlit as st
import pandas as pd
import datetime
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 메인 앱에서 함수 가져오기
from apps.test.main import (
    load_members,
    load_areas,
    generate_assignment,
    export_assignment_to_excel,
    check_login,
)

# 페이지 설정
st.set_page_config(
    page_title="배치 생성 - 청소 구역 배치 시스템", page_icon="🔄", layout="wide"
)

# 페이지 제목을 한글로 표시
st.title("청소 구역 배치 생성")


def main():
    # 로그인 확인
    if not check_login():
        return

    # 활성화된 팀원 및 필요 인원 계산
    members_df = load_members()
    areas_df = load_areas()

    active_members = members_df[members_df["활성"] == True]
    total_active_members = len(active_members)
    total_required_members = areas_df["필요인원"].sum()

    # 필요한 인원과 활성 인원 표시
    col1, col2 = st.columns(2)
    with col1:
        st.metric("활성화된 팀원 수", total_active_members)
    with col2:
        st.metric("필요한 인원 수", total_required_members)

    # 인원 불일치 체크
    if total_active_members != total_required_members:
        st.warning(
            f"활성화된 팀원 수({total_active_members})와 필요한 인원 수({total_required_members})가 일치하지 않습니다."
        )
        st.info(
            "배치를 생성하면 인원이 많은 경우 랜덤으로 추가 배치되고, 인원이 부족한 경우 일부 구역에 배치되지 않을 수 있습니다."
        )
        proceed = st.radio("계속 진행하시겠습니까?", ["예", "아니오"], index=1)
        if proceed == "아니오":
            st.stop()

    if st.button("새 배치 생성"):
        with st.spinner("배치 생성 중..."):
            new_assignments = generate_assignment()

            # 구역별로 그룹화하여 보여주기
            st.subheader("생성된 배치")

            # 결과를 테이블 형태로 보여주기
            grouped = (
                new_assignments.groupby("구역")["담당자"].apply(list).reset_index()
            )

            # 헤더 추가
            header_col1, header_col2 = st.columns([3, 7])
            with header_col1:
                st.write("**구역명**")
            with header_col2:
                st.write("**담당자**")

            st.divider()  # 구분선 추가

            # 결과를 테이블 형태로 표시
            for i, row in grouped.iterrows():
                col1, col2 = st.columns([3, 7])
                with col1:
                    st.write(row["구역"])
                with col2:
                    st.write(", ".join(row["담당자"]))

            # 엑셀 파일 다운로드 버튼
            excel_data = export_assignment_to_excel(new_assignments)
            current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"청소구역배치_{current_date}.xlsx"

            st.download_button(
                label="엑셀 파일로 다운로드",
                data=excel_data,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


if __name__ == "__main__":
    main()
