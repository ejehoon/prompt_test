import streamlit as st
import asyncio
import requests
import time
import os
from openai import OpenAI
import jwt

# OpenAI API 클래스
class DalleAPI:
    def __init__(self, org_id=None, api_key=None):
        self.client = OpenAI(
            organization=org_id,
            api_key=api_key
        )

    async def generate_image_async(self, prompt):
        """DALL-E 이미지 비동기 생성"""
        try:
            response = await asyncio.to_thread(
                lambda: self.client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1792x1024",  # 16:9 비율
                    quality="standard",
                    n=1
                )
            )
            return "DALL-E 3", response.data[0].url
        except Exception as e:
            st.error(f"DALL-E 이미지 생성 오류: {str(e)}")
            return "DALL-E 3", None

# Kling API 클래스
class KlingAPI:
    def __init__(self, access_key=None, secret_key=None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.api_url = "https://api.klingai.com/v1/images/generations"

    def _encode_jwt_token(self):
        """JWT 토큰 생성"""
        headers = {
            "alg": "HS256",
            "typ": "JWT"
        }
        payload = {
            "iss": self.access_key,
            "exp": int(time.time()) + 1800,
            "nbf": int(time.time()) - 5
        }
        return jwt.encode(payload, self.secret_key, headers=headers)

    async def generate_image_async(self, prompt):
        """Kling AI 이미지 비동기 생성"""
        try:
            authorization = self._encode_jwt_token()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {authorization}"
            }
            
            data = {
                "model": "kling-v1",
                "prompt": prompt,
                "negative_prompt": "",
                "n": 1,
                "width": 1792,    # 16:9 비율
                "height": 1024    # 16:9 비율
            }
            
            # 이미지 생성 요청
            response = requests.post(self.api_url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                task_id = result["data"]["task_id"]
                
                # 결과 조회를 위한 최대 30번 시도
                for _ in range(30):
                    response = requests.get(
                        self.api_url,
                        headers={"Authorization": f"Bearer {authorization}"},
                        params={"pageSize": 500}
                    )
                    data = response.json()
                    
                    for task in data["data"]:
                        if task["task_id"] == task_id and task["task_status"] == "succeed":
                            return "Kling AI", task["task_result"]["images"][0]['url']
                    
                    await asyncio.sleep(2)  # 2초 대기
                    
            return "Kling AI", None
        except Exception as e:
            st.error(f"Kling AI 이미지 생성 오류: {str(e)}")
            return "Kling AI", None

# API 클래스 초기화
dalle_api = DalleAPI(
    org_id=st.secrets["openai_api"]["org"],
    api_key=st.secrets["openai_api"]["key"]
)
kling_api = KlingAPI(
    access_key=st.secrets["kling_api"]["access_key"],
    secret_key=st.secrets["kling_api"]["secret_key"]
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