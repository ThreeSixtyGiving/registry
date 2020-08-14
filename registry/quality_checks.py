class QualityCheck:

    def __init__(self, file_):
        self.file = file_

    @property
    def title(self):
        """
        The title of the item (might change depending on whether it's valid or not)
        """
        return ""

    @property
    def description(self):
        """
        The description of the result of the check (might change depending on whether it's valid or not)
        """
        return ""

    @property
    def visible(self):
        """
        Some check results should only be shown if they are valid
        """
        return True

    @property
    def valid(self):
        """
        Whether the file passes this check

        True or false, or can return "info" if it's an information check
        """
        return True


class CurrencyCheck(QualityCheck):
    title = "Uses non-GBP currencies"
    description = "Contains information about grants made in currencies other than british pounds £."

    @property
    def visible(self):
        return 'GBP' not in self.file.aggregates['currencies'] or len(self.file.aggregates['currencies']) > 1

    @property
    def valid(self):
        return 'info'


class BasicDetailsCheck(QualityCheck):
    title = "Includes basic details"
    description = "This file contains the basic fields required to meet the 360Giving Data Standard."


class GrantProgrammeCheck(QualityCheck):

    @property
    def title(self):
        return "Includes grant programme" if self.valid else "Missing grant programme"

    @property
    def description(self):
        if self.valid:
            return "This file includes details of the grant programmes that each grant is part of."
        return "This file does not include details of the grant programmes that each grant is part of."

    @property
    def valid(self):
        return '/grants/grantProgramme' in self.file.coverage


class BeneficiaryGeographyCheck(QualityCheck):

    @property
    def title(self):
        return "Includes beneficiary geography" if self.valid else "Missing beneficiary geography"

    @property
    def description(self):
        if self.valid:
            return "This file contains data in the beneficiary geography fields, allowing you to pinpoint where the grant activity took place."
        return "This file does not contain data in the beneficiary geography fields, allowing you to pinpoint where the grant activity took place."

    @property
    def valid(self):
        return '/grants/beneficiaryLocation' in self.file.coverage


class RecipientGeographyCheck(QualityCheck):

    @property
    def title(self):
        return "Includes recipient geography" if self.valid else "Missing recipient geography"

    @property
    def description(self):
        if self.valid:
            return "Contains data about the location of the grant recipient."
        return "This file does not contain data about the location of the grant recipient."

    @property
    def valid(self):
        return '/grants/recipientOrganization/postalCode' in self.file.coverage or \
            '/grants/recipientOrganization/location' in self.file.coverage


class PlannedDatesCheck(QualityCheck):

    @property
    def title(self):
        return "Includes planned or actual dates" if self.valid else "Missing planned or actual dates"

    @property
    def description(self):
        if self.valid:
            return "Contains data about the duration and timing of the grants, beyond the date the award was made."
        return "This file does not contain data about the duration and timing of the grants, beyond the date the award was made."

    @property
    def valid(self):
        return '/grants/plannedDates' in self.file.coverage or \
            '/grants/actualDates' in self.file.coverage


class OrganisationIdentifiersCheck(QualityCheck):

    threshold = 0.5

    def __init__(self, file_):
        self.file = file_

        self.external_ids = 0  # count of records using a valid internal identifier
        self.internal_ids = 0  # count of records using a non-external identifier
        self.invalid_ids = 0   # count of records with an invalid identifier

        for prefix, count in self.file.aggregates.get('recipient_org_identifier_prefixes', {}).items():
            if prefix == '360G':
                self.internal_ids += count
            else:
                self.external_ids += count

        for count in self.file.aggregates.get('recipient_org_identifiers_unrecognised_prefixes', {}).values():
            self.invalid_ids += count

        self.valid_ids_pc = self.external_ids / (self.invalid_ids + self.internal_ids + self.external_ids)

    @property
    def title(self):
        return "Includes organisation identifiers" if self.valid else "Missing organisation identifiers"

    @property
    def description(self):
        return "{:,.0f}% of records contain a useful organisation identifier.".format(self.valid_ids_pc * 100)

    @property
    def valid(self):
        return self.valid_ids_pc >= self.threshold
