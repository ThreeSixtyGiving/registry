from collections import OrderedDict
from datetime import datetime
import random
import sqlite3
import string
from typing import Any


sqlite3.register_adapter(datetime, lambda x: int(x.timestamp()))


class MockSimpleSalesforce:
    """Mock for SimpleSalesforce that returns data from an in-memory database"""

    def __init__(
        self, consumer_key: str = None, consumer_secret: str = None, domain: str = None
    ):
        """Initialise the mock.

        Parameters
        ----------
        consumer_key : str, optional
            Client id for accessing Salesforce, by default None.
        consumer_secret : str, optional
            Client secret for accessing Salesforce, by default None.
        domain : str, optional
            The Salesforce domain; this can be specifically formatted to initialise the mock.
        """

        # Setup in-memory DB.
        self.con = sqlite3.connect(":memory:")
        cur = self.con.cursor()
        cur.execute("CREATE TABLE Account(Id,Name,Website,LastModifiedDate);")
        self.con.commit()

        # Setup random number generator to create SF ids.
        self.rnd = random.Random()

    def add_custom_account_fields(self, field_names: list[str]) -> None:
        """Add custom fields to the Account table.  These will have __c appended to them.

        Parameters
        ----------
        field_names : list[str]
            List of field names to add.
        """
        cur = self.con.cursor()
        for field in field_names:
            cur.execute(f"ALTER TABLE Account ADD {field}__c;")
        self.con.commit()

    def add_custom_table(
        self, sobject_name: str, custom_field_names: list[str], related: list[str]
    ):
        """Add a custom table to the mock.

        Parameters
        ----------
        sobject_name : str
            Table name, will have __c appended to it.
        custom_field_names : list[str]
            List of custom field names, each one will have __c appended to it.
        related : list[str]
            List of related objects, e.g., Account, or a custom table (without the __c).
        """
        cur = self.con.cursor()
        sql = f"CREATE TABLE {sobject_name}__c("
        sql += ", ".join(
            ["Id", "Name", "LastModifiedDate"]
            + [field_name + "__c" for field_name in custom_field_names]
            + [rel + "__r" for rel in related]
        )
        sql += ");"
        cur = self.con.cursor()
        cur.execute(sql)
        self.con.commit()

    def create_record(self, sobject: str, data: dict[str, Any]) -> str:
        """Create a record in a given table (Salesforce object)

        Parameters
        ----------
        sobject : str
            The table in which to create the record, custom tables must have the __c appended.
        data : dict[str, Any]
            Dictionary of data (custom fields must have the __c appended).

        Returns
        -------
        str
            Salesforce ID for the created record.

        Raises
        ------
        Exception
            If the caller provides an Id, rather than letting this method create a random id.
        """

        if "Id" in data:
            raise Exception

        field_names = ["Id"] + list(data.keys())

        sql = (
            f"INSERT INTO {sobject}("
            + ", ".join(field_names)
            + ") VALUES ("
            + ", ".join(["?"] * len(field_names))
            + ");"
        )

        sfid = self.random_sfid(account=True if sobject == "Account" else False)
        values = [sfid] + [data[field_name] for field_name in list(data.keys())]

        cur = self.con.cursor()
        cur.execute(sql, values)
        self.con.commit()

        return sfid

    def random_sfid(self, account=False) -> str:
        """Generate a random unique ID in the SF format

        Parameters
        ----------
        account : bool, optional
            If True, generate Id in the format used for Account records, default False.

        Returns
        -------
        str
        """

        prefix = "a"
        block_a_alphabet = string.ascii_uppercase
        block_a_length = 1
        num_zeros = 5
        block_b_alphabet = string.ascii_letters + string.digits
        block_b_length = 8

        if account:
            prefix = ""
            block_a_alphabet = string.ascii_uppercase + string.digits
            block_a_length = 2

        sfid = (
            f"{prefix}00{self.rnd.choice(string.digits)}"
            + "".join(self.rnd.choices(block_a_alphabet, k=block_a_length))
            + "0" * num_zeros
            + "".join(self.rnd.choices(block_b_alphabet, k=block_b_length))
        )

        return sfid
