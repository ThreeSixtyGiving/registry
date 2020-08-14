import os
from collections import OrderedDict
from datetime import datetime

import humanize
import requests
from flask import url_for

from registry.quality_checks import (
    BasicDetailsCheck,
    BeneficiaryGeographyCheck,
    CurrencyCheck,
    GrantProgrammeCheck,
    OrganisationIdentifiersCheck,
    PlannedDatesCheck,
    RecipientGeographyCheck,
)
from tests.samples.registry_raw_data import RAW_DATA


def get_currency_symbol(currency, data):
    """
    :param currency: currency code (eg. GBP).
    :param data:
    {
        "count": 6263,
        "currency_symbol": "&pound;",
        "max_amount": 3466000,
        "min_amount": 271,
        "total_amount": 257947904
    }
    """
    if not data.get("currency_symbol"):
        return currency
    return data["currency_symbol"]


def format_value(value, to_round=False, shorten=False):
    """
    Format value from 492793844.650000003 to 492,793,844.65
    If to_round=True, the value gets rounded.
    """
    if value and isinstance(value, (float, int)):
        if shorten:
            if value > 1000000000:
                return "{:,.1f}bn".format(value / 1000000000)
            if value > 1000000:
                return "{:,.1f}m".format(value / 1000000)
        if type(value) == float:
            if to_round:
                value = round(value)
            else:
                value = float(format(value, ".2f"))
        return "{:,}".format(value)
    return value


def format_date(date, date_format="%b '%y"):
    """
    :param date: string (yyyy-mm-dd)
    :return: string (eg. Jun '18)
    """
    try:
        return datetime.strptime(date, "%Y-%m-%d").strftime(date_format)
    except ValueError:
        return date


def get_check_cross_symbol(boolean_data):
    """
    :param boolean_data: Boolean.
    :return: 'tick' if true, 'cross' if False else ''.
    """
    if boolean_data is True:
        return "&#x2713;"
    if boolean_data is False:
        return "&#x2715;"
    return ""


def get_file_type(file_type):
    file_types = {
        "csv": "CSV",
        "json": "json",
        "xlsx": "Excel",
    }
    return file_types.get(file_type, "file")


def get_prefix_data(data):
    return {
        "publisher": {
            "name": data["publisher"]["name"],
            "logo": data["publisher"]["logo"],
            "website": data["publisher"]["website"],
        },
        "grant": [],
    }


def get_data_by_prefix(raw_data):
    """
    Given a json value where publishers can have more than one entry,
    this function creates a new dictionary keyed by publisher prefix.
    Sample output:
    {
        'prefix': {
            'publisher': {
                'name': string,
                'logo': url of the logo,
            },
            'grant': [{
                'file': {
                    'title': string,
                    'url': string,
                    'type': string (eg. 'csv'),
                    'available': boolean,
                },
                'licence': html code string with licence information,
                'total_value': string with a float or integer,
                'records': string with an integer,
                'period': {
                    'first_date': string with a date,
                    'latest_date': string with a date
                },
                'issued_date': string with a date,
                'valid': tick or cross html symbols,
            }]
        }
    }
    """
    data_by_prefix = {}

    for data in raw_data:
        prefix = data["publisher"]["prefix"]

        if prefix not in data_by_prefix:
            data_by_prefix[prefix] = get_prefix_data(data)

        data_by_prefix[prefix]["grant"].append(RegistryFile(data))

    return data_by_prefix


def sort_data(data_by_prefix):
    """
    Sort grants first by publisher name and, and then by date of the latest date.
    """
    for prefix in data_by_prefix:
        try:
            sort_by_grant_latest_date = sorted(
                data_by_prefix[prefix]["grant"],
                key=lambda x: x.period["max_award_date"],
                reverse=True,
            )
            data_by_prefix[prefix]["grant"] = sort_by_grant_latest_date
        except TypeError:
            pass

    def get_publisher_name(datarow):
        name = datarow[1]["publisher"]["name"].casefold()
        if name.lower().startswith("the "):
            return name[4:]
        return name

    sort_by_publisher_name = sorted(data_by_prefix.items(), key=get_publisher_name)

    return OrderedDict(sort_by_publisher_name)


def get_raw_data(test=False):
    if test or "PYTEST_CURRENT_TEST" in os.environ:
        return RAW_DATA

    return requests.get(
        "http://store.data.threesixtygiving.org/reports/daily_coverage.json"
    ).json()


def get_data_sorted_by_prefix(raw_data):
    data_by_prefix = get_data_by_prefix(raw_data) if raw_data else None
    sorted_data = sort_data(data_by_prefix)

    return sorted_data


