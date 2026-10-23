from django.conf import settings


def test_localization_defaults():
    assert settings.LANGUAGE_CODE == "es-mx"
    assert settings.TIME_ZONE == "America/Mexico_City"


def test_admin_route_exists(client):
    assert client.get("/admin/", follow=False).status_code == 302
