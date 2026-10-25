import pytest
from django.contrib import admin
from django.db import models
from django.test import Client
from django.urls import reverse
from model_bakery import baker


def test_admin_login_page(client: Client, db: None) -> None:
    response = client.get(reverse('admin:login'))
    assert response.status_code == 200


@pytest.mark.parametrize(
    'model', list(admin.site._registry), ids=lambda model: model._meta.label
)
def test_admin_changelist_and_add_pages(
    admin_client: Client, model: type[models.Model]
) -> None:
    baker.make(model)
    opts = model._meta
    for view in ('changelist', 'add'):
        url = reverse(f'admin:{opts.app_label}_{opts.model_name}_{view}')
        assert admin_client.get(url).status_code == 200