def get_schema_org_list(raw_data):
    datacatalog = {
        "@context": "https://schema.org/",
        "@type": "DataCatalog",
        "name": "360Giving Data Registry",
        "url": url_for("data_registry", _external=True),
        "description": "A registry of data about grants made, published using the 360Giving Data Standard",
        "maintainer": {
            "@type": "Organization",
            "url": "https://www.threesixtygiving.org/",
            "name": "360Giving",
        },
    }
    schemaorg = [datacatalog] + [
        {
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "name": d.get("title", ""),
            "description": "Data on grants made by {} published using the 360Giving Data Standard".format(
                d.get("publisher", {}).get("name", "")
            ),
            "url": d.get("distribution", [{}])[0].get("accessURL"),
            "license": d.get("license", ""),
            "creator": {
                "@type": "Organization",
                "url": d.get("publisher", {}).get("website", ""),
                "name": d.get("publisher", {}).get("name", ""),
            },
            "includedInDataCatalog": {
                "@type": "DataCatalog",
                "name": datacatalog["name"],
            },
            "distribution": [
                {
                    "@type": "DataDownload",
                    "encodingFormat": d.get("datagetter_metadata", {}).get("file_type"),
                    "contentUrl": d.get("distribution", [{}])[0].get("downloadURL"),
                },
            ],
            "temporalCoverage": "{}/{}".format(
                d.get("datagetter_aggregates", {}).get("min_award_date"),
                d.get("datagetter_aggregates", {}).get("max_award_date"),
            ),
        }
        for d in raw_data
    ]
    return schemaorg


class RegistryFile:

    checks = [
        CurrencyCheck,
        BasicDetailsCheck,
        GrantProgrammeCheck,
        BeneficiaryGeographyCheck,
        RecipientGeographyCheck,
        PlannedDatesCheck,
        OrganisationIdentifiersCheck,
    ]

    def __init__(self, data):
        self.aggregates = data.get("datagetter_aggregates", {})
        self.metadata = data.get("datagetter_metadata", {})
        self.coverage = data.get("datagetter_coverage", {})
        self.description = data.get("description")
        self.distribution = data.get("distribution", [])
        self.identifier = data.get("identifier")
        if data.get("issued"):
            self.issued = datetime.strptime(data.get("issued"), "%Y-%m-%d")
        else:
            self.issued = None
        self.licence = {
            "url": data.get("license"),
            "name": data.get("license_name"),
            "acceptable": self.metadata.get("acceptable_license"),
        }
        if data.get("modified"):
            self.modified = datetime.strptime(
                data.get("modified"), "%Y-%m-%dT%H:%M:%S.%f%z"
            )
        else:
            self.modified = None
        self.publisher = data.get("publisher", {})
        self.title = data.get("title")

    @property
    def file(self):
        return {
            "title": self.distribution[0]["title"],
            "url": self.distribution[0]["downloadURL"],
            "accessURL": self.distribution[0]["accessURL"],
            "type": get_file_type(self.metadata.get("file_type")),
            "size": humanize.naturalsize(self.metadata.get("file_size"), format="%.0f")
            if self.metadata.get("file_type")
            else "-",
            "available": self.metadata.get("downloads"),
        }

    @property
    def total_value(self):
        """
        :param data_by_currency:
        {
            "GBP":
                {
                    "count": 6263,
                    "currency_symbol": "&pound;",
                    "max_amount": 3466000,
                    "min_amount": 271,
                    "total_amount": 257947904
                },
            "CHF":
                {...}
        }

        :return: currency + total value (eg. '&pound; 257,947,904').
        """
        total_value = []

        if self.aggregates.get("currencies"):
            for currency, data in self.aggregates.get("currencies").items():
                total_amount = data.get("total_amount")

                if total_amount and total_amount is not None:
                    total_value.append(
                        "{} {}".format(
                            get_currency_symbol(currency, data),
                            format_value(
                                value=total_amount, to_round=True, shorten=True
                            ),
                        )
                    )
        return total_value

    @property
    def records(self):
        if self.aggregates.get("count"):
            return format_value(self.aggregates.get("count"))
        return None

    @property
    def period(self):
        return {
            "max_award_date": self.aggregates.get("max_award_date"),
            "first_date": format_date(self.aggregates.get("min_award_date"), "%b %Y")
            if self.aggregates
            else "",
            "latest_date": format_date(self.aggregates.get("max_award_date"), "%b %Y")
            if self.aggregates
            else "",
        }

    @property
    def valid(self):
        return get_check_cross_symbol(self.metadata.get("valid"))

    def quality_checks(self):
        for Check in self.checks:
            yield Check(self)

    def schemaorg(self, datacatalog_name):
        return {
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "name": self.title,
            "description": "Data on grants made by {} published using the 360Giving Data Standard".format(
                self.publisher.get("name", "")
            ),
            "url": self.distribution[0].get("accessURL"),
            "license": self.licence.get("url", ""),
            "creator": {
                "@type": "Organization",
                "url": self.publisher.get("website", ""),
                "name": self.publisher.get("name", ""),
            },
            "includedInDataCatalog": {"@type": "DataCatalog", "name": datacatalog_name},
            "distribution": [
                {
                    "@type": "DataDownload",
                    "encodingFormat": self.metadata.get("file_type"),
                    "contentUrl": self.distribution[0].get("downloadURL"),
                },
            ],
            "temporalCoverage": "{}/{}".format(
                self.aggregates.get("min_award_date"),
                self.aggregates.get("max_award_date"),
            ),
        }
