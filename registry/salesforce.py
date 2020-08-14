import json
import os

from simple_salesforce import Salesforce


def get_salesforce_access():
    return Salesforce(
        username="360support@opendataservices.coop",
        password=os.environ["SALESFORCE_PASSWORD"],
        security_token=os.environ["SALESFORCE_SECURITY_TOKEN"],
    )


def clean_object(obj):
    new_obj = {}

    obj.pop("attributes", None)
    for key, value in obj.items():
        new_key = key.replace("__c", "").replace("__r", "").replace("_", "")
        new_key = new_key[:1].lower() + new_key[1:] if new_key else ""
        new_obj[new_key] = value
    return new_obj


def get_output_dataset(dataset):
    license = clean_object(dataset["license"])
    publisher = clean_object(dataset["account"])

    return {
        "title": dataset["name"],
        "description": dataset["description"]
        if dataset["description"] is not None
        else "",
        "identifier": dataset["id"],
        "license": license["uRL"],
        "license_name": license["name"],
        "issued": dataset["dateFirstPublished"],
        "modified": dataset["lastModifiedDate"],
        "publisher": {
            "name": publisher["name"],
            "website": publisher["website"] if publisher["website"] else "",
            "logo": publisher["logo"] if publisher["logo"] else "",
            "prefix": publisher["prefix"],
        },
        "distribution": [
            {
                "downloadURL": dataset["downloadURL"],
                "accessURL": dataset["accessURL"],
                "title": dataset["name"],
            }
        ],
    }


def clean_output(api_output):
    datasets = []
    for dataset in api_output["records"]:
        if dataset["Approved__c"]:
            try:
                clean_dataset = clean_object(dataset)
                output_dataset = get_output_dataset(clean_dataset)
                datasets.append(output_dataset)
            # We have bad data
            except Exception:
                pass

    if len(dataset) == 0:
        raise Exception("No data could be cleaned for output")

    return datasets


def get_salesforce_data():
    salesforce = get_salesforce_access()
    sf_query = (
        "SELECT Id, Name, License__r.Name, License__r.URL__c, Access_URL__c, Description__c, Download_URL__c,"
        "Account__r.Id, Account__r.Logo__c, Account__r.Name, Account__r.Website, Account__r.prefix__c,"
        "Date_First_Published__c, LastModifiedDate, Approved__c from Dataset__c ORDER BY Account__r.Name"
    )  # noqa: E126

    output = clean_output(salesforce.query(sf_query))

    return json.dumps(output, indent=2)
