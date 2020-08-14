import os

from registry.registry import (
    RegistryFile,
    format_date,
    format_value,
    get_check_cross_symbol,
    get_currency_symbol,
    get_data_by_prefix,
    get_data_sorted_by_prefix,
    get_file_type,
    get_raw_data,
    sort_data,
)
from tests.samples.registry_scvo_data import SCVO_DATA

os.environ["FLASK_ENV"] = "development"


def test_get_currency_symbol_with_symbol():
    response = get_currency_symbol("GBP", {"currency_symbol": "&pound;"})

    assert response == "&pound;"


def test_get_currency_symbol_without_key():
    response = get_currency_symbol("GBP", {})

    assert response == "GBP"


def test_get_currency_symbol_without_symbol_with_currency():
    response = get_currency_symbol("GBP", {"currency_symbol": ""})

    assert response == "GBP"


def test_get_currency_symbol_without_symbol_without_currency():
    response = get_currency_symbol("", {"currency_symbol": ""})

    assert response == ""


def test_format_value_integer():
    response = format_value(492793844)

    assert response == "492,793,844"


def test_format_value_float():
    response = format_value(492793844.630005)

    assert response == "492,793,844.63"


def test_format_value_string():
    response = format_value("492793844")

    assert response == "492793844"


def test_format_value_none():
    response = format_value(None)

    assert response is None


def test_format_date_correct_date_param():
    response = format_date("2018-07-23")

    assert response == "Jul '18"


def test_format_date_empty_string():
    response = format_date("")

    assert response == ""


def test_format_date_wrong_date_param():
    response = format_date("23-07-2018")

    assert response == "23-07-2018"


def test_get_total_value_one_currency():
    r = RegistryFile(
        {
            "datagetter_aggregates": {
                "currencies": {
                    "GBP": {"currency_symbol": "&pound;", "total_amount": 257947}
                }
            }
        }
    )
    response = r.total_value

    assert response == ["&pound; 257,947"]


def test_get_total_value_multiple_currencies():
    r = RegistryFile(
        {
            "datagetter_aggregates": {
                "currencies": {
                    "GBP": {"currency_symbol": "&pound;", "total_amount": 257947},
                    "CHP": {"currency_symbol": "", "total_amount": 234.898000},
                }
            }
        }
    )
    response = r.total_value

    assert response == ["&pound; 257,947", "CHP 235"]


def test_get_total_value_empty_dict():
    r = RegistryFile({"datagetter_aggregates": {"currencies": {}}})
    response = r.total_value

    assert response == []


def test_get_total_value_currency_symbol_key_missing():
    r = RegistryFile(
        {"datagetter_aggregates": {"currencies": {"GBP": {"total_amount": 257947}}}}
    )
    response = r.total_value

    assert response == ["GBP 257,947"]


def test_get_total_value_total_amount_key_missing():
    r = RegistryFile(
        {
            "datagetter_aggregates": {
                "currencies": {
                    "GBP": {"currency_symbol": "&pound;"},
                    "CHP": {"currency_symbol": "", "total_amount": 234.898000},
                }
            }
        }
    )
    response = r.total_value

    assert response == ["CHP 235"]


def test_get_total_value_total_amount_empty_string():
    r = RegistryFile(
        {
            "datagetter_aggregates": {
                "currencies": {
                    "GBP": {"currency_symbol": "&pound;", "total_amount": 257947},
                    "CHP": {"currency_symbol": "", "total_amount": ""},
                }
            }
        }
    )
    response = r.total_value

    assert response == ["&pound; 257,947"]


def test_get_total_value_rounded_value():
    r = RegistryFile(
        {"datagetter_aggregates": {"currencies": {"GBP": {"total_amount": 257947.49}}}}
    )
    response = r.total_value

    assert response == ["GBP 257,947"]


def test_get_check_symbol():
    response = get_check_cross_symbol(True)

    assert response == "&#x2713;"


def test_get_cross_symbol():
    response = get_check_cross_symbol(False)

    assert response == "&#x2715;"


def test_get_check_cross_symbol_return_string():
    response = get_check_cross_symbol("true")

    assert response == ""


def test_get_file_type_csv():
    response = get_file_type("csv")

    assert response == "CSV"


def test_get_file_type_json():
    response = get_file_type("json")

    assert response == "json"


def test_get_file_type_xlsx():
    response = get_file_type("xlsx")

    assert response == "Excel"


def test_get_file_type_file():
    response = get_file_type("Json")

    assert response == "file"


def test_get_file_type_empty_strings():
    response = get_file_type("")

    assert response == "file"


def test_get_file_type_none():
    response = get_file_type(None)

    assert response == "file"


# def test_get_licence_not_acceptable():
#     response = get_licence('CCO', 'url', False)

#     assert response == '&#x2715;'


# def test_get_licence_acceptable():
#     response = get_licence('CCO', 'url', True)

#     assert response == "<a href=\"url\"><img src=\"../images/licenses/cc_pd.png\" width='70' height='27'></a>"


