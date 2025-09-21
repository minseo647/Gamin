#cd "C:\Users\권민서\OneDrive\바탕 화면\Gamin"; streamlit run public.py
import streamlit as st
import pandas as pd
import webbrowser
from datetime import datetime
import urllib.parse
import re

# 페이지 설정
st.set_page_config(
    page_title="공중화장실 추천 프로그램",
    page_icon="🚻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS 스타일 적용
st.markdown("""
    <style>
    .main {
        background-color: #E8F4FF;
    }
    .stButton > button {
        background-color: #0066CC;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #0052A3;
        transform: scale(1.05);
    }
    .district-button {
        background-color: #4A90E2;
        color: white;
        padding: 1rem;
        margin: 0.5rem;
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }
    .district-button:hover {
        background-color: #357ABD;
        transform: scale(1.1);
    }
    h1 {
        color: #0066CC;
        text-align: center;
        font-size: 4rem !important;
        margin-bottom: 0 !important;
    }
    h2 {
        color: #0066CC;
        text-align: center;
        font-size: 1.5rem !important;
        margin-top: 0 !important;
    }
    h3 {
        color: #0066CC;
    }
    .time-filter-button-current {
        background-color: #28A745;
    }
    .time-filter-button-custom {
        background-color: #FFC107;
    }
    .back-button {
        background-color: #6C757D;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_and_process_data():
    """데이터 로드 및 전처리"""
    try:
        # CSV 파일 읽기
        df = pd.read_csv('public.csv', encoding='utf-8')
        
        # 불필요한 컬럼 삭제
        columns_to_drop = ['관리기관명', '데이터기준일자']
        df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
        
        # 지역 컬럼 생성
        def extract_district(address):
            if pd.isna(address):
                return None
            if '서울특별시' in address:
                match = re.search(r'서울특별시\s+([가-힣]+구)', address)
                if match:
                    return match.group(1)
            return None
        
        df['지역'] = df['소재지도로명주소'].apply(extract_district)
        
        # 서울시 데이터만 필터링
        df = df[df['지역'].notna()].copy()
        
        return df
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {str(e)}")
        return None

def is_toilet_available(row, check_time):
    """특정 시간에 화장실이 이용 가능한지 확인"""
    # 상시 개방
    if pd.notna(row['개방시간']) and row['개방시간'] == '상시':
        return True
    
    # 개방시간상세 확인
    if pd.notna(row['개방시간상세']):
        time_detail = str(row['개방시간상세'])
        
        # 시간 범위 파싱 (예: "09:00~18:00")
        match = re.match(r'(\d{1,2}):(\d{2})[~-](\d{1,2}):(\d{2})', time_detail)
        if match:
            start_hour, start_min, end_hour, end_min = map(int, match.groups())
            
            # 체크 시간 파싱
            check_hour, check_min = map(int, check_time.split(':'))
            
            # 시간을 분으로 변환하여 비교
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min
            check_minutes = check_hour * 60 + check_min
            
            # 종료 시간이 시작 시간보다 작으면 자정을 넘는 경우
            if end_minutes < start_minutes:
                return check_minutes >= start_minutes or check_minutes <= end_minutes
            else:
                return start_minutes <= check_minutes <= end_minutes
    
    return False

def create_map_link(address, link_type='naver'):
    """지도 링크 생성"""
    if pd.isna(address):
        return None
    
    encoded_address = urllib.parse.quote(address)
    
    if link_type == 'naver':
        return f"https://map.naver.com/v5/search/{encoded_address}"
    else:  # google
        return f"https://www.google.com/maps/search/{encoded_address}"

def main():
    # 세션 상태 초기화
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'selected_district' not in st.session_state:
        st.session_state.selected_district = None
    if 'filter_time' not in st.session_state:
        st.session_state.filter_time = None
    
    # 데이터 로드
    df = load_and_process_data()
    if df is None:
        return
    
    # 페이지 라우팅
    if st.session_state.page == 'home':
        show_home_page()
    elif st.session_state.page == 'district_select':
        show_district_select_page(df)
    elif st.session_state.page == 'toilet_list':
        show_toilet_list_page(df)

def show_home_page():
    """화면1: 시작 화면"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1>🚻 공중화장실 추천 프로그램</h1>", unsafe_allow_html=True)
        st.markdown("<h2>가까운 공중화장실을 찾아보세요</h2>", unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if st.button("🏃 지역 선택하기", use_container_width=True, key="start_btn"):
            st.session_state.page = 'district_select'
            st.rerun()

def show_district_select_page(df):
    """화면2: 지역 선택"""
    # 뒤로가기 버튼
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("◀ 뒤로", key="back_to_home"):
            st.session_state.page = 'home'
            st.rerun()
    
    # 타이틀
    st.markdown("<h3 style='text-align: center;'>🗺️ 지역을 선택하세요</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 지역 목록 가져오기
    districts = sorted(df['지역'].unique())
    
    # 그리드로 지역 버튼 표시 (5열)
    cols = st.columns(5)
    for idx, district in enumerate(districts):
        col_idx = idx % 5
        with cols[col_idx]:
            if st.button(district, use_container_width=True, key=f"district_{district}"):
                st.session_state.selected_district = district
                st.session_state.page = 'toilet_list'
                st.session_state.filter_time = None
                st.rerun()

def show_toilet_list_page(df):
    """화면3: 화장실 목록"""
    # 헤더
    col1, col2, col3 = st.columns([1, 2, 3])
    
    with col1:
        if st.button("◀ 지역 선택", key="back_to_district"):
            st.session_state.page = 'district_select'
            st.session_state.filter_time = None
            st.rerun()
    
    with col2:
        st.markdown(f"<h3>{st.session_state.selected_district} 화장실 목록</h3>", unsafe_allow_html=True)
    
    # 필터 옵션
    with col3:
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            if st.button("🕐 현재 이용가능", key="filter_current", help="현재 시간 기준 이용 가능한 화장실"):
                current_time = datetime.now()
                st.session_state.filter_time = f"{current_time.hour:02d}:{current_time.minute:02d}"
                st.rerun()
        
        with filter_col2:
            custom_time = st.text_input("시간 입력 (HH:MM)", placeholder="14:30", key="custom_time")
            if st.button("⏰ 시간 적용", key="filter_custom"):
                if custom_time and re.match(r'^\d{1,2}:\d{2}$', custom_time):
                    try:
                        hour, minute = map(int, custom_time.split(':'))
                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                            st.session_state.filter_time = f"{hour:02d}:{minute:02d}"
                            st.rerun()
                        else:
                            st.error("올바른 시간 범위를 입력하세요 (00:00~23:59)")
                    except:
                        st.error("올바른 시간 형식을 입력하세요 (예: 14:30)")
                else:
                    st.error("시간을 HH:MM 형식으로 입력하세요")
        
        with filter_col3:
            if st.button("📋 전체 보기", key="show_all"):
                st.session_state.filter_time = None
                st.rerun()
    
    st.markdown("---")
    
    # 필터링된 데이터 가져오기
    district_df = df[df['지역'] == st.session_state.selected_district].copy()
    
    # 시간 필터 적용
    if st.session_state.filter_time:
        mask = district_df.apply(lambda row: is_toilet_available(row, st.session_state.filter_time), axis=1)
        filtered_df = district_df[mask]
        st.info(f"⏰ {st.session_state.filter_time} 기준 이용 가능한 화장실: {len(filtered_df)}개")
    else:
        filtered_df = district_df
        st.info(f"📊 전체 화장실: {len(filtered_df)}개")
    
    if len(filtered_df) == 0:
        st.warning("🚫 조건에 맞는 화장실이 없습니다.")
    else:
        # 화장실 목록 표시
        for idx, (_, row) in enumerate(filtered_df.iterrows(), start=1):
            with st.expander(f"📍 {idx}. {row['화장실명']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**주소:** {row['소재지도로명주소']}")
                    st.write(f"**개방시간:** {row['개방시간'] if pd.notna(row['개방시간']) else '정보없음'}")
                    st.write(f"**상세시간:** {row['개방시간상세'] if pd.notna(row['개방시간상세']) else '정보없음'}")
                    
                    # 시설 정보
                    facility_info = []
                    if pd.notna(row.get('남성용-대변기수', 0)) and row.get('남성용-대변기수', 0) > 0:
                        facility_info.append(f"남성 대변기: {int(row['남성용-대변기수'])}개")
                    if pd.notna(row.get('여성용-대변기수', 0)) and row.get('여성용-대변기수', 0) > 0:
                        facility_info.append(f"여성 대변기: {int(row['여성용-대변기수'])}개")
                    if pd.notna(row.get('남성용-장애인용대변기수', 0)) and row.get('남성용-장애인용대변기수', 0) > 0:
                        facility_info.append(f"장애인용: ♿")
                    
                    if facility_info:
                        st.write(f"**시설:** {', '.join(facility_info)}")
                
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # 지도 링크 버튼들
                    naver_link = create_map_link(row['소재지도로명주소'], 'naver')
                    google_link = create_map_link(row['소재지도로명주소'], 'google')
                    
                    if naver_link:
                        st.markdown(f'<a href="{naver_link}" target="_blank"><button style="background-color: #03C75A; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; width: 100%; margin-bottom: 5px;">네이버 지도 🗺️</button></a>', unsafe_allow_html=True)
                    
                    if google_link:
                        st.markdown(f'<a href="{google_link}" target="_blank"><button style="background-color: #4285F4; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; width: 100%;">구글 지도 🌍</button></a>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()