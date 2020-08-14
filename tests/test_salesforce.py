from registry.salesforce import clean_object, clean_output
from tests.samples.salesforce import API_OUTPUT, LICENSE_OBJECT


def test_only_returns_approved_datasets():
    response = clean_output(API_OUTPUT)

    assert len(response) == 2
    publishers = [response[0]["publisher"]["name"], response[1]["publisher"]["name"]]
    assert "A B Charitable Trust" in publishers
    assert "ARCADIA" not in publishers
    assert "Barrow Cadbury Trust" in publishers


def test_correct_output():
    response = clean_output(API_OUTPUT)[0]

    expected_response = {
        "title": "Open Programme grants awarded from 2015 until February 2018",
        "description": "",
        "identifier": "a001p00000zgyHZAAY",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "license_name": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "issued": "2018-06-21",
        "modified": "2018-08-03T10:26:35.000+0000",
        "publisher": {
            "name": "A B Charitable Trust",
            "website": "http://abcharitabletrust.org.uk/",
            "logo": "",
            "prefix": "360G-ABCT",
        },
        "distribution": [
            {
                "downloadURL": "http://abcharitabletrust.org.uk/data/abct-data-february-2018.xlsx",
                "accessURL": "http://abcharitabletrust.org.uk/awards.htm",
                "title": "Open Programme grants awarded from 2015 until February 2018",
            }
        ],
    }

    assert len(response) == 9
    assert response == expected_response


def test_description_returns_empty_string_if_none():
    response = clean_output(API_OUTPUT)[0]

    assert response["description"] == ""


def test_logo_returns_empty_string_if_none():
    response = clean_output(API_OUTPUT)[0]

    assert response["publisher"]["logo"] == ""


def test_website_returns_empty_string_if_none():
    response = clean_output(API_OUTPUT)[1]

    assert response["publisher"]["website"] == ""


def test_clean_object():
    response = clean_object(LICENSE_OBJECT)

    assert response == {
        "name": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "uRL": "https://creativecommons.org/licenses/by/4.0/",
    }
