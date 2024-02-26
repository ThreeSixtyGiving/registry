import os

from simple_salesforce import Salesforce


def get_salesforce_access():
    return Salesforce(
        username=os.environ["SALESFORCE_USERNAME"],
        password=os.environ["SALESFORCE_PASSWORD"],
        security_token=os.environ["SALESFORCE_SECURITY_TOKEN"],
        domain=os.environ.get("SALESFORCE_DOMAIN"),
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
        "description": (
            dataset["description"] if dataset["description"] is not None else ""
        ),
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
            "last_published": publisher["lastpublisheddate"],
            "org_id": publisher.get("orgIdentifier", ""),
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
            except Exception as e:
                print(e)
                pass

    if len(dataset) == 0:
        raise Exception("No data could be cleaned for output")

    return datasets


def get_salesforce_data():
    salesforce = get_salesforce_access()
    sf_query = (
        "SELECT Id, Name, License__r.Name, License__r.URL__c, Access_URL__c, Description__c, Download_URL__c,"
        "Account__r.Id, Account__r.Logo__c, Account__r.Name, Account__r.Website, Account__r.prefix__c, "
        "Date_First_Published__c, LastModifiedDate, Approved__c, Account__r.Last_published_date__c, Account__r.Org_Identifier__c from Dataset__c ORDER BY Account__r.Name"
    )  # noqa: E126

    return clean_output(salesforce.query_all(sf_query))


def get_salesforce_publishers():
    salesforce = get_salesforce_access()
    sf_query = (
        "SELECT Id, Logo__c, Name, Website, prefix__c, "
        "Org_Identifier__c, Authorised_Domain__c, Self_registration_enabled__c from Account WHERE prefix__c != null ORDER BY Name "
    )  # noqa: E126

    sf_data = salesforce.query_all(sf_query)
    publishers = {}

    for publisher in sf_data["records"]:
        publisher = clean_object(clean_object(publisher))
        publishers[publisher["prefix"]] = {
            "id": publisher["id"],
            "name": publisher["name"],
            "website": publisher.get("website", ""),
            "logo": publisher.get("logo", ""),
            "prefix": publisher["prefix"],
            "org_id": publisher.get("orgIdentifier", ""),
            "self_publish": {
                "enabled": publisher.get("selfregistrationenabled", False),
                "authorised_domains": (
                    [publisher["authorisedDomain"]]
                    if publisher.get("authorisedDomain")
                    else []
                ),
            },
        }

    return publishers
