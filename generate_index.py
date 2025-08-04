#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
#     "beautifulsoup4",
# ]
# ///

import requests
from bs4 import BeautifulSoup

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
    
def get_translated_title(filename_base, original_title, essays_dir="./essays"):
    try:
        with open(f"{essays_dir}/{filename_base}.md", "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line.startswith("#"):
                return first_line.lstrip("# ").strip()
    except FileNotFoundError:
        print(f"경고: '{filename_base}.md' 파일을 찾을 수 없습니다. 원본 제목을 사용합니다.")
        return original_title
    return original_title
        
def create_index_html(essays_info, essays_dir="./essays"):
    """에세이 정보 목록을 기반으로 index.html 파일을 생성합니다."""

    html_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>폴 그레이엄 에세이 (한국어 번역)</title>
    <link rel="stylesheet" href="style.css">

    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-0NXVCDMDN2"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', 'G-0NXVCDMDN2');
    </script>
</head>
<body>
    <div class="container">
        <header>
            <h1>폴 그레이엄 에세이 (한국어 번역)</h1>
            <p>이 페이지는 <a href="https://www.paulgraham.com/articles.html" target="_blank" rel="noopener noreferrer">폴 그레이엄의 에세이</a>를 Gemini API를 이용해 한국어로 번역한 모음입니다. 목록은 원본 사이트의 순서를 따릅니다.</p>
        </header>
        <main>
"""

    # 추천 에세이의 번역된 제목 가져오기
    title_greatwork = get_translated_title('greatwork', 'How to Do Great Work', essays_dir)
    title_kids = get_translated_title('kids', 'Having Kids', essays_dir)
    title_selfindulgence = get_translated_title('selfindulgence', 'How to Lose Time and Money', essays_dir)
    
    # 추천 에세이 문구 추가
    html_content += f"""            <p class="recommendation">무엇부터 읽어야 할지 고민된다면, <a href="essay_template.html?essay=greatwork">{title_greatwork}</a>, <a href="essay_template.html?essay=kids">{title_kids}</a>, 또는 <a href="essay_template.html?essay=selfindulgence">{title_selfindulgence}</a>를 먼저 읽어보세요.</p>
            <ul class="essay-list">
"""

    for url, original_title in essays_info:
        filename_base = url.split('/')[-1].replace('.html', '')
        translated_title = get_translated_title(filename_base, original_title, essays_dir)
        
        # 각 에세이 링크는 템플릿 페이지를 가리키고, ?essay= 파라미터로 파일명을 전달합니다.
        html_content += f'                <li><a href="essay_template.html?essay={filename_base}">{translated_title}</a></li>\n'

    html_content += """            </ul>
        </main>
        <footer>
            <p>Generated for educational purposes. All original content by Paul Graham.</p>
        </footer>
    </div>
</body>
</html>"""

    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("\n'index.html' 파일이 성공적으로 생성되었습니다.")
    except IOError as e:
        print(f"index.html 파일 저장 중 오류 발생: {e}")


if __name__ == "__main__":
    essays_to_list = get_all_essays_info()
    if essays_to_list:
        create_index_html(essays_to_list)

