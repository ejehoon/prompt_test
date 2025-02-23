from openai import OpenAI
import asyncio
import streamlit as st
import os

class DalleAPI:
    def __init__(self, org_id=None, api_key=None):
        if not org_id or not api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
            
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
