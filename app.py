import streamlit as st
import asyncio
import requests
import time
from dotenv import load_dotenv
import os
from dalle import DalleAPI
from Kling import KlingAPI

# 환경 변수 로드
load_dotenv()

# API 클래스 초기화
dalle_api = DalleAPI(
    org_id=os.getenv("OPENAI_ORG"),
    api_key=os.getenv("OPENAI_API_KEY")
)
kling_api = KlingAPI(
    access_key=os.getenv("KLING_ACCESS_KEY"),
    secret_key=os.getenv("KLING_SECRET_KEY")
)

def main():
    # 페이지 설정
    st.set_page_config(
        page_title="AI 이미지 생성 비교",
        layout="wide"
    )

    # 사이드바 설정
    with st.sidebar:
        st.title("AI 모델 선택")
        st.write("테스트할 AI 모델을 선택하세요")
        
        # 모델 선택 체크박스
        models = {
            "DALL-E 3": st.checkbox("DALL-E 3", value=True),
            "Kling AI": st.checkbox("Kling AI", value=True),
            "Hailuo": st.checkbox("hailuo (준비중)", disabled=True),
            "Flux": st.checkbox("Flux (준비중)", disabled=True),
            "Midjourney": st.checkbox("Midjourney (준비중)", disabled=True)
        }
        
        st.divider()
        st.subheader("⚙️ 설정")
        st.info("미구현.(현재 16:9로 1792:1024 비율로 생성)")

    # 메인 영역
    st.title("AI 이미지 생성 비교")
    st.write("선택된 모델 비교")

    # 프롬프트 입력
    prompt = st.text_area(
        "프롬프트를 입력하세요:",
        placeholder="예: a cute dog playing in a garden with flowers",
        height=100
    )

    # 생성 버튼
    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        generate_button = st.button("이미지 생성", use_container_width=True)

    if generate_button and prompt:
        selected_models = [model for model, selected in models.items() if selected and not model.endswith("(준비중)")]
        if not selected_models:
            st.warning("최소 하나의 모델을 선택해주세요.")
            return
            
        # 결과 컨테이너 생성
        st.write("### 생성된 이미지 결과")
        result_container = st.container()
        
        async def generate_images():
            tasks = []
            if "DALL-E 3" in selected_models:
                tasks.append(dalle_api.generate_image_async(prompt))
            if "Kling AI" in selected_models:
                tasks.append(kling_api.generate_image_async(prompt))
            
            results = await asyncio.gather(*tasks)
            generated_images = {model: url for model, url in results if url}
            
            # 결과 표시
            with result_container:
                cols = st.columns(3)
                for idx, (model_name, image_url) in enumerate(generated_images.items()):
                    col_idx = idx % 3
                    with cols[col_idx]:
                        st.caption(f"**{model_name}**의 결과")
                        
                        image_container = st.container()
                        with image_container:
                            st.image(image_url, use_container_width=True, output_format="JPEG")
                            
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                st.download_button(
                                    "다운로드",
                                    data=requests.get(image_url).content,
                                    file_name=f"{model_name.lower().replace(' ', '_')}_{int(time.time())}.png",
                                    mime="image/png",
                                    use_container_width=True
                                )
                            with col2:
                                if st.button("크게 보기", key=f"view_{idx}", use_container_width=True):
                                    st.session_state[f'show_large_{idx}'] = True
                        
                        if st.session_state.get(f'show_large_{idx}', False):
                            with st.expander("큰 이미지 보기", expanded=True):
                                st.image(image_url, use_container_width=True)
                                if st.button("닫기", key=f"close_{idx}"):
                                    st.session_state[f'show_large_{idx}'] = False
                
                with st.expander("프롬프트 정보", expanded=False):
                    st.text_area("사용된 프롬프트:", value=prompt, height=100, disabled=True)
                    st.caption(f"생성 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        with st.spinner("이미지 생성 중..."):
            asyncio.run(generate_images())

    elif generate_button and not prompt:
        st.warning("프롬프트를 입력해주세요!")

    st.divider()
    st.caption("© 2024 AI Image Generation Comparison. All rights reserved.")

if __name__ == "__main__":
    main()