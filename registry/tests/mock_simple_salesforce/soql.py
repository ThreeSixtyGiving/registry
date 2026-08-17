from collections import namedtuple
from typing import Any

from pyparsing import ParseResults
import python_soql_parser


def flatten_pyparse(data: ParseResults) -> list[Any]:
    """Flatten nested lists returned from python_soql_parser

    python_soql_parser uses pyparsing to parse SOQL queries.  Some of
    the returned objects are heavily nested lists.  This helper
    function flattens those nested lists.  For example, [[[1, 2, 3]]]
    would be flattened to [1, 2, 3].

    Parameters
    ----------
    data : ParseResults
        Parsing results object to be flattened

    Returns
    -------
    list[Any]
    """

    def _flatten(_data: Any, output: list):
        if isinstance(_data, ParseResults):
            for item in _data:
                if isinstance(item, ParseResults):
                    _flatten(item, output)
                else:
                    output.append(item)

        return output

    return _flatten(data, [])


ParsedFieldName = namedtuple("ParsedFieldName", ["field_name", "table_name", "related"])


def parse_field_name(field_name_from_query: str, sobject: str) -> ParsedFieldName:
    """Parse a field name in a SOQL query.

    This will parse a variety of field names, e.g., Account.Id, Name, Account__r
    to give the table that the field is from, the field name itself, and if it's a
    related field then it will give us the table that this field relates to.

    Parameters
    ----------
    field_name_from_query : str
        The field name as contained in a query.
    sobject : str
        The object of that query, e.g., SELECT Id FROM Dataset__c, the sobject would be Dataset__c.

    Returns
    -------
    ParsedFieldName
    """

    # Is this field in the table that the SELECT query is FROM?
    is_sobject_field = len(field_name_from_query.split(".")) == 1

    if is_sobject_field:
        # We need to append the table name, e.g., "SELECT Id FROM Account;"
        # will become "SELECT Account.Id FROM Account";
        field_name = field_name_from_query
        table_name = sobject
        related = None

    else:
        # We need to modify this as we have a fieldname like "Account__r.Name".  This needs
        # to be parsed into the table_name "Account", the related name "Account__r", and
        # a full field name including table "Account.Name".  If this were a custom table
        # for example, "Dataset__c.URL__c" then we would get table "Dataset__c", related name
        # "Dataset__r", and field name "Dataset__c.URL__c".
        related, field_name = field_name_from_query.split(".")

        table_name = related[:-3]
        if related != "Account__r":
            table_name = related[:-3] + "__c"

    return ParsedFieldName(
        table_name=table_name, field_name=table_name + "." + field_name, related=related
    )


ConvertedQuery = namedtuple("ConvertedQuery", ["sql", "sobject", "joins", "fields"])


def convert_soql_to_sqlite(soql_query: str) -> ConvertedQuery:
    """Parse Salesforce Object Query Language query and convert into an SQLite query

    Only select queries are supported.

    Parameters
    ----------
    soql_query : str
        Salesforce Object Query Language query string.

    Returns
    -------
    ConvertedQuery

    Raises
    ------
    ValueError
        If a non-SELECT query is passed.
    """

    # Parse the query and check we can convert it.
    parsed_query = python_soql_parser.parse(soql_query)
    if parsed_query[0] != "select":
        raise ValueError(
            "Only SELECT queries can be parsed by the SimpleSalesforce mock"
        )

    # We need to do three things: find all the tables we need to JOIN, sort out
    # join ids, correct the field names by adding/changing table prefixes.
    join_tables = []
    join_table_names = []
    fields = []

    for orig_field in parsed_query.fields:

        parsed_field = parse_field_name(orig_field, parsed_query.sobject)
        if parsed_field.table_name != parsed_query.sobject:
            if parsed_field.table_name not in join_table_names:
                join_tables.append(parsed_field)
                join_table_names.append(parsed_field.table_name)

        fields.append(parsed_field.field_name)

    for table in join_tables:
        if table.table_name + ".Id" not in fields:
            fields.append(table.table_name + ".Id")

    # Construct SQL for SQLite.
    sql = "SELECT " + ", ".join(fields)
    sql += " FROM " + parsed_query.sobject
    for join_table in join_tables:
        sql += f" INNER JOIN {join_table.table_name} ON {join_table.table_name}.Id = {parsed_query.sobject}.{join_table.related}"

    if parsed_query.where:
        where = flatten_pyparse(parsed_query.where)
        where[0] = parse_field_name(where[0], parsed_query.sobject).field_name
        if where[1] == "!=":
            where[1] = "NOT"
        sql += " WHERE " + " ".join(where)

    if parsed_query.order_by:
        order_by = parse_field_name(
            flatten_pyparse(parsed_query.order_by)[0], parsed_query.sobject
        )
        sql += " ORDER BY " + order_by.field_name

    sql += ";"

    return ConvertedQuery(
        sql=sql,
        sobject=parsed_query.sobject,
        joins=join_tables,
        fields={field: index for index, field in enumerate(fields)},
    )
