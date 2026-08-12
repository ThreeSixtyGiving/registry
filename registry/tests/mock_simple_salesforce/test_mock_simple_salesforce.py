from django.test import TestCase
import python_soql_parser
from tests.mock_simple_salesforce.core import MockSimpleSalesforce


class DatabaseTests(TestCase):
    def test_account_custom_fields(self):
        mock = MockSimpleSalesforce()
        cur = mock.con.cursor()

        res = cur.execute("pragma table_info('Account');")
        field_names = [row[1] for row in res.fetchall()]
        assert len(field_names) == 4
        assert "Id" in field_names
        assert "Name" in field_names
        assert "Website" in field_names
        assert "LastModifiedDate" in field_names

        mock.add_custom_account_fields(["Logo", "prefix"])

        res = cur.execute("pragma table_info('Account');")
        field_names = [row[1] for row in res.fetchall()]
        assert len(field_names) == 6
        assert "Id" in field_names
        assert "Name" in field_names
        assert "Website" in field_names
        assert "LastModifiedDate" in field_names
        assert "Logo__c" in field_names
        assert "prefix__c" in field_names

    def test_custom_table(self):
        mock = MockSimpleSalesforce()
        cur = mock.con.cursor()

        mock.add_custom_table("TestTable", ["TestField"], ["Account"])

        res = cur.execute("pragma table_info('TestTable__c');")
        field_names = [row[1] for row in res.fetchall()]
        assert len(field_names) == 5
        assert "Id" in field_names
        assert "Name" in field_names
        assert "LastModifiedDate" in field_names
        assert "TestField__c" in field_names
        assert "Account__r" in field_names

    def test_add_records(self):
        mock = MockSimpleSalesforce()

        mock.create_record("Account", {"Name": "B Record"})
        mock.create_record("Account", {"Name": "C Record"})
        mock.create_record("Account", {"Name": "L Record"})
        mock.create_record("Account", {"Name": "A Record"})
        mock.create_record("Account", {"Name": "G Record"})

        cur = mock.con.cursor()
        res = cur.execute("SELECT Account.Name FROM Account ORDER BY Name;")
        result = res.fetchall()
        assert result[0][0] == "A Record"
        assert result[1][0] == "B Record"
        assert result[2][0] == "C Record"
        assert result[3][0] == "G Record"
        assert result[4][0] == "L Record"
