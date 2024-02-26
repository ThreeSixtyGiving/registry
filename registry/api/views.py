from django.http.response import JsonResponse
from django.views import View

from salesforce import salesforce


class DataView(View):
    def get(self, *args, **kwargs):
        return JsonResponse(salesforce.get_salesforce_data(), safe=False)


class PublishersView(View):
    def get(self, *args, **kwargs):
        return JsonResponse(salesforce.get_salesforce_publishers(), safe=False)
