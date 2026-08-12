from django.test import TestCase
import python_soql_parser
from tests.mock_simple_salesforce import soql
from tests.mock_simple_salesforce.core import _make_object_url, MockSimpleSalesforce


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

    def test_add_and_query_records(self):
        mock = MockSimpleSalesforce()

        mock.create_record("Account", {"Name": "B Record"})
        mock.create_record("Account", {"Name": "C Record"})
        mock.create_record("Account", {"Name": "L Record"})
        mock.create_record("Account", {"Name": "A Record"})
        mock.create_record("Account", {"Name": "G Record"})

        result = mock.query_all("SELECT Id, Name FROM Account ORDER BY Name")

        assert result["totalSize"] == 5
        assert result["done"] == True

        assert result["records"][0]["attributes"]["type"] == "Account"
        assert result["records"][0]["Name"] == "A Record"

        assert result["records"][1]["attributes"]["type"] == "Account"
        assert result["records"][1]["Name"] == "B Record"

        assert result["records"][2]["attributes"]["type"] == "Account"
        assert result["records"][2]["Name"] == "C Record"

        assert result["records"][3]["attributes"]["type"] == "Account"
        assert result["records"][3]["Name"] == "G Record"

        assert result["records"][4]["attributes"]["type"] == "Account"
        assert result["records"][4]["Name"] == "L Record"

    def test_related_records(self):
        mock = MockSimpleSalesforce()
        mock.add_custom_account_fields(["prefix"])
        mock.add_custom_table("License", ["URL"], [])
        mock.add_custom_table("Dataset", ["Access_URL"], ["Account", "License"])

        b_org_sfid = mock.create_record(
            "Account", {"Name": "Org B", "prefix__c": "360G-OrgB"}
        )
        c_org_sfid = mock.create_record(
            "Account", {"Name": "Org C", "prefix__c": "360G-OrgC"}
        )
        a_org_sfid = mock.create_record(
            "Account", {"Name": "Org A", "prefix__c": "360G-OrgA"}
        )

        a_license_sfid = mock.create_record(
            "License__c", {"Name": "License A", "URL__c": "a"}
        )
        b_license_sfid = mock.create_record(
            "License__c", {"Name": "License B", "URL__c": "b"}
        )

        d_dataset_sfid = mock.create_record(
            "Dataset__c",
            {
                "Name": "Dataset D",
                "Account__r": a_org_sfid,
                "License__r": a_license_sfid,
                "Access_URL__c": "d",
            },
        )
        c_dataset_sfid = mock.create_record(
            "Dataset__c",
            {
                "Name": "Dataset C",
                "Account__r": c_org_sfid,
                "License__r": a_license_sfid,
                "Access_URL__c": "c",
            },
        )
        b_dataset_sfid = mock.create_record(
            "Dataset__c",
            {
                "Name": "Dataset B",
                "Account__r": b_org_sfid,
                "License__r": b_license_sfid,
                "Access_URL__c": "b",
            },
        )
        a_dataset_sfid = mock.create_record(
            "Dataset__c",
            {
                "Name": "Dataset A",
                "Account__r": a_org_sfid,
                "License__r": a_license_sfid,
                "Access_URL__c": "a",
            },
        )

        result = mock.query_all(
            "SELECT Id, Name, Access_URL__c, Account__r.Name, Account__r.prefix__c, License__r.Name, License__r.URL__c FROM Dataset__c ORDER BY Name"
        )
        assert result["totalSize"] == 4
        assert result["done"] == True

        record = result["records"][0]
        assert record["attributes"]["type"] == "Dataset__c"
        assert record["Id"] == a_dataset_sfid
        assert record["Name"] == "Dataset A"
        assert record["Access_URL__c"] == "a"
        assert record["Account__r"]["attributes"]["type"] == "Account"
        assert record["Account__r"]["attributes"]["url"] == _make_object_url(
            "Account", a_org_sfid
        )
        assert record["Account__r"]["Name"] == "Org A"
        assert record["Account__r"]["prefix__c"] == "360G-OrgA"
        assert record["License__r"]["attributes"]["type"] == "License__c"
        assert record["License__r"]["attributes"]["url"] == _make_object_url(
            "License__c", a_license_sfid
        )
        assert record["License__r"]["Name"] == "License A"
        assert record["License__r"]["URL__c"] == "a"

        record = result["records"][1]
        assert record["attributes"]["type"] == "Dataset__c"
        assert record["Id"] == b_dataset_sfid
        assert record["Name"] == "Dataset B"
        assert record["Access_URL__c"] == "b"
        assert record["Account__r"]["attributes"]["type"] == "Account"
        assert record["Account__r"]["attributes"]["url"] == _make_object_url(
            "Account", b_org_sfid
        )
        assert record["Account__r"]["Name"] == "Org B"
        assert record["Account__r"]["prefix__c"] == "360G-OrgB"
        assert record["License__r"]["attributes"]["type"] == "License__c"
        assert record["License__r"]["attributes"]["url"] == _make_object_url(
            "License__c", b_license_sfid
        )
        assert record["License__r"]["Name"] == "License B"
        assert record["License__r"]["URL__c"] == "b"

        record = result["records"][2]
        assert record["attributes"]["type"] == "Dataset__c"
        assert record["Id"] == c_dataset_sfid
        assert record["Name"] == "Dataset C"
        assert record["Access_URL__c"] == "c"
        assert record["Account__r"]["attributes"]["type"] == "Account"
        assert record["Account__r"]["attributes"]["url"] == _make_object_url(
            "Account", c_org_sfid
        )
        assert record["Account__r"]["Name"] == "Org C"
        assert record["Account__r"]["prefix__c"] == "360G-OrgC"
        assert record["License__r"]["attributes"]["type"] == "License__c"
        assert record["License__r"]["attributes"]["url"] == _make_object_url(
            "License__c", a_license_sfid
        )
        assert record["License__r"]["Name"] == "License A"
        assert record["License__r"]["URL__c"] == "a"

        record = result["records"][3]
        assert record["attributes"]["type"] == "Dataset__c"
        assert record["Id"] == d_dataset_sfid
        assert record["Name"] == "Dataset D"
        assert record["Access_URL__c"] == "d"
        assert record["Account__r"]["attributes"]["type"] == "Account"
        assert record["Account__r"]["attributes"]["url"] == _make_object_url(
            "Account", a_org_sfid
        )
        assert record["Account__r"]["Name"] == "Org A"
        assert record["Account__r"]["prefix__c"] == "360G-OrgA"
        assert record["License__r"]["attributes"]["type"] == "License__c"
        assert record["License__r"]["attributes"]["url"] == _make_object_url(
            "License__c", a_license_sfid
        )
        assert record["License__r"]["Name"] == "License A"
        assert record["License__r"]["URL__c"] == "a"


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
