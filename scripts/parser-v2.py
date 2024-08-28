import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import json
import os
import argparse


def get_domain(url):
    return urlparse(url).netloc


def normalize_url(url):
    return urldefrag(url)[0]


def is_pdf_link(url):
    return url.lower().endswith('.pdf')

def should_skip_url(url):
    return 'opsmanual' in url.lower() or is_pdf_link(url)

def extract_text_from_element(element):
    if element:
        # Recursively extract text from all child elements
        texts = []
        for child in element.descendants:
            if isinstance(child, str) and child.strip():
                texts.append(child.strip())
            elif child.name == 'br':
                texts.append('\n')

        # Join all texts
        return ' '.join(texts)
    return ""


def extract_main_content(soup):
    page_body = soup.find('div', class_='inz_page_body')
    if page_body:
        # Удаляем left_hand_nav, если он существует
        left_nav = page_body.find('div', class_='left_hand_nav')
        if left_nav:
            left_nav.extract()

        # Ищем inz_main_column внутри очищенного page_body
        main_column = page_body.find('div', class_='inz_main_column')
        if main_column:
            return extract_text_from_element(main_column)
    return ""


def parse_site_content(start_url, max_pages=None):
    domain = get_domain(start_url)
    visited = set()
    to_visit = [start_url]
    site_content = {}

    while to_visit and (max_pages is None or len(visited) < max_pages):
        current_url = to_visit.pop(0)
        current_url = normalize_url(current_url)

        if current_url in visited or is_pdf_link(current_url):
            continue

        print(f"Parsing: {current_url}")
        visited.add(current_url)

        try:
            response = requests.get(current_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            header = extract_text_from_element(soup.find('header', class_='inz_page_header'))
            main_content = extract_main_content(soup)

            if header or main_content:  # Сохраняем только если есть хоть какой-то контент
                site_content[current_url] = {
                    "header": header,
                    "main_content": main_content
                }

            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(current_url, href)
                full_url = normalize_url(full_url)

                if (get_domain(full_url) == domain and
                        full_url not in visited and
                        full_url not in to_visit and
                        not should_skip_url(full_url)):
                    to_visit.append(full_url)

        except Exception as e:
            print(f"Error parsing {current_url}: {e}")

    return site_content


def save_to_json(data, filename):
    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Create the full path for the file
    filepath = os.path.join('data', filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse website content and save to JSON.")
    parser.add_argument("-o", "--output", default="site_content.json",
                        help="Output filename (default: site_content.json)")
    parser.add_argument("-m", "--max-pages", type=int, default=100,
                        help="Maximum number of pages to parse (default:100)")
    parser.add_argument("--parse-all", action="store_true",
                        help="Parse all pages without limit")
    args = parser.parse_args()

    start_url = "https://www.immigration.govt.nz/new-zealand-visas"
    
    if args.parse_all:
        content = parse_site_content(start_url)
    else:
        content = parse_site_content(start_url, args.max_pages)

    print("\nSite content:")
    if args.max_pages and len(content) >= args.max_pages:
        print(f"\nWARNING: Max pages limit ({args.max_pages}) reached. Some pages may not have been parsed.")
    for url, page_content in content.items():
        print(f"\n{url}")
        print(f"Header: {page_content['header'][:100]}...")
        print(f"Main content (first 200 characters): {page_content['main_content'][:200]}...")

    print(f"\nTotal unique pages analyzed with content: {len(content)}")

    # Save results to JSON file in the data folder
    save_to_json(content, args.output)
    print(f"\nResults saved to file 'data/{args.output}'")
