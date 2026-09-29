import pytest

from permissions_server.domain.errors import (
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)


@pytest.mark.parametrize(
    ("error_type", "expected_code"),
    [
        (DomainError, "error"),
        (NotFoundError, "not_found"),
        (UnauthorizedError, "unauthorized"),
        (ForbiddenError, "forbidden"),
        (ConflictError, "conflict"),
    ],
)
def test_each_error_type_has_a_generic_default_code(error_type, expected_code):
    error = error_type("english message")
    assert error.code == expected_code
    assert error.params == {}
    assert str(error) == "english message"


def test_explicit_code_and_params_override_the_default():
    error = ConflictError("x", code="invalid_child_type", params={"child": "map"})
    assert error.code == "invalid_child_type"
    assert error.params == {"child": "map"}
    # Message stays the English detail — the code is for client-side translation.
    assert str(error) == "x"


def test_params_are_not_shared_between_instances():
    first = NotFoundError("a")
    first.params["leak"] = 1
    assert NotFoundError("b").params == {}
