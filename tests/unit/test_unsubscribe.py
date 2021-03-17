import base64

import pytest

from handlers.handler import unsubscribe


def api_gateway_event(payload: dict) -> dict:
    return {
        "resource": "",
        "path": "",
        "httpMethod": "GET",
        "headers": {"host": "meadow.test"},
        "requestContext": {"resourcePath": "", "http": {"method": "GET"}},
        "queryStringParameters": payload,
    }


def subscription_record() -> dict:
    return {
        "partitionKey": {"S": "test@test.test"},
        "sortKey": {"S": "NEWSLETTER_SIGNUP"},
        "random_string": {"S": "12345678"},
        "is_validated": {"BOOL": True},
        "is_subscribed": {"BOOL": True},
    }


def newsletter_record() -> dict:
    return {
        "partitionKey": {"S": "test@test.test"},
        "sortKey": {"S": "EMAIL_SENT#20210226010203"},
        "random_string": {"S": "12345678"},
    }


def test_newsletter_unsubscribe_happy_path(initialise):
    ddb = initialise[0]
    # Populate with test user
    ddb.put_item(
        TableName="meadow-users",
        Item=subscription_record(),
    )
    ddb.put_item(
        TableName="meadow-users",
        Item=newsletter_record(),
    )
    # Validate with correct details
    email = "test@test.test"
    email_sent_date = "20210226010203"
    random_string = "12345678"
    response = unsubscribe(
        api_gateway_event(
            {
                "email": base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                "email_sent": email_sent_date,
                "random_string": random_string,
            }
        ),
        None,
    )
    assert response == {"statusCode": 200, "body": "Success!"}
    # Check user is unsubscribed
    post_unsubscribe_record = ddb.get_item(
        TableName="meadow-users",
        Key={"partitionKey": {"S": email}, "sortKey": {"S": "NEWSLETTER_SIGNUP"}},
        ConsistentRead=True,
        ProjectionExpression="is_subscribed",
    )
    assert post_unsubscribe_record["Item"]["is_subscribed"]["BOOL"] is False


def test_newsletter_unsubscribe_incorrect_email(initialise):
    ddb = initialise[0]
    # Populate with test user
    ddb.put_item(
        TableName="meadow-users",
        Item=subscription_record(),
    )
    ddb.put_item(
        TableName="meadow-users",
        Item=newsletter_record(),
    )
    # Validate with incorrect email
    email = "wrong@test.test"
    email_sent_date = "20210226010203"
    random_string = "12345678"
    with pytest.raises(Exception):
        unsubscribe(
            api_gateway_event(
                {
                    "email": base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                    "email_sent": email_sent_date,
                    "random_string": random_string,
                }
            ),
            None,
        )
    # Since the email is wrong we cannot check the user is still subscribed


def test_newsletter_unsubscribe_incorrect_send_date(initialise):
    ddb = initialise[0]
    # Populate with test user
    ddb.put_item(
        TableName="meadow-users",
        Item=subscription_record(),
    )
    ddb.put_item(
        TableName="meadow-users",
        Item=newsletter_record(),
    )
    # Validate with incorrect email_send date
    email = "test@test.test"
    email_sent_date = "20200226010203"
    random_string = "12345678"
    with pytest.raises(Exception):
        unsubscribe(
            api_gateway_event(
                {
                    "email": base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                    "email_sent": email_sent_date,
                    "random_string": random_string,
                }
            ),
            None,
        )
    # Check user is still subscribed
    post_unsubscribe_record = ddb.get_item(
        TableName="meadow-users",
        Key={"partitionKey": {"S": email}, "sortKey": {"S": "NEWSLETTER_SIGNUP"}},
        ConsistentRead=True,
        ProjectionExpression="is_subscribed",
    )
    assert post_unsubscribe_record["Item"]["is_subscribed"]["BOOL"] is True


def test_newsletter_unsubscribe_incorrect_random_string(initialise):
    ddb = initialise[0]
    # Populate with test user
    ddb.put_item(
        TableName="meadow-users",
        Item=subscription_record(),
    )
    ddb.put_item(
        TableName="meadow-users",
        Item=newsletter_record(),
    )
    # Validate with incorrect random_string
    email = "test@test.test"
    email_sent_date = "20210226010203"
    random_string = "incorrect"
    with pytest.raises(Exception):
        unsubscribe(
            api_gateway_event(
                {
                    "email": base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                    "email_sent": email_sent_date,
                    "random_string": random_string,
                }
            ),
            None,
        )
    # Check user is still subscribed
    post_unsubscribe_record = ddb.get_item(
        TableName="meadow-users",
        Key={"partitionKey": {"S": email}, "sortKey": {"S": "NEWSLETTER_SIGNUP"}},
        ConsistentRead=True,
        ProjectionExpression="is_subscribed",
    )
    assert post_unsubscribe_record["Item"]["is_subscribed"]["BOOL"] is True


def test_newsletter_unsubscribe_corrupt_encoding(initialise):
    ddb = initialise[0]
    # Populate with test user
    ddb.put_item(
        TableName="meadow-users",
        Item=subscription_record(),
    )
    ddb.put_item(
        TableName="meadow-users",
        Item=newsletter_record(),
    )
    # Validate with corrupt encoding
    email = "test@test.test"
    email_sent_date = "20210226010203"
    random_string = "12345678"
    with pytest.raises(Exception):
        unsubscribe(
            api_gateway_event(
                {
                    "email": "booo"
                    + base64.urlsafe_b64encode(email.encode()).decode("ascii")
                    + "y",
                    "email_sent": email_sent_date,
                    "random_string": random_string,
                }
            ),
            None,
        )
    # Check user is still subscribed
    post_unsubscribe_record = ddb.get_item(
        TableName="meadow-users",
        Key={"partitionKey": {"S": email}, "sortKey": {"S": "NEWSLETTER_SIGNUP"}},
        ConsistentRead=True,
        ProjectionExpression="is_subscribed",
    )
    assert post_unsubscribe_record["Item"]["is_subscribed"]["BOOL"] is True


def test_newsletter_unsubscribe_missing_element(initialise):
    ddb = initialise[0]
    # Populate with test user
    ddb.put_item(
        TableName="meadow-users",
        Item=subscription_record(),
    )
    ddb.put_item(
        TableName="meadow-users",
        Item=newsletter_record(),
    )
    # Validate with missing email_send date
    email = "test@test.test"
    random_string = "12345678"
    with pytest.raises(Exception):
        unsubscribe(
            api_gateway_event(
                {
                    "email": base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                    "random_string": random_string,
                }
            ),
            None,
        )
    # Check user is still subscribed
    post_unsubscribe_record = ddb.get_item(
        TableName="meadow-users",
        Key={"partitionKey": {"S": email}, "sortKey": {"S": "NEWSLETTER_SIGNUP"}},
        ConsistentRead=True,
        ProjectionExpression="is_subscribed",
    )
    assert post_unsubscribe_record["Item"]["is_subscribed"]["BOOL"] is True
