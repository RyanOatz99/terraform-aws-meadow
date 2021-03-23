import base64
import urllib.parse

import pytest

from handlers.handler import signup


def api_gateway_event(payload: dict) -> dict:
    payload = urllib.parse.urlencode(payload).encode("utf-8")
    payload = base64.b64encode(payload)
    return {
        "resource": "",
        "path": "",
        "httpMethod": "POST",
        "headers": {
            "host": "meadow.test",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        "requestContext": {"resourcePath": "", "http": {"method": "POST"}},
        "body": payload.decode("utf-8"),
    }


def test_newsletter_signup_happy_path(initialise):
    # Validate with email
    email = "test@test.test"
    response = signup(api_gateway_event({"email": email, "secret": "11111111"}), None)
    assert response == {"statusCode": 200, "body": "Success!"}


def test_newsletter_signup_email_already_exists(initialise):
    ddb = initialise[0]
    # Populate with test user
    ddb.put_item(
        TableName="meadow-users",
        Item={
            "partitionKey": {"S": "test@test.test"},
            "sortKey": {"S": "NEWSLETTER_SIGNUP"},
            "random_string": {"S": "12345678"},
        },
    )
    # Validate with email
    email = "test@test.test"
    response = signup(api_gateway_event({"email": email, "secret": "11111111"}), None)
    assert response == {"statusCode": 200, "body": "Success!"}


def test_newsletter_signup_no_email(initialise):
    with pytest.raises(Exception):
        signup(api_gateway_event({}), None)
