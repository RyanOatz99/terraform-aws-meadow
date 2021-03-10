import base64

import pytest

from handlers.unsubscribe import unsubscribe


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
            "sortKey": {"S": "newsletter"},
            "random_string": {"S": "12345678"},
            "validation_sent": {"BOOL": True},
            "is_validated": {"BOOL": True},
            "is_subscribed": {"BOOL": True}
        }

def newsletter_record() -> dict:
    return {
            "partitionKey": {"S": "newsletter@meadow.test"},
            "sortKey": {"S": "NEWSLETTER_SENT#20210226"},
            "random_string": {"S": "ABCDEFGH"},
        }

def test_newsletter_validate_happy_path(initialise):
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
    newsletter_send_date = "20210226"
    random_string = "ABCDEFGH"
    response = unsubscribe(
        api_gateway_event(
            {
                "email": base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                "newsletter_sent": newsletter_send_date,
                "random_string": random_string,
            }
        ),
        None,
    )
    assert response == {"statusCode": 200, "body": "Success!"}
    # Check user is unsubscribed
    post_unsubscribe_record = ddb.get_item(
        TableName="meadow-users",
        Key={
            "partitionKey": { "S": email },
            "sortKey": {"S": "newsletter" }
        },
        ConsistentRead=True,
        ProjectionExpression="is_subscribed"
    )
    assert post_unsubscribe_record["Item"]["is_subscribed"] == False


def test_newsletter_incorrect_email(initialise):
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
    newsletter_send_date = "20210226"
    random_string = "ABCDEFGH"
    with pytest.raises(Exception):
        unsubscribe(
            api_gateway_event(
                {
                    "email": base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                    "newsletter_sent": newsletter_send_date,
                    "random_string": random_string,
                }
            ),
            None,
        )
    # Check user is still subscribed
    post_unsubscribe_record = ddb.get_item(
        TableName="meadow-users",
        Key={
            "partitionKey": { "S": email },
            "sortKey": {"S": "newsletter" }
        },
        ConsistentRead=True,
        ProjectionExpression="is_subscribed"
    )
    assert post_unsubscribe_record["Item"]["is_subscribed"] == True

def test_newsletter_incorrect_send_date(initialise):
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
    # Validate with incorrect newsletter_send_date
    email = "test@test.test"
    newsletter_send_date = "20200226"
    random_string = "ABCDEFGH"
    with pytest.raises(Exception):
        unsubscribe(
            api_gateway_event(
                {
                    "email": base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                    "newsletter_sent": newsletter_send_date,
                    "random_string": random_string,
                }
            ),
            None,
        )
    # Check user is still subscribed
    post_unsubscribe_record = ddb.get_item(
        TableName="meadow-users",
        Key={
            "partitionKey": { "S": email },
            "sortKey": {"S": "newsletter" }
        },
        ConsistentRead=True,
        ProjectionExpression="is_subscribed"
    )
    assert post_unsubscribe_record["Item"]["is_subscribed"] == True

def test_newsletter_incorrect_random_string(initialise):
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
    newsletter_send_date = "20210226"
    random_string = "incorrect"
    with pytest.raises(Exception):
        unsubscribe(
            api_gateway_event(
                {
                    "email": base64.urlsafe_b64encode(email.encode()).decode("ascii"),
                    "newsletter_sent": newsletter_send_date,
                    "random_string": random_string,
                }
            ),
            None,
        )
    # Check user is still subscribed
    post_unsubscribe_record = ddb.get_item(
        TableName="meadow-users",
        Key={
            "partitionKey": { "S": email },
            "sortKey": {"S": "newsletter" }
        },
        ConsistentRead=True,
        ProjectionExpression="is_subscribed"
    )
    assert post_unsubscribe_record["Item"]["is_subscribed"] == True

def test_newsletter_incorrect_corrupt_encoding(initialise):
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
    newsletter_send_date = "20210226"
    random_string = "ABCDEFGH"
    with pytest.raises(Exception):
        unsubscribe(
            api_gateway_event(
                {
                    "email": base64.urlsafe_b64encode(email.encode()).decode("ascii") + "1",
                    "newsletter_sent": newsletter_send_date,
                    "random_string": random_string,
                }
            ),
            None,
        )
    # Check user is still subscribed
    post_unsubscribe_record = ddb.get_item(
        TableName="meadow-users",
        Key={
            "partitionKey": { "S": email },
            "sortKey": {"S": "newsletter" }
        },
        ConsistentRead=True,
        ProjectionExpression="is_subscribed"
    )
    assert post_unsubscribe_record["Item"]["is_subscribed"] == True

def test_newsletter_missing_element(initialise):
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
    # Validate with missing newsletter_send_date
    email = "wrong@test.test"
    random_string = "ABCDEFGH"
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
        Key={
            "partitionKey": { "S": email },
            "sortKey": {"S": "newsletter" }
        },
        ConsistentRead=True,
        ProjectionExpression="is_subscribed"
    )
    assert post_unsubscribe_record["Item"]["is_subscribed"] == True
