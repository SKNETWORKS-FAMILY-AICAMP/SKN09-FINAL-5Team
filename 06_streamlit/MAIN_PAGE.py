import streamlit as st
from PIL import Image
import base64
from io import BytesIO

page_bg_color = '#00102D'
text_color = 'white'
button_color = '#FFA500'

st.markdown(f"""
    <style>
        .stApp {{
            background-color: {page_bg_color};
            color: {text_color};
            min-height: 100vh;
            text-align: center;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
        }}
        .dais-image {{
            display: block;
            margin-left: auto;
            margin-right: auto;
            max-width: 100vw;
            height: 80vh;
            object-fit: contain;
        }}
        /* 상단바(헤더) 색상 및 테두리 */
        header[data-testid="stHeader"] {{
            background-color: {page_bg_color} !important;
            border-bottom: 2px solid {button_color} !important;
        }}
        /* 상단바 버튼 색상, 테두리, 아이콘, 호버 */
        header[data-testid="stHeader"] button,
        header[data-testid="stHeader"] .stButton > button,
        header[data-testid="stHeader"] .stActionButton > button {{
            color: {button_color} !important;
            border: 2px solid {button_color} !important;
            background: transparent !important;
        }}
        header[data-testid="stHeader"] button svg,
        header[data-testid="stHeader"] .stButton > button svg,
        header[data-testid="stHeader"] .stActionButton > button svg {{
            fill: {button_color} !important;
            stroke: {button_color} !important;
        }}
        header[data-testid="stHeader"] button:hover,
        header[data-testid="stHeader"] .stButton > button:hover,
        header[data-testid="stHeader"] .stActionButton > button:hover {{
            background: rgba(255, 165, 0, 0.2) !important;
        }}
        /* 사이드바 전체 배경 및 테두리 */
        section[data-testid="stSidebar"] {{
            background-color: {page_bg_color} !important;
            border-right: 2px solid {button_color} !important;
        }}
        /* 사이드바 내부 텍스트 색상 및 가운데 정렬 */
        section[data-testid="stSidebar"] * {{
            color: {text_color} !important;
            text-align: center !important;
        }}
        /* 사이드바 버튼 텍스트, 테두리, 아이콘 */
        section[data-testid='stSidebar'] button {{
            color: {button_color} !important;
            background-color: transparent !important;
            border-color: {button_color} !important;
        }}
        section[data-testid='stSidebar'] button svg {{
            fill: {button_color} !important;
            stroke: {button_color} !important;
        }}
        section[data-testid='stSidebar'] button:hover {{
            background-color: rgba(255, 165, 0, 0.2) !important;
        }}
        /* 모든 텍스트 가운데 정렬 강제 */
        .stApp, .stApp * {{
            text-align: center !important;
        }}
        /* 메인 영역 버튼도 오렌지 */
        button, .stButton > button, .stActionButton > button {{
            color: {button_color} !important;
            border: 2px solid {button_color} !important;
            background: transparent !important;
        }}
        button svg, .stButton > button svg, .stActionButton > button svg {{
            fill: {button_color} !important;
            stroke: {button_color} !important;
        }}
        button:hover, .stButton > button:hover, .stActionButton > button:hover {{
            background-color: rgba(255, 165, 0, 0.2) !important;
        }}
        /* 사이드바 여는 버튼(햄버거)와 닫는 버튼(X) 아이콘 오렌지 */
        button[title="Open sidebar"] svg,
        button[title="Close sidebar"] svg {{
            fill: {button_color} !important;
            stroke: {button_color} !important;
        }}
        button[title="Open sidebar"], button[title="Close sidebar"] {{
            background: transparent !important;
            border: none !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 이미지 base64 변환 함수
def image_to_base64(image_path):
    img = Image.open(image_path)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

image_path = "./images/DAIS_BI.png"
img_base64 = image_to_base64(image_path)

st.markdown('<div class="container">', unsafe_allow_html=True)

st.header("과학을 즐겁게! 과학 AI 인플루언서 DAIS!")
st.subheader("Divergent AI with Science")

st.markdown(
    f'<img src="data:image/png;base64,{img_base64}" class="dais-image">',
    unsafe_allow_html=True
)

st.markdown(
    f"<p style='color:{text_color}; margin-top:8px; font-size:20px;'>DAIS는 AI 인플루언서를 통해 과학을 즐겁게 만나볼 수 있는 서비스입니다.</p>",
    unsafe_allow_html=True
)

st.markdown('</div>', unsafe_allow_html=True)
