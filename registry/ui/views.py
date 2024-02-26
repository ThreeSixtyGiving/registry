from django.views.generic import TemplateView
from salesforce import salesforce
from datetime import datetime


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["data"] = salesforce.get_salesforce_data()
        context["year_now"] = datetime.now().strftime("%Y")
        return context
