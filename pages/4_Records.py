import streamlit as st
import pandas as pd
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 메인 앱에서 함수 가져오기
from apps.test.main import load_assignments, export_assignment_to_excel, check_login

# 페이지 설정
st.set_page_config(
    page_title="배치 기록 - 청소 구역 배치 시스템", page_icon="📋", layout="wide"
)

# 페이지 제목을 한글로 표시
st.title("배치 기록")


def main():
    # 로그인 확인
    if not check_login():
        return

    assignments_df = load_assignments()

    if assignments_df.empty:
        st.write("아직 생성된 배치가 없습니다.")
    else:
        # 날짜 선택
        dates = sorted(assignments_df["날짜"].unique(), reverse=True)
        selected_date = st.selectbox("날짜 선택", dates)

        # 선택된 날짜의 배치 표시
        filtered_df = assignments_df[assignments_df["날짜"] == selected_date]

        # 구역별로 그룹화하여 보여주기
        st.subheader(f"{selected_date} 배치")
        grouped = filtered_df.groupby("구역")["담당자"].apply(list).reset_index()

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
        excel_data = export_assignment_to_excel(filtered_df)
        file_name = f"청소구역배치_{selected_date.replace('-', '').replace(' ', '_').replace(':', '')}.xlsx"

        st.download_button(
            label="엑셀 파일로 다운로드",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


if __name__ == "__main__":
    main()
