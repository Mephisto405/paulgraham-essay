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
import re
from functools import wraps
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from dotenv import load_dotenv
import argparse

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

def retry_on_quota_exhaustion(max_retries=5, default_delay=60):
    """
    Gemini API의 'RESOURCE_EXHAUSTED' 오류 발생 시, 지정된 횟수만큼 재시도하는 데코레이터.
    오류 메시지에 포함된 'retryDelay'를 파싱하여 대기 시간으로 사용합니다.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except genai.errors.ClientError as e:
                    retries += 1
                    
                    retry_delay = default_delay
                    error_str = str(e)
                    match = re.search(r"'retryDelay':\s*'(\d+)s'", error_str)
                    
                    if match:
                        retry_delay = int(match.group(1))

                    print(f"API 할당량이 소진되었습니다. {retry_delay}초 후 재시도합니다... (시도 {retries}/{max_retries})")
                    time.sleep(retry_delay + 1)
            
            print(f"최대 재시도 횟수({max_retries})를 초과했습니다. API 호출에 최종 실패했습니다.")
            raise e

        return wrapper
    return decorator

@retry_on_quota_exhaustion(max_retries=3)
def translate_essay_with_gemini(essay_title, essay_text):
    """Gemini API를 사용하여 에세이 전문을 번역합니다."""
    client = genai.Client(
        api_key=API_KEY,
    )
    model = "gemini-2.5-flash-lite"
    
    prompt = f"""
    아래는 폴 그레이엄의 에세이 '{essay_title}'의 전문입니다.
    이 글을 한국 문화권의 한국어 독자들이 읽기 쉽고 자연스럽게 번역해주세요.
    1. 에세이의 내용 말고 다른 쓸데없는 응답을 하지 마세요 (네 알겠습니다! 등). 
    2. -요, -습니다 등 경어체를 써주세요.
    2. 에세에의 타이틀은 항상 '한국어 (영어)'처럼 괄호 안에 영어 원문을 그대로 써주세요.
    3. 영어 용어는 한국인들이 자주 사용하는 용어면 바로 번역하고, 그렇지 않으면 영어를 병기해주세요. 그렇다고 해서, 스타트업에 관심있는 독자에게 너무 쉬운 용어를 쓸데없이 한영 병기하지 마세요.
    4. 최종 아웃풋은 Markdown 형식으로 제공해주세요. 예를 들어, 제목은 '# 제목' 과 같이 마크다운 제목 레벨 1로 시작해야 합니다.
    5. 각주를 표현하는 문자 [^n] (n은 자연수)는 이전 문장의 바로 뒤에 바로 붙여주세요. 때때로 이전 문장과 newline만큼의 차이가 있을 수 있는데, 그것을 교정해 달라는 의미입니다.
    6. 작가의 의도가 가장 잘 드러나면서도 한국어적으로 자연스럽게 번역해주세요. 만약 이 목표가 상충한다면, 작가의 의도를 살리는 방향으로 번역해주세요.
    7. 다음과 같은 포맷으로 번역해주세요. Optional은 영어 원문에 있는 경우에만 채워넣으면 됩니다.

    --- 예시 포맷 시작 ---
    # {{제목}}

    {{스타트업을 시작하고 싶나요? Y Combinator에서 투자를 받으세요. 등과 같은 광고 멘트. optional}}

    {{20XX}}년 {{YY}}월

    ## {{소제목. optional}}

    {{어떤 문장입니다.}}{{[^n] 형식의 주석 표시. n은 자연수. optional}} {{다른 문장입니다.}}

    {{감사의 말. 주석 앞에 옵니다. optional}}

    {{[^n]: n번째 주석에 관한 설명. markdown-it-footnote 를 이용하기 위해 콜론이 꼭 있어야 함. 출력의 가장 마지막에 위치해야 합니다. 별도 섹션으로 나누지 않습니다. 렌더링 시 자동으로 구분됩니다. optional}}
    --- 예시 포맷 끝 ---

    --- 원문 시작 ---
    {essay_text}
    --- 원문 끝 ---
    """
    
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
            thinking_budget=-1,
        ),
    )

    response = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        response += str(chunk.text if chunk.text != None else "")
    return response

def main():
    """메인 실행 함수: 선택적 번역 또는 전체 번역을 수행합니다."""
    
    parser = argparse.ArgumentParser(description="폴 그레이엄 에세이 번역 스크립트")
    parser.add_argument(
        "--all",
        action="store_true",
        help="기존 번역 상태와 상관없이 모든 에세이를 다시 번역합니다."
    )
    args = parser.parse_args()

    output_dir = "./essays"
    os.makedirs(output_dir, exist_ok=True)

    essays_info = get_all_essays_info()

    if not essays_info:
        print("번역할 에세이를 찾지 못했습니다.")
        return

    for i, (url, essay_title) in enumerate(essays_info):
        filename_base = url.split('/')[-1].replace('.html', '')
        file_path = os.path.join(output_dir, f"{filename_base}.md")
        
        print(f"\n--- [{i+1}/{len(essays_info)}] '{essay_title}' 처리 시작 ---")

        should_translate = False
        if args.all:
            print("'--all' 옵션이 지정되어 강제로 번역을 실행합니다.")
            should_translate = True
        else:
            if not os.path.exists(file_path):
                print(f"번역 파일 '{file_path}'이(가) 존재하지 않아 새로 번역합니다.")
                should_translate = True
            else:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if content.strip() == "" or content.startswith("번역 중 오류 발생"):
                        print(f"이전에 실패한 번역('{file_path}')을 재시도합니다.")
                        should_translate = True
                    else:
                        print(f"이미 성공적으로 번역된 파일('{file_path}')입니다. 건너뜁니다.")
                except Exception as e:
                    print(f"파일 '{file_path}' 확인 중 오류 발생: {e}. 안전을 위해 재번역합니다.")
                    should_translate = True

        if should_translate:
            original_text = get_essay_text(url)
            
            if not original_text:
                print(f"'{essay_title}'의 원문이 비어있어 건너뜁니다.")
                continue

            try:
                translated_text = translate_essay_with_gemini(essay_title, original_text)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(translated_text)
                print(f"--- '{essay_title}' 번역 및 저장 완료 ---")
                print(f"번역된 에세이를 '{file_path}'에 저장했습니다.")

            except Exception as e:
                print(f"'{essay_title}' 번역 중 최종 오류가 발생했습니다.")
                print(f"발생한 오류: {e}")
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("번역 중 오류 발생\n\n")
                        f.write(f"오류 발생 시각: {time.ctime()}\n")
                        f.write(f"에세이: {essay_title}\n")
                        f.write(f"오류 내용: {str(e)}\n")
                    print(f"오류 상태를 '{file_path}'에 기록했습니다.")
                except IOError as io_e:
                    print(f"오류 상태 파일 작성에 실패했습니다: {io_e}")
            
            print("다음 요청까지 2초 대기합니다...")
            time.sleep(2)

if __name__ == "__main__":
    main()