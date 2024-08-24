import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import json

# Константа для ограничения количества обрабатываемых страниц
MAX_PAGES = 1000


def get_domain(url):
    return urlparse(url).netloc


def normalize_url(url):
    return urldefrag(url)[0]


def extract_text_from_main_column(soup):
    main_column = soup.find('div', class_='inz_main_column')
    if main_column:
        # Удаляем все скрипты и стили из основного блока
        for script_or_style in main_column(["script", "style"]):
            script_or_style.extract()

        # Получаем текст
        text = main_column.get_text(separator='\n', strip=True)

        # Удаляем пустые строки и лишние пробелы
        lines = (line.strip() for line in text.splitlines() if line.strip())
        return '\n'.join(lines)
    return ""


def parse_site_content(start_url):
    domain = get_domain(start_url)
    visited = set()
    to_visit = [start_url]
    site_content = {}

    while to_visit and len(visited) < MAX_PAGES:
        current_url = to_visit.pop(0)
        current_url = normalize_url(current_url)

        if current_url in visited:
            continue

        print(f"Парсинг: {current_url}")
        visited.add(current_url)

        try:
            response = requests.get(current_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            content = extract_text_from_main_column(soup)
            if content:  # Сохраняем только если контент не пустой
                site_content[current_url] = content

            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(current_url, href)
                full_url = normalize_url(full_url)

                if get_domain(full_url) == domain and full_url not in visited and full_url not in to_visit:
                    to_visit.append(full_url)

        except Exception as e:
            print(f"Ошибка при парсинге {current_url}: {e}")

    return site_content


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    start_url = "https://www.immigration.govt.nz/new-zealand-visas"
    content = parse_site_content(start_url)

    print("\nСодержимое сайта:")
    for url, text in content.items():
        print(f"\n{url}")
        print(f"Текст (первые 200 символов): {text[:200]}...")

    print(f"\nВсего проанализировано уникальных страниц с содержимым: {len(content)}")

    # Сохраняем результаты в JSON файл
    save_to_json(content, 'site_content.json')
    print(f"\nРезультаты сохранены в файл 'site_content.json'")