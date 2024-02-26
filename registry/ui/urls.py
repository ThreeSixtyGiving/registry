from django.urls import path

import ui.views

app_name = "ui"

urlpatterns = [
    path("", ui.views.IndexView.as_view(), name="index"),
]
