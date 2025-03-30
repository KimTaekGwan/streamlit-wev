import streamlit as st
import pandas as pd
import sys
import os
import datetime
import json

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 메인 앱에서 함수 가져오기
from main import (
    load_assignments,
    export_assignment_to_excel,
    check_login,
    save_assignments,
)
from streamlit.components.v1 import html

# 페이지 설정
st.set_page_config(
    page_title="배치 기록 - 청소 구역 배치 시스템", page_icon="📋", layout="wide"
)

# 템플릿 기본값 설정
DEFAULT_HEADER = """안녕하세요. 한세호대리입니다.

{month}월 청소구역 공유드립니다.

기간 : {period}

"""

DEFAULT_FOOTER = """
자신의 청소구역을 숙지해주시고 내일 뵙겠습니다.
안녕히주무세요:)

감사합니다."""

# 세션 상태 초기화
if "template_header" not in st.session_state:
    st.session_state.template_header = DEFAULT_HEADER

if "template_footer" not in st.session_state:
    st.session_state.template_footer = DEFAULT_FOOTER

# 페이지 제목을 한글로 표시
st.title("배치 기록")


def generate_template_text(
    date, grouped_data, header_template=None, footer_template=None
):
    if header_template is None:
        header_template = st.session_state.template_header

    if footer_template is None:
        footer_template = st.session_state.template_footer

    # 년, 월 추출
    try:
        # 날짜 형식에 시간이 포함되어 있을 수 있으므로 더 포괄적인 형식 처리
        if " " in date:
            # 날짜와 시간이 포함된 경우 (예: 2023-04-05 12:34:56)
            date_part = date.split(" ")[0]  # 날짜 부분만 추출
            date_obj = datetime.datetime.strptime(date_part, "%Y-%m-%d")
        else:
            # 날짜만 있는 경우
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        # 다른 형식으로 시도
        try:
            # 간단히 날짜 객체로 변환 (이미 날짜 객체인 경우도 처리)
            if isinstance(date, (datetime.date, datetime.datetime)):
                date_obj = (
                    date
                    if isinstance(date, datetime.datetime)
                    else datetime.datetime.combine(date, datetime.time())
                )
            else:
                # 마지막 시도로 날짜만 파싱
                date_obj = datetime.datetime.strptime(str(date)[:10], "%Y-%m-%d")
        except ValueError:
            # 모든 시도가 실패하면 현재 날짜 사용
            st.error(f"날짜 형식을 인식할 수 없습니다: {date}. 현재 날짜를 사용합니다.")
            date_obj = datetime.datetime.now()

    month = date_obj.month
    year = date_obj.year % 100  # 년도의 마지막 두 자리만 사용

    # 시작일과 마지막일 계산
    month_start = datetime.date(date_obj.year, date_obj.month, 1)
    next_month = month_start.replace(day=28) + datetime.timedelta(days=4)
    month_end = (next_month - datetime.timedelta(days=next_month.day)).replace(
        day=1
    ) - datetime.timedelta(days=1)

    period = f"{year}.{month:02d}.01~{year}.{month:02d}.{month_end.day}"

    # 템플릿 헤더 (포맷팅)
    template = header_template.format(month=month, period=period, year=year)

    # 각 구역별 담당자 목록 추가
    for i, row in grouped_data.iterrows():
        template += f"{i+1}. {row['구역']} - {'. '.join(row['담당자'])}\n"

    # 템플릿 푸터 (포맷팅)
    template += footer_template.format(month=month, period=period, year=year)

    return template


def create_copy_button(text, button_id="copy_btn"):
    """클립보드 복사 버튼 생성"""
    # JavaScript로 클립보드 복사 기능 구현
    copy_js = f"""
    <script>
    function copyToClipboard() {{
        const text = {json.dumps(text)};
        navigator.clipboard.writeText(text).then(function() {{
            document.getElementById("{button_id}_result").innerText = "복사되었습니다!";
            setTimeout(function() {{
                document.getElementById("{button_id}_result").innerText = "";
            }}, 2000);
        }})
        .catch(function(err) {{
            document.getElementById("{button_id}_result").innerText = "복사 실패: " + err;
        }});
    }}
    </script>
    <button onclick="copyToClipboard()" style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">클립보드에 복사</button>
    <span id="{button_id}_result" style="margin-left: 10px; color: green;"></span>
    """
    return copy_js


def main():
    # 로그인 확인
    if not check_login():
        return

    # 템플릿 설정 탭과 배치 기록 탭
    tab1, tab2 = st.tabs(["배치 기록", "템플릿 설정"])

    with tab2:
        st.subheader("템플릿 설정")
        st.write(
            "템플릿에서 사용할 수 있는 변수: {month} (월), {period} (기간), {year} (년도 끝 두자리)"
        )

        # 템플릿 헤더 설정
        header = st.text_area(
            "템플릿 상단", st.session_state.template_header, height=200
        )

        # 템플릿 푸터 설정
        footer = st.text_area(
            "템플릿 하단", st.session_state.template_footer, height=200
        )

        # 템플릿 저장
        if st.button("템플릿 저장"):
            st.session_state.template_header = header
            st.session_state.template_footer = footer
            st.success("템플릿이 저장되었습니다.")

        # 기본값으로 재설정
        if st.button("기본값으로 재설정"):
            st.session_state.template_header = DEFAULT_HEADER
            st.session_state.template_footer = DEFAULT_FOOTER
            st.success("템플릿이 기본값으로 재설정되었습니다.")

    with tab1:
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

            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(
                    label="엑셀 파일로 다운로드",
                    data=excel_data,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            with col3:
                # 배치 기록 삭제 버튼
                if st.button(
                    "이 배치 기록 삭제", type="primary", use_container_width=True
                ):
                    delete_confirm = st.checkbox(
                        "정말로 이 배치 기록을 삭제하시겠습니까?"
                    )

                    if delete_confirm:
                        # 선택된 날짜의 배치 기록을 제외한 나머지 기록만 유지
                        assignments_df = assignments_df[
                            assignments_df["날짜"] != selected_date
                        ]
                        save_assignments(assignments_df)
                        st.success(f"{selected_date} 배치 기록이 삭제되었습니다.")
                        st.rerun()

            # 템플릿 문자열 생성 및 복사 기능
            template_text = generate_template_text(selected_date, grouped)

            st.subheader("메시지 템플릿")
            st.text_area(
                "아래 텍스트를 복사하여 사용하세요:",
                template_text,
                height=400,
                key="template_display",
            )

            # 클립보드 복사 버튼
            html(create_copy_button(template_text), height=50)

            with col2:
                # 템플릿 복사 버튼
                st.download_button(
                    label="텍스트 파일로 다운로드",
                    data=template_text,
                    file_name=f"청소구역안내_{selected_date.replace('-', '')}.txt",
                    mime="text/plain",
                )


if __name__ == "__main__":
    main()
