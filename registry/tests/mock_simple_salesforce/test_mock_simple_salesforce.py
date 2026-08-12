from django.test import TestCase
import python_soql_parser
from tests.mock_simple_salesforce import soql
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


class QueryParseTests(TestCase):
    def test_flatten_pyparse_results(self):
        parsed_query = python_soql_parser.parse("""
            SELECT Id, Name from Account WHERE field != null ORDER BY Name
            """)
        assert soql.flatten_pyparse(parsed_query.where) == ["field", "!=", "null"]
        assert soql.flatten_pyparse(parsed_query.order_by) == ["Name"]

    def test_parse_field_name(self):
        parsed_field = soql.parse_field_name("Name", "Account")
        assert parsed_field.field_name == "Account.Name"
        assert parsed_field.table_name == "Account"
        assert parsed_field.related == None

        parsed_field = soql.parse_field_name("Account__r.Name", "Dataset__c")
        assert parsed_field.field_name == "Account.Name"
        assert parsed_field.table_name == "Account"
        assert parsed_field.related == "Account__r"

        parsed_field = soql.parse_field_name("License__r.Name", "Dataset__c")
        assert parsed_field.field_name == "License__c.Name"
        assert parsed_field.table_name == "License__c"
        assert parsed_field.related == "License__r"

    def test_soql_to_sql_conversion(self):
        sf_query = (
            "SELECT Id, Name, License__r.Name, Account__r.Name "
            "FROM Dataset__c ORDER BY Account__r.Name"
        )
        conv_query = soql.convert_soql_to_sqlite(sf_query)
        assert conv_query.sql == (
            "SELECT Dataset__c.Id, Dataset__c.Name, License__c.Name, Account.Name, License__c.Id, Account.Id "
            "FROM Dataset__c "
            "INNER JOIN License__c ON License__c.Id = Dataset__c.License__r "
            "INNER JOIN Account ON Account.Id = Dataset__c.Account__r "
            "ORDER BY Account.Name;"
        )

        sf_query = (
            "SELECT Id, Name, prefix__c "
            "from Account "
            "WHERE prefix__c != null "
            "ORDER BY Name"
        )
        conv_query = soql.convert_soql_to_sqlite(sf_query)
        assert conv_query.sql == (
            "SELECT Account.Id, Account.Name, Account.prefix__c "
            "FROM Account "
            "WHERE Account.prefix__c NOT null "
            "ORDER BY Account.Name;"
        )
