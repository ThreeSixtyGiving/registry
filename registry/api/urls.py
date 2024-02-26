from django.urls import path

import api.views

app_name = "api"

urlpatterns = [
    path("", api.views.DataView.as_view(), name="data"),
]
