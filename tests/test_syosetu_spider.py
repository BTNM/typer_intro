import logging
import pytest
import time
from unittest.mock import patch
from bs4 import BeautifulSoup
from scrapy.http import HtmlResponse, Request
from src.syosetu_spider.spiders.syosetu_spider import SyosetuSpider

TEST_URL = "https://ncode.syosetu.com"


# Parametrized fixtures for main page data
@pytest.fixture(
    params=[
        ("tests/test_data/ncode_main_page_1.html", "n8611bv"),
        ("tests/test_data/ncode_main_page_2.html", "n2335de"),
    ]
)
def main_page_response(request):
    file_path, novel_code = request.param
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HtmlResponse(url=TEST_URL, body=content, encoding="utf-8"), novel_code


# Parametrized fixtures for chapter page data
@pytest.fixture(
    params=[
        ("tests/test_data/ncode_chapter_page_1.html", "n8611bv", 4),
        ("tests/test_data/ncode_chapter_page_2.html", "n2335de", 137),
    ]
)
def chapter_page_response(request):
    file_path, novel_code, chapter_num = request.param
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    request_obj = Request(
        url=f"{TEST_URL}/{novel_code}/{chapter_num}/",
        meta={"start_time": time.perf_counter()},
    )
    return (
        HtmlResponse(
            url=f"{TEST_URL}/{novel_code}/{chapter_num}/",
            body=content,
            encoding="utf-8",
            request=request_obj,
        ),
        novel_code,
        chapter_num,
    )


# Fixtures for parsing main pages
@pytest.fixture
def parsed_results_main_page(main_page_response):
    response, _ = main_page_response
    spider = SyosetuSpider()
    return list(spider.parse(response)), response


@pytest.fixture
def parse_main_page(main_page_response):
    response, _ = main_page_response
    spider = SyosetuSpider()
    results = list(spider.parse(response))

    soup = BeautifulSoup(response.text, "html.parser")
    return results, soup, response


# Fixtures for parsing chapter pages
@pytest.fixture
def parse_chapter_page(chapter_page_response):
    response, novel_code, chapter_num = chapter_page_response
    spider = SyosetuSpider()
    results = list(spider.parse_chapters(response))
    novel_item = results[0] if results else None

    soup = BeautifulSoup(response.text, "html.parser")
    return novel_item, soup, response, novel_code, chapter_num


# Tests for main page parsing (parametrized)
def test_parse_main_page_novel_description(parse_main_page):
    results, soup, response = parse_main_page

    # Check that correct novel description is extracted
    expected_description = soup.select_one("div#novel_ex.p-novel__summary").text
    assert "novel_description" in results[0].meta
    assert results[0].meta["novel_description"] == expected_description


def test_parse_main_page_first_chapter_link(parse_main_page):
    results, soup, response = parse_main_page

    # Check that correct first chapter link is used
    expected_link = soup.select_one("div.p-eplist__sublist > a")["href"]
    assert results[0].url == f"{TEST_URL}{expected_link}"

    novel_code = results[0].url.split("/")[3]
    expected_novel_code = expected_link.split("/")[1]
    assert novel_code == expected_novel_code


def test_parse_main_page_meta_callback(main_page_response):
    response, _ = main_page_response
    spider = SyosetuSpider()
    results = list(spider.parse(response))

    # Verify request metadata
    assert "start_time" in results[0].meta
    assert isinstance(results[0].meta["start_time"], float)

    # Verify callback is set correctly
    assert results[0].callback == spider.parse_chapters


# Tests for chapter page parsing (parametrized)
def test_parse_chapters_novel_title(parse_chapter_page):
    novel_item, soup, response, novel_code, chapter_num = parse_chapter_page

    if novel_item:
        # Test novel title
        expected_title = soup.select("div.c-announce-box div.c-announce a")[1].text
        assert novel_item["novel_title"] == expected_title


def test_parse_chapters_volume_title(parse_chapter_page):
    novel_item, soup, response, novel_code, chapter_num = parse_chapter_page

    if novel_item:
        # Test volume title
        volume_title = soup.select_one("div.c-announce-box span")
        expected_volume = volume_title.text if volume_title else ""
        assert novel_item["volume_title"] == expected_volume


