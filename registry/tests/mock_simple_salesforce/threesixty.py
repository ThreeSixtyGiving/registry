from datetime import datetime
from random import Random
import string

from tests.mock_simple_salesforce.core import MockSimpleSalesforce


def random_invalid_base_url(rnd: Random) -> str:
    """Generate a random base url that is an invalid URL

    Parameters
    ----------
    rnd : Random
        Random number generator.

    Returns
    -------
    str
    """
    return (
        "https://"
        + "".join(rnd.choices(string.ascii_letters + string.digits, k=32))
        + ".invalid/"
    )


def random_orgid(rnd: Random) -> str:
    """Generate a random org id

    Parameters
    ----------
    rnd : Random
        Random number generator.

    Returns
    -------
    str
    """
    return f"GB-{rnd.choice(string.ascii_uppercase)*3}-{rnd.uniform(0,999999)}"


def random_datetime(
    rnd: Random,
    start_date: datetime = datetime(2017, 1, 1, 12, 0, 0),
    end_date: datetime = datetime(2026, 1, 1, 12, 0, 0),
) -> datetime:
    """Generate a random datetime between two dates

    Parameters
    ----------
    rnd : Random
        Random number generator.
    start_date : datetime, optional
        Minimum datetime that will be returned, by default datetime(2017, 1, 1, 12, 0, 0)
    end_date : datetime, optional
        Maximum datetime that will be returned, by default datetime(2026, 1, 1, 12, 0, 0)

    Returns
    -------
    datetime
    """
    timestamp_range = end_date.timestamp() - start_date.timestamp()

    return datetime.fromtimestamp(
        start_date.timestamp() + rnd.uniform(0.0, timestamp_range)
    )


def random_bool(rnd: Random) -> bool:
    """Return random boolean.

    Parameters
    ----------
    rnd : Random
        Random number generator.

    Returns
    -------
    bool
    """
    return rnd.choice([True, False])


class MockSimpleSalesforce360Giving(MockSimpleSalesforce):
    LICENSES = [
        {
            "Name": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "URL__c": "https://creativecommons.org/licenses/by/4.0/",
        },
        {
            "Name": "Creative Commons Attribution 4.0 ShareAlike 4.0 International (CC BY-SA 4.0)",
            "URL__c": "https://creativecommons.org/licenses/by-sa/4.0/",
        },
    ]

    def __init__(self, **kwargs) -> None:
        """Initialise a Mock SimpleSalesforce object setup to represent the 360 Registry

        The first dataset is always not approved, and the first account has no prefix so
        that we can test specific functionality required by the registry.
        """
        super().__init__(**kwargs)

        # Add custom Account fields
        self.add_custom_account_fields(
            [
                "Logo",
                "prefix",
                "Org_Identifier",
                "Authorised_Domain",
                "Self_registration_enabled",
                "Last_published_date",
            ]
        )

        # Add Dataset and License tables.
        self.add_custom_table("License", ["URL"], [])
        self.add_custom_table(
            "Dataset",
            [
                "Access_URL",
                "Description",
                "Download_URL",
                "Date_First_Published",
                "Approved",
            ],
            ["License", "Account"],
        )

    def init_mock_registry(
        self,
        num_accounts: int,
        num_datasets: int,
        num_accounts_no_prefix: int = 1,
        num_datasets_not_approved: int = 1,
        seed: int = 98562891,
    ) -> None:
        """Initialise the mock registry with licenses, organisations and datasets.

        Parameters
        ----------
        num_accounts : int
            Number of organisations to create.
        num_datasets : int
            Number of datasets to create
        num_accounts_no_prefix : int, optional
            Number of organisations to create with a NULL prefix, by default 1
        num_datasets_not_approved : int, optional
            Number of datasets to create that are not approved, by default 1
        seed : int, optional
            Seed for the random number generator, by default 98562891
        """

        self.rnd.seed(int(seed))

        self._generate_licenses()
        self._generate_accounts(num_accounts, num_accounts_no_prefix)
        self._generate_datasets(num_datasets, num_datasets_not_approved)

    def _generate_licenses(self) -> None:
        """Add licenses to the mock."""
        for license in self.LICENSES:
            self.create_record(
                "License__c", {"Name": license["Name"], "URL__c": license["URL__c"]}
            )

    def _generate_accounts(self, num: int, num_with_no_prefix: int) -> None:
        """Add fake organisations to the mock.

        Parameters
        ----------
        num : int
            Number of organisations to make.
        num_with_no_prefix : int
            Number of organisations to make with no prefix.
        """
        for index in range(num):
            logo = (
                "https://registry.threesixtygiving.org/static/images/360-logos/360giving-registry.svg"
                if random_bool(self.rnd)
                else None
            )
            base_url = random_invalid_base_url(self.rnd)
            self.create_record(
                "Account",
                {
                    "Name": f"Charitable Trust {index+1}",
                    "Logo__c": logo,
                    "Website": base_url + "index.html",
                    "prefix__c": (
                        f"360G-CT{index+1}"
                        if index > (num_with_no_prefix - 1)
                        else None
                    ),
                    "Org_Identifier__c": random_orgid(self.rnd),
                    "Authorised_Domain__c": base_url,
                    "Self_registration_enabled__c": False,
                    "Last_published_date__c": datetime(1900, 1, 1, 0, 0, 0),
                },
            )

    def _generate_datasets(self, num: int, num_not_approved: int) -> None:
        """Add fake datasets to the mock.

        Parameters
        ----------
        num : int
            Number of datasets to create.
        num_not_approved : int
            Number of datasets to create that are not approved.
        """
        cur = self.con.cursor()
        for index in range(num):
            account_sfid = self.rnd.choice(
                cur.execute(
                    "SELECT Id FROM Account WHERE Account.prefix__c NOT null;"
                ).fetchall()
            )[0]
            license_sfid = self.rnd.choice(
                cur.execute("SELECT Id FROM License__c;").fetchall()
            )[0]
            base_url = cur.execute(
                f"SELECT Authorised_Domain__c FROM Account WHERE Id='{account_sfid}';"
            ).fetchone()[0]
            first_published = random_datetime(self.rnd)
            last_modified = random_datetime(self.rnd, start_date=first_published)

            self.create_record(
                "Dataset__c",
                {
                    "Name": f"Grant {index+1}",
                    "Access_URL__c": base_url,
                    "Description__c": (
                        f"This is description {index+1}"
                        if random_bool(self.rnd)
                        else None
                    ),
                    "Download_URL__c": base_url
                    + "data."
                    + self.rnd.choice(["xlsx", "json"]),
                    "Date_First_Published__c": first_published,
                    "LastModifiedDate": last_modified,
                    "Approved__c": True if index > (num_not_approved - 1) else False,
                    "License__r": license_sfid,
                    "Account__r": account_sfid,
                },
            )

        res = cur.execute("SELECT Id from ACCOUNT;")
        for account_sfid in res.fetchall():
            datasets = cur.execute(
                f"SELECT Date_First_Published__c FROM Dataset__c WHERE Account__r='{account_sfid[0]}' ORDER BY Date_First_Published__c;"
            )
            result = datasets.fetchall()
            if len(result) > 0:
                latest_dataset_publish_date = result[-1][0]
                cur.execute(
                    f"UPDATE Account SET Last_published_date__c = '{latest_dataset_publish_date}' WHERE Id='{account_sfid[0]}';"
                )
