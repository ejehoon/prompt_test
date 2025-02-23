import time
import jwt
import requests
import asyncio
import streamlit as st

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
