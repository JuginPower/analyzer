from django.urls import path
from . import views

urlpatterns = [
    path('', views.load_chat_view, name='chat_view'),
    path('response/', views.chatbot_response, name='chatbot_response'),
]
