#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-genai",
#     "requests",
#     "beautifulsoup4",
#     "python-dotenv",
# ]
# ///

# To run this code you need to install the following dependencies:
# uv run translate_essays.py

import os
import time
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY 환경 변수를 설정해주세요.")

def get_all_essays_info(base_url="https://www.paulgraham.com/"):
    """폴 그레이엄의 에세이 목록 페이지에서 모든 에세이의 (URL, 제목)을 가져옵니다."""
    articles_url = base_url + "articles.html"
    essays = []
    try:
        response = requests.get(articles_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for a in soup.select('table a[href$=".html"]'):
            url = base_url + a['href']
            title = a.get_text(strip=True)
            essays.append((url, title))
        
        # index.html, rss.html 제거
        essays = [e for e in essays if not (e[0].endswith("index.html") or e[0].endswith("rss.html"))]

        # 폴 그레이엄 추천 에세이 제거
        unique_essays = []
        seen_urls = set()
        for url, title in reversed(essays):
            if url not in seen_urls:
                unique_essays.append((url, title))
                seen_urls.add(url)
        essays = list(reversed(unique_essays))
        
        print(f"총 {len(essays)}개의 에세이 링크를 찾았습니다.")
        return essays
    except requests.exceptions.RequestException as e:
        print(f"에세이 목록을 가져오는 데 실패했습니다: {e}")
        return []

def get_essay_text(url):
    """개별 에세이 URL에서 본문 텍스트를 추출합니다."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        body = soup.find('font')
        if body:
            return body.get_text(separator='\n', strip=True)
        return None
    except requests.exceptions.RequestException as e:
        print(f"'{url}'에서 본문을 가져오는 데 실패했습니다: {e}")
        return None

def translate_essay_with_gemini(essay_title, essay_text):
    """Gemini API를 사용하여 에세이 전문을 번역합니다."""
    client = genai.Client(
        api_key=API_KEY,
    )
    model = "gemini-2.5-flash"
    
    prompt = f"""
    아래는 폴 그레이엄의 에세이 '{essay_title}'의 전문입니다.
    이 글을 한국 문화권의 한국어 독자들이 읽기 쉽고 자연스럽게 번역해주세요.
    1. 에세이의 내용 말고 다른 쓸데없는 응답을 하지 마세요 (네 알겠습니다! 등).
    2. 에세에의 타이틀은 항상 '한국어 (영어)'처럼 괄호 안에 영어 원문을 그대로 써주세요.
    3. 영어 용어는 한국인들이 자주 사용하는 용어면 바로 번역하고, 그렇지 않으면 영어를 병기해주세요. 그렇다고 해서, 스타트업에 관심있는 독자에게 너무 쉬운 용어를 쓸데없이 한영 병기하지 마세요.
    4. 최종 아웃풋은 Markdown 형식으로 제공해주세요. 예를 들어, 제목은 '# 제목' 과 같이 마크다운 제목 레벨 1로 시작해야 합니다.
    5. [1], [2] 등 각주를 표현하는 문자는 이전 문장 뒤에 바로 붙여주세요. 원문에는 띄어쓰기가 있을테지만 무시하라는 소립니다.

    --- 원문 시작 ---
    {essay_text}
    --- 원문 끝 ---
    """
    
    try:
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            thinking_config = types.ThinkingConfig(
                thinking_budget=0,
            ),
        )

        response = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response += chunk.text
        return response
    except Exception as e:
        return f"번역 중 오류 발생: {e}"

def main():
    """메인 실행 함수"""
    output_dir = "./essays"
    os.makedirs(output_dir, exist_ok=True)

    essays_info  = get_all_essays_info()

    if not essays_info:
        print("번역할 에세이를 찾지 못했습니다.")
        return

    for i, (url, essay_title) in enumerate(essays_info):
        filename_base = url.split('/')[-1].replace('.html', '')
        
        print(f"\n--- [{i+1}/{len(essays_info)}] '{essay_title}' 번역 시작 ---")
        
        original_text = get_essay_text(url)
        
        if original_text:
            translated_text = translate_essay_with_gemini(essay_title, original_text)
            
            file_path = os.path.join(output_dir, f"{filename_base}.md")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(translated_text)
                print(f"--- '{essay_title}' 번역 완료 ---")
                print(f"번역된 에세이를 '{file_path}'에 저장했습니다.")
            except IOError as e:
                print(f"파일 저장 중 오류 발생: {e}")
        else:
            print(f"'{essay_title}'의 본문이 비어있어 번역을 건너뜁니다.")
        
        time.sleep(5) 

if __name__ == "__main__":
    main()