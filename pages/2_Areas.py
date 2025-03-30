import streamlit as st
import pandas as pd
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 메인 앱에서 함수 가져오기
from apps.test.main import load_areas, save_areas, check_login

# 페이지 설정
st.set_page_config(
    page_title="청소 구역 관리 - 청소 구역 배치 시스템", page_icon="🧹", layout="wide"
)

# 페이지 제목을 한글로 표시
st.title("청소 구역 관리")


def main():
    # 로그인 확인
    if not check_login():
        return

    areas_df = load_areas()

    # 원본 데이터 복사본 만들기 (비교용)
    if "original_areas" not in st.session_state:
        st.session_state.original_areas = areas_df.copy()

    # 기존 구역 수정
    st.subheader("기존 구역 관리")

    # 헤더 추가
    header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
    with header_col1:
        st.write("**구역명**")
    with header_col2:
        st.write("**필요인원**")
    with header_col3:
        st.write("**작업**")

    st.divider()  # 구분선 추가

    # 각 구역을 행으로 표시하고 수정/삭제 기능 추가
    for i, row in areas_df.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.write(row["구역명"])

        with col2:
            areas_df.at[i, "필요인원"] = st.number_input(
                "필요인원",
                min_value=1,
                value=row["필요인원"],
                key=f"area_people_{i}",
                label_visibility="collapsed",
            )

        with col3:
            # 삭제 확인 상태 추적을 위한 세션 상태 변수
            if f"confirm_delete_area_{i}" not in st.session_state:
                st.session_state[f"confirm_delete_area_{i}"] = False

            # 삭제 버튼 또는 확인 버튼 표시
            if not st.session_state[f"confirm_delete_area_{i}"]:
                if st.button("삭제", key=f"delete_area_{i}"):
                    st.session_state[f"confirm_delete_area_{i}"] = True
                    st.rerun()
            else:
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button(
                        "확인",
                        key=f"confirm_area_{i}",
                        type="primary",
                        use_container_width=True,
                    ):
                        areas_df = areas_df.drop(i)
                        save_areas(areas_df)
                        st.success(f"'{row['구역명']}' 구역이 삭제되었습니다.")
                        st.session_state[f"confirm_delete_area_{i}"] = False
                        st.rerun()
                with confirm_col2:
                    if st.button(
                        "취소", key=f"cancel_area_{i}", use_container_width=True
                    ):
                        st.session_state[f"confirm_delete_area_{i}"] = False
                        st.rerun()

    # 변경사항 감지
    has_changes = not areas_df.equals(st.session_state.original_areas)

    # 변경사항이 있을 때만 저장 버튼 활성화
    save_disabled = not has_changes
    if st.button("변경사항 저장", disabled=save_disabled, key="save_areas"):
        save_areas(areas_df)
        st.session_state.original_areas = areas_df.copy()  # 원본 데이터 업데이트
        st.success("청소 구역 정보가 저장되었습니다.")

    # 새 구역 추가
    st.subheader("새 청소 구역 추가")
    new_area = st.text_input("새 청소 구역 이름")
    new_people = st.number_input("필요 인원", min_value=1, value=1)

    if st.button("구역 추가") and new_area:
        if new_area not in areas_df["구역명"].values:
            new_row = pd.DataFrame({"구역명": [new_area], "필요인원": [new_people]})
            areas_df = pd.concat([areas_df, new_row], ignore_index=True)
            save_areas(areas_df)
            st.success(f"{new_area} 구역이 추가되었습니다.")
            st.rerun()
        else:
            st.error("이미 존재하는 구역입니다.")


if __name__ == "__main__":
    main()
