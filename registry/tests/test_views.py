from django.test import LiveServerTestCase
from django.urls import reverse_lazy


class TestViewsRespond(LiveServerTestCase):
    def test_views(self):
        urls = [
            reverse_lazy("ui:index"),
            reverse_lazy("data"),
            reverse_lazy("publishers"),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200, f"Url {url} did not return a 200 response"
            )

    def test_json_length(self):
        response = self.client.get(reverse_lazy("data"))
        data = response.json()

        # There are currently 601 datasets 28/02/2024
        self.assertTrue(len(data) > 600)

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
