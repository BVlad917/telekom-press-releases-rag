import os
import time
import json
import shutil
import requests
from pathlib import Path
from tqdm.auto import tqdm
from tabulate import tabulate
from unidecode import unidecode
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag

from constants import *


def get_soup(url: str, params: dict = None, headers: dict = None) -> BeautifulSoup:
    """ Get the HTML content of a webpage and parse it into a BeautifulSoup instance. """
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def scrape_article_urls() -> list[str]:
    """ Retrieve the list of press releases URLs that we are interested in. """
    article_urls = set()

    page = 0
    with tqdm(total=PRESS_RELEASES_TARGET_COUNT, desc="Scraping press release article URLs") as pbar:
        while len(article_urls) < PRESS_RELEASES_TARGET_COUNT:
            params = {
                'viewtype': 'asFeedList',
                'page_active': page,
                '_': int(time.time() * 1000)  # Cache-busting parameter
            }

            soup = get_soup(PRESS_RELEASES_URL, params=params, headers=HEADERS)
            article_tags_on_page = soup.find_all('a', class_='media-link', href=True)
            for article_tag in article_tags_on_page:
                full_article_url = urljoin(TELEKOM_BASE_URL, article_tag['href'])
                article_urls.add(full_article_url)
                pbar.update(1)

                if len(full_article_url) == PRESS_RELEASES_TARGET_COUNT:
                    break

            page += 1
    article_urls = list(article_urls)
    return article_urls[:PRESS_RELEASES_TARGET_COUNT]


def serialize_table_to_text(table_tag: Tag) -> str:
    """ Convert an HTML table into a simplified text format. """
    rows = []
    for row in table_tag.find_all('tr'):
        cols = [ele.text.strip() for ele in row.find_all(['th', 'td'])]

        if len(cols) > 0:
            rows.append(cols)

    return tabulate(rows[1:], headers=rows[0], tablefmt="grid")


def html_aware_chunker(html_content: Tag) -> list[str]:
    """
    Chunk content based on its HTML structure (p, ul, h2, table).
    Prepend the last seen H2 to subsequent chunks for context.
    """
    content_area = html_content.find('div', class_='richtext')

    chunks = []
    last_header_text = ""

    for tag in content_area.find_all(['p', 'ul', 'h2', 'div'], recursive=False):
        # The footnotes are always the same on each page, and they are not related to the content of the article
        if 'footnote' in tag.get('class', []):
            continue

        # Capture headers to prepend to subsequent chunks
        if tag.name == 'h2':
            last_header_text = tag.get_text(strip=True)
            continue  # Don't add the header as its own chunk

        text = ""

        # Handle paragraphs and lists
        if tag.name in ['p', 'ul']:
            text = tag.get_text(strip=True)
        # Handle tables
        elif tag.name == 'div' and tag.find('table'):
            text = serialize_table_to_text(tag.find('table'))

        if text:
            # Prepend the last header for context
            chunk_content = f"{last_header_text}: {text}" if last_header_text else text

            # Use all ASCII characters for easier processing and use single quotes to avoid formatting issues
            chunk_content = unidecode(chunk_content).replace('"', "'")
            chunks.append(chunk_content)

    return chunks


def clear_directory(path):
    """ Delete all files and directories in the given directory without deleting the directory itself. """
    for item in Path(path).iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def scrape_articles_content(article_urls: list[str]):
    """ Retrieve the content of the given list of press release URLs, parse that content into a useful format, and save it to disk. """
    # Delete the previous articles, if any
    os.makedirs(PRESS_RELEASES_DIR, exist_ok=True)
    clear_directory(PRESS_RELEASES_DIR)

    for idx, article_url in enumerate(tqdm(article_urls, desc="Scraping the content of the articles")):
        soup = get_soup(article_url)
        main_section = soup.find('main')

        # Split the content of the article according to the page structure (paragraphs, headers, tables, etc)
        article_content = main_section.find('section')
        article_content_chunks = html_aware_chunker(article_content)

        # Get the date, title, and author of the article
        article_date = main_section.find('time').get_text(separator='\n', strip=True)
        article_title = soup.find('title').get_text(separator='\n', strip=True)

        # Some articles don't have authors
        article_author_tag = main_section.find('address')
        if article_author_tag is None:
            article_author = None
        else:
            article_author = unidecode(article_author_tag.get_text(separator='\n', strip=True))

        # Use just ASCII characters instead of UniCode
        article_title = unidecode(article_title)
        article_date = unidecode(article_date)

        # Concatenate all the article information in one file
        article_dict = {
            "title": article_title,
            "date": article_date,
            "author": article_author,
            "link": article_url,
            "content": article_content_chunks
        }

        full_file_path = os.path.join(PRESS_RELEASES_DIR, f"press_release_{idx}.json")
        with open(full_file_path, 'w') as fp:
            json.dump(article_dict, fp, indent=4)


if __name__ == "__main__":
    articles_urls = scrape_article_urls()
    scrape_articles_content(articles_urls)