# def test_get_licence_with_name_not_in_dict_and_url():
#     response = get_licence('CC', 'url', True)

#     assert response == "<a href=\"url\">CC</a>"


# def test_get_licence_name_not_in_dict_and_without_url():
#     response = get_licence('CC', None, True)

#     assert response == 'CC'


# def test_get_licence_without_name_and_without_url():
#     response = get_licence(None, None, True)

#     assert response is None


# def test_data_correct_format():
#     data = get_data_by_prefix(RAW_DATA)
#     assert len(data) == 3
#
#     bbc_data = data['360g-cin']
#     assert len(bbc_data) == 3
#     assert bbc_data['publisher'] == {
#         'name': 'BBC Children in Need',
#         'logo': 'http://www.threesixtygiving.org/wp-content/uploads/BBCCiN_CoreLogo.png'
#     }
#     assert bbc_data['licence'] == {
#         'url': 'https://creativecommons.org/licenses/by/4.0/',
#         'name': 'Creative Commons Attribution 4.0'
#     }
#     assert bbc_data['grant'] == [{
#         'url': 'http://downloads.bbc.co.uk/tv/pudsey/360_giving_data_02102016.xlsx',
#         'name': 'BBC Children in Need grants'
#     }]


# def test_data_is_sorted_alphabetically_by_org_name():
#     keys = list(get_data_by_prefix(RAW_DATA).keys())
#
#     assert keys[0] == '360g-cin'
#     assert keys[1] == '360G-blf'
#     assert keys[2] == '360G-CorraFoundation'
#
#
# def test_publisher_with_multiple_entries_is_consolidated_in_a_single_entry():
#     big_lottery_grant = get_data_by_prefix(RAW_DATA)['360G-blf']['grant']
#
#     assert len(big_lottery_grant) is 2
#     assert big_lottery_grant[0]['name'] == 'Big Lottery Fund - grants data 2015 to 2017'
#     assert big_lottery_grant[1]['name'] == 'Big Lottery Fund - grants data 2017-18 year-to-date'


def test_max_award_date_correct_format():
    raw_data = get_raw_data(True)
    data = get_data_sorted_by_prefix(raw_data)
    grants_blf = data["360G-blf"]["grant"]

    assert grants_blf[0].period["latest_date"] == "Mar 2018"
    assert grants_blf[1].period["latest_date"] == "Mar 2017"


def test_publisher_data_is_sorted_by_max_award_date():
    data_by_prefix = get_data_by_prefix(SCVO_DATA)
    sorted_data = sort_data(data_by_prefix)
    grants = sorted_data["360G-SCVO"]["grant"]

    assert len(grants) == 4
    assert grants[0].period["latest_date"] == "May 2019"
    assert grants[1].period["latest_date"] == "Dec 2018"
    assert grants[2].period["latest_date"] == "Nov 2018"
    assert grants[3].period["latest_date"] == "Aug 2018"


def test_registryfile_class():
    """
    Load the data as a registry file without causing an error
    """
    for d in SCVO_DATA:
        _ = RegistryFile(d)


def test_registryfile_file():
    r = RegistryFile(SCVO_DATA[0])
    assert r.file["title"] == "SCVO Community Capacity & Resilience Fund grants"
    assert (
        r.file["url"]
        == "https://scvo.org/running-your-organisation/funding/community-capacity-resilience-fund/projects/data.json"
    )
    assert r.file["accessURL"] == "https://scvo.org/transparency-open-data"
    assert r.file["type"] == "json"
    assert r.file["size"] == "966 kB"
    assert r.file["available"] is True


def test_registryfile_records():
    r = RegistryFile(SCVO_DATA[0])
    assert r.records == "191"

    r.aggregates["count"] = 11234
    assert r.records == "11,234"


def test_registryfile_vaild():
    r = RegistryFile(SCVO_DATA[0])
    r.metadata["valid"] = True
    assert r.valid == "&#x2713;"

    r.metadata["valid"] = False
    assert r.valid == "&#x2715;"


def test_registryfile_schemaorg():
    datacatalog_name = "test_datacatalog"
    r = RegistryFile(SCVO_DATA[0])
    s = r.schemaorg(datacatalog_name)

    assert s == {
        "@context": "https://schema.org/",
        "@type": "Dataset",
        "name": "SCVO Community Capacity & Resilience Fund grants",
        "description": "Data on grants made by Scottish Council for Voluntary Organisations published using the 360Giving Data Standard",
        "url": "https://scvo.org/transparency-open-data",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "creator": {
            "@type": "Organization",
            "url": "http://scvo.org",
            "name": "Scottish Council for Voluntary Organisations",
        },
        "includedInDataCatalog": {"@type": "DataCatalog", "name": datacatalog_name},
        "distribution": [
            {
                "@type": "DataDownload",
                "encodingFormat": "json",
                "contentUrl": "https://scvo.org/running-your-organisation/funding/community-capacity-resilience-fund/projects/data.json",
            },
        ],
        "temporalCoverage": "2015-07-03/2018-11-02",
    }
