"""Tests for the custom User model."""

import uuid
import pytest
from accounts.models import User


@pytest.mark.django_db
def test_user_model_pk_is_uuid():
    pk_field = User._meta.pk
    assert pk_field.name == "id"
    from django.db.models import UUIDField
    assert isinstance(pk_field, UUIDField)


@pytest.mark.django_db
def test_user_model_default_pk_is_uuid4():
    user = User(username="testuser")
    assert isinstance(user.id, uuid.UUID)


@pytest.mark.django_db
def test_user_model_pk_not_sequential():
    user_a = User(username="a")
    user_b = User(username="b")
    assert user_a.id != user_b.id
