import os

import pytest
from flask import url_for
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

os.environ["FLASK_ENV"] = "development"
BROWSER = os.environ.get("BROWSER", "ChromeHeadless")


@pytest.fixture(scope="module")
def browser(request):
    if BROWSER == "ChromeHeadless":
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        browser = webdriver.Chrome(options=chrome_options)
    else:
        browser = getattr(webdriver, BROWSER)()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


@pytest.mark.usefixtures("live_server")
def test_nav_menu_home_link(browser):
    browser.get(url_for("data_registry", _external=True))
    browser.find_element_by_link_text("GrantNav").click()

    assert browser.current_url == "https://grantnav.threesixtygiving.org/"


@pytest.mark.usefixtures("live_server")
def test_nav_menu_standard_link(browser):
    browser.get(url_for("data_registry", _external=True))
    browser.find_element_by_link_text("The Data Standard").click()

    assert browser.current_url.endswith("/support/standard/")


@pytest.mark.usefixtures("live_server")
def test_body_h1(browser):
    browser.get(url_for("data_registry", _external=True))

    assert (
        "Which funders publish grants data openly?"
        in browser.find_element_by_tag_name("body").text
    )


@pytest.mark.usefixtures("live_server")
def get_card_data(browser):
    browser.get(url_for("data_registry", _external=True))
    cards = []
    for card in browser.find_elements_by_css_selector(
        "ul.card-list li.card-list__item"
    ):
        cards.append(card)

    return cards


@pytest.mark.usefixtures("live_server")
def test_registry_cards(browser):
    cards = get_card_data(browser)
    assert len(cards) == 3


@pytest.mark.usefixtures("live_server")
def test_table_organisations_order(browser):
    browser.get(url_for("data_registry", _external=True))

    headers = []
    for header in browser.find_elements_by_css_selector(".registry-card__pub-name"):
        headers.append(header.text)

    assert len(headers) == 3
    assert headers[0] == "bbc children in need"
    assert headers[1] == "The Big Lottery Fund"
    assert (
        headers[2]
        == "The Corra Foundation, previously called Lloyds TSB Foundation for Scotland"
    )


@pytest.mark.usefixtures("live_server")
def test_table_grants_order(browser):
    browser.get(url_for("data_registry", _external=True))

    headers = []
    for header in browser.find_elements_by_css_selector("td.registry-grant__title"):
        headers.append(header.text)

    assert len(headers) == 4
    assert headers[1] == "Big Lottery Fund - grants data 2017-18"
    assert headers[2] == "Big Lottery Fund - grants data 2015 to 2017"


@pytest.mark.usefixtures("live_server")
def test_table_logos(browser):
    browser.get(url_for("data_registry", _external=True))

    table_data_logos = []
    for table_logo in browser.find_elements_by_css_selector(
        ".registry-card__pub-logo img"
    ):
        table_data_logos.append(table_logo.get_attribute("src"))

    assert len(table_data_logos) == 2
    assert table_data_logos == [
        "http://www.threesixtygiving.org/wp-content/uploads/BBCCiN_CoreLogo.png",
        "http://www.threesixtygiving.org/wp-content/uploads/big-lottery-fund.png",
    ]


@pytest.mark.usefixtures("live_server")
@pytest.mark.parametrize("link_text", ["Terms & Conditions", "Take Down Policy"])
def test_footer_links(browser, link_text):
    browser.get(url_for("data_registry", _external=True))
    browser.find_element_by_link_text(link_text)


@pytest.mark.usefixtures("live_server")
def test_footer_terms_and_conditions_link(browser, live_server):
    browser.get(url_for("data_registry", _external=True))
    browser.find_element_by_link_text("Terms").click()

    assert browser.current_url == live_server.url() + "/terms-conditions"
    assert "Terms & Conditions" in browser.find_element_by_tag_name("h1").text


@pytest.mark.usefixtures("live_server")
def test_footer_take_down_policy_link(browser):
    browser.get(url_for("data_registry", _external=True))
    browser.find_element_by_link_text("Take Down Policy").click()

    assert browser.current_url.endswith("/take-down-policy/")


@pytest.mark.usefixtures("live_server")
def test_footer_license_link(browser):
    browser.get(url_for("data_registry", _external=True))
    link = browser.find_element_by_link_text(
        "Creative Commons Attribution 4.0 International License"
    )

    assert link.get_attribute("href") == "https://creativecommons.org/licenses/by/4.0/"
