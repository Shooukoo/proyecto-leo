from django.urls import path

from . import views

urlpatterns = [
    path("chat/", views.ChatView.as_view(), name="chat"),
    path("conversaciones/", views.ConversacionListView.as_view(), name="conversaciones"),
    path(
        "conversaciones/<str:conversation_id>/",
        views.ConversacionDetalleView.as_view(),
        name="conversacion-detalle",
    ),
]