def test_parse_chapters_start_end_numbers(parse_chapter_page):
    novel_item, soup, response, novel_code, chapter_num = parse_chapter_page

    if novel_item:
        # Test chapter fields
        chapter_start_end = soup.select_one("div.p-novel__number").text
        assert novel_item["chapter_start_end"] == chapter_start_end
        assert novel_item["chapter_number"] == chapter_start_end.split("/")[0]


def test_parse_chapters_title_chapter(parse_chapter_page):
    novel_item, soup, response, novel_code, chapter_num = parse_chapter_page

    if novel_item:
        expected_chapter_title = soup.select_one(
            "h1.p-novel__title.p-novel__title--rensai"
        ).text
        assert novel_item["chapter_title"] == expected_chapter_title


def test_parse_chapters_content_foreword(parse_chapter_page):
    novel_item, soup, response, novel_code, chapter_num = parse_chapter_page

    if novel_item:
        # Test chapter content fields
        foreword = soup.select_one(
            "div.p-novel__body div.js-novel-text.p-novel__text--preface"
        )
        if foreword:
            expected_foreword = "\n".join(p.text for p in foreword.select("p"))
            assert novel_item["chapter_foreword"] == expected_foreword


def test_parse_chapters_content_text(parse_chapter_page):
    novel_item, soup, response, novel_code, chapter_num = parse_chapter_page

    if novel_item:
        chapter_text = soup.select_one(
            "div.p-novel__body div.js-novel-text.p-novel__text"
        )
        if chapter_text:
            expected_text = "\n".join(p.text for p in chapter_text.select("p[id^='L']"))
            assert novel_item["chapter_text"] == expected_text


def test_parse_chapters_content_afterword(parse_chapter_page):
    novel_item, soup, response, novel_code, chapter_num = parse_chapter_page

    if novel_item:
        afterword = soup.select_one(
            "div.p-novel__body div.js-novel-text.p-novel__text--afterword"
        )
        if afterword:
            expected_afterword = "\n".join(p.text for p in afterword.select("p"))
            assert novel_item["chapter_afterword"] == expected_afterword


def test_parse_chapters_next_page_link(chapter_page_response):
    response, novel_code, chapter_num = chapter_page_response
    spider = SyosetuSpider()
    results = list(spider.parse_chapters(response))

    soup = BeautifulSoup(response.text, "html.parser")
    next_page = soup.select_one("div.c-pager a.c-pager__item--next")

    if next_page and len(results) > 1:
        next_request = results[1]
        expected_url = next_page["href"]

        assert next_request.url.endswith(expected_url)
        assert next_request.callback == spider.parse_chapters


def test_spider_crawl_chapters_content(parse_chapter_page):
    novel_item, soup, response, novel_code, chapter_num = parse_chapter_page

    if novel_item:
        # Test foreword content
        foreword = soup.select_one(
            "div.p-novel__body div.js-novel-text.p-novel__text--preface"
        )
        if foreword:
            expected_foreword = "\n".join(p.text for p in foreword.select("p"))
            assert novel_item["chapter_foreword"] == expected_foreword
        else:
            # Field may not be present if there's no foreword
            assert novel_item.get("chapter_foreword", "") == ""

        # Test main chapter text content
        chapter_text = soup.select_one(
            "div.p-novel__body div.js-novel-text.p-novel__text"
        )
        if chapter_text:
            expected_text = "\n".join(p.text for p in chapter_text.select("p[id^='L']"))
            assert novel_item["chapter_text"] == expected_text

        # Test afterword content
        afterword = soup.select_one(
            "div.p-novel__body div.js-novel-text.p-novel__text--afterword"
        )
        if afterword:
            expected_afterword = "\n".join(p.text for p in afterword.select("p"))
            assert novel_item["chapter_afterword"] == expected_afterword
        else:
            # Field may not be present if there's no afterword
            assert novel_item.get("chapter_afterword", "") == ""
