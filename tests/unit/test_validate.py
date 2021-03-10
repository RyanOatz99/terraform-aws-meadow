import base64

import pytest

from handlers.validate import validate


def api_gateway_event(payload: dict) -> dict:
    return {
        "resource": "",
        "path": "",
        "httpMethod": "GET",
        "headers": {"host": "meadow.test"},
        "requestContext": {"resourcePath": "", "http": {"method": "GET"}},
        "queryStringParameters": payload,
    }


def test_newsletter_validate_happy_path(initialise):
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
    # Validate with correct email and random_string
    email = "test@test.test"
    random_string = "12345678"
    response = validate(
        api_gateway_event(
            {
                "email": base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                "random_string": random_string,
            }
        ),
        None,
    )
    assert response == {"statusCode": 200, "body": "Success!"}


def test_newsletter_incorrect_email(initialise):
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
    # Validate with incorrect email
    email = "test@wrong.email"
    random_string = "12345678"
    with pytest.raises(Exception):
        validate(
            api_gateway_event(
                {
                    "email": base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                    "random_string": random_string,
                }
            ),
            None,
        )


def test_newsletter_corrupt_encoding(initialise):
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
    # Validate with corrupt encoding
    email = "test@test.test"
    random_string = "12345678"
    with pytest.raises(Exception):
        validate(
            api_gateway_event(
                {
                    "email": "boo"
                    + base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                    "random_string": random_string,
                }
            ),
            None,
        )


def test_newsletter_incorrect_random_string(initialise):
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
    # Validate with incorrect random_string
    email = "test@test.test"
    random_string = "12345678"
    with pytest.raises(Exception):
        validate(
            api_gateway_event(
                {
                    "email": base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                    "random_string": "7" + random_string,
                }
            ),
            None,
        )


def test_newsletter_no_random_string(initialise):
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
    # Validate with no random_string
    email = "test@test.test"
    with pytest.raises(Exception):
        validate(
            api_gateway_event(
                {"email": base64.urlsafe_b64encode(email.encode()).decode("ascii")}
            ),
            None,
        )
