from unittest.mock import patch

from django.test import LiveServerTestCase
from django.urls import reverse_lazy
from tests.mock_simple_salesforce.threesixty import MockSimpleSalesforce360Giving

NUM_DATASETS = 51
NUM_DATASETS_NOT_APPROVED = 1
NUM_DATASETS_APPROVED = NUM_DATASETS - NUM_DATASETS_NOT_APPROVED
NUM_ORGANISATIONS = 11
NUM_ORGANISATIONS_NO_PREFIX = 1
NUM_ORGANISATIONS_WITH_PREFIX = NUM_ORGANISATIONS - NUM_ORGANISATIONS_NO_PREFIX


class TestViewsRespond(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        cls.mock_sf = MockSimpleSalesforce360Giving()
        cls.mock_sf.init_mock_registry(
            NUM_ORGANISATIONS,
            NUM_DATASETS,
            num_accounts_no_prefix=NUM_ORGANISATIONS_NO_PREFIX,
            num_datasets_not_approved=NUM_DATASETS_NOT_APPROVED,
        )
        cls.patcher = patch(
            "salesforce.salesforce.get_salesforce_access", return_value=cls.mock_sf
        )
        cls.patcher.start()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def test_views(self):
        urls = [
            reverse_lazy("ui:index"),
            reverse_lazy("data"),
            reverse_lazy("publishers"),
            reverse_lazy("funders"),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200, f"Url {url} did not return a 200 response"
            )

    def test_json_length(self):
        response = self.client.get(reverse_lazy("data"))
        data = response.json()

        self.assertTrue(len(data) == NUM_DATASETS_APPROVED)

        # Check these keys are in at least the first item
        for key in [
            "title",
            "description",
            "identifier",
            "license",
            "license_name",
            "issued",
            "modified",
            "publisher",
            "distribution",
        ]:
            self.assertIn(key, data[0].keys())

    def test_funders_json(self):
        response = self.client.get(reverse_lazy("funders"))
        data = response.json()

        cur = self.mock_sf.con.cursor()
        expected_ids = [
            row[0]
            for row in cur.execute(
                "SELECT Id FROM Account WHERE "
                "X360Giving_Publisher__c = 'Funder in GrantNav' "
                "OR X360Giving_Publisher__c = '360Giving Publisher';"
            ).fetchall()
        ]

        self.assertEqual(sorted(data.keys()), sorted(expected_ids))

        for account_id, funder in data.items():
            self.assertEqual(funder["id"], account_id)
            self.assertIn(
                funder["x360GivingPublisher"],
                ["Funder in GrantNav", "360Giving Publisher"],
            )
            for key in ["name", "prefix", "orgIdentifier"]:
                self.assertIn(key, funder.keys())

    def test_funders_json_excludes_non_funders(self):
        response = self.client.get(reverse_lazy("funders"))
        data = response.json()

        cur = self.mock_sf.con.cursor()
        excluded_ids = [
            row[0]
            for row in cur.execute(
                "SELECT Id FROM Account WHERE "
                "X360Giving_Publisher__c IS NULL "
                "OR (X360Giving_Publisher__c != 'Funder in GrantNav' "
                "AND X360Giving_Publisher__c != '360Giving Publisher');"
            ).fetchall()
        ]

        self.assertTrue(len(excluded_ids) > 0)
        for account_id in excluded_ids:
            self.assertNotIn(account_id, data.keys())
