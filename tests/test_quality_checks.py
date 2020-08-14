from registry.quality_checks import (
    BasicDetailsCheck,
    BeneficiaryGeographyCheck,
    CurrencyCheck,
    GrantProgrammeCheck,
    OrganisationIdentifiersCheck,
    PlannedDatesCheck,
    RecipientGeographyCheck,
)
from registry.registry import RegistryFile


def test_currency_check_gbp_only():
    c = CurrencyCheck(
        RegistryFile({"datagetter_aggregates": {"currencies": {"GBP": 100}}})
    )

    assert c.visible is False
    assert c.valid == "info"
    assert c.title == "Uses non-GBP currencies"
    assert (
        c.description
        == "Contains information about grants made in currencies other than british pounds £."
    )


def test_currency_check_non_gbp():
    c = CurrencyCheck(
        RegistryFile({"datagetter_aggregates": {"currencies": {"EUR": 100}}})
    )
    assert c.visible is True


def test_currency_check_multiple():
    c = CurrencyCheck(
        RegistryFile(
            {"datagetter_aggregates": {"currencies": {"EUR": 100, "GBP": 1200,}}}
        )
    )
    assert c.visible is True


def test_currency_check_multiple_non_gbp():
    c = CurrencyCheck(
        RegistryFile(
            {"datagetter_aggregates": {"currencies": {"EUR": 100, "USD": 1200,}}}
        )
    )
    assert c.visible is True


def test_grant_programme_check_true():
    c = GrantProgrammeCheck(
        RegistryFile({"datagetter_coverage": {"/grants/grantProgramme": {}}})
    )
    assert c.visible is True
    assert c.valid is True
    assert c.title == "Includes grant programme"
    assert (
        c.description
        == "This file includes details of the grant programmes that each grant is part of."
    )


def test_grant_programme_check_false():
    c = GrantProgrammeCheck(RegistryFile({"datagetter_coverage": {}}))
    assert c.visible is True
    assert c.valid is False
    assert c.title == "Missing grant programme"
    assert (
        c.description
        == "This file does not include details of the grant programmes that each grant is part of."
    )


def test_basic_details_check_true():
    c = BasicDetailsCheck(
        RegistryFile({"datagetter_coverage": {"/grants/grantProgramme": {}}})
    )
    assert c.visible is True
    assert c.valid is True
    assert c.title == "Includes basic details"
    assert (
        c.description
        == "This file contains the basic fields required to meet the 360Giving Data Standard."
    )


def test_true_false_checks():
    checks = [
        (GrantProgrammeCheck, "/grants/grantProgramme"),
        (BeneficiaryGeographyCheck, "/grants/beneficiaryLocation"),
        (RecipientGeographyCheck, "/grants/recipientOrganization/postalCode"),
        (RecipientGeographyCheck, "/grants/recipientOrganization/location"),
        (PlannedDatesCheck, "/grants/plannedDates"),
        (PlannedDatesCheck, "/grants/actualDates"),
    ]
    for check in checks:
        c = check[0](RegistryFile({"datagetter_coverage": {check[1]: {}}}))
        assert c.visible is True
        assert c.valid is True

        c = check[0](RegistryFile({"datagetter_coverage": {}}))
        assert c.visible is True
        assert c.valid is False


def test_organisation_identifiers_check_all_internal():
    c = OrganisationIdentifiersCheck(
        RegistryFile(
            {
                "datagetter_aggregates": {
                    "recipient_org_identifier_prefixes": {"360G": 10}
                }
            }
        )
    )
    assert c.valid is False
    assert "0%" in c.description


def test_organisation_identifiers_check_all_external():
    c = OrganisationIdentifiersCheck(
        RegistryFile(
            {
                "datagetter_aggregates": {
                    "recipient_org_identifier_prefixes": {"GB-CHC": 10}
                }
            }
        )
    )
    assert c.valid is True
    assert "100%" in c.description


def test_organisation_identifiers_check_all_invalid():
    c = OrganisationIdentifiersCheck(
        RegistryFile(
            {
                "datagetter_aggregates": {
                    "recipient_org_identifier_prefixes": {},
                    "recipient_org_identifiers_unrecognised_prefixes": {"missing": 10},
                }
            }
        )
    )
    assert c.valid is False
    assert "0%" in c.description


def test_organisation_identifiers_check_all():
    c = OrganisationIdentifiersCheck(
        RegistryFile(
            {
                "datagetter_aggregates": {
                    "recipient_org_identifier_prefixes": {"360G": 10, "GB-CHC": 10},
                    "recipient_org_identifiers_unrecognised_prefixes": {"missing": 20},
                }
            }
        )
    )
    assert c.valid is False
    assert "25%" in c.description


def test_organisation_identifiers_check_all_valid():
    c = OrganisationIdentifiersCheck(
        RegistryFile(
            {
                "datagetter_aggregates": {
                    "recipient_org_identifier_prefixes": {"360G": 10, "GB-CHC": 80},
                    "recipient_org_identifiers_unrecognised_prefixes": {"missing": 10},
                }
            }
        )
    )
    assert c.valid is True
    assert "80%" in c.description


def test_organisation_identifiers_check_all_fifty():
    c = OrganisationIdentifiersCheck(
        RegistryFile(
            {
                "datagetter_aggregates": {
                    "recipient_org_identifier_prefixes": {"360G": 20, "GB-CHC": 50},
                    "recipient_org_identifiers_unrecognised_prefixes": {"missing": 30},
                }
            }
        )
    )
    assert c.valid is True
    assert "50%" in c.description
