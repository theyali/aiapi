from django.urls import path

from .views import chat_completions_view


app_name = "gateway"


urlpatterns = [
    path("v1/chat/completions/",chat_completions_view,name="chat_completions"),
]