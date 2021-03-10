import base64

import botocore

from handlers import initialise


def unsubscribe(event, context):
    # Initialise
    logger, meadow, table = initialise()

    # Decode email string
    try:
        email = base64.urlsafe_b64decode(
            event["queryStringParameters"]["email"].encode("ascii")
        ).decode()
    except base64.binascii.Error as error:
        logger("Cannot decode email string")
        raise error

    # Load in random_string
    try:
        random_string = event["queryStringParameters"]["random_string"]
    except KeyError as error:
        logger("Cannot fetch random_string")
        raise error

    # Load in email_sent date
    try:
        email_sent = event["queryStringParameters"]["email_sent"]
    except KeyError as error:
        logger("Cannot fetch email_sent date")
        raise error

    # Check email exists, and newsletter_date & random_string matches a newsletter
    # Then set is_subscribed to False
    try:
        validate_email_sent = table.get_item(
            Key={
                "partitionKey": email,
                "sortKey": "EMAIL_SENT#" + email_sent,
            },
            ConsistentRead=True,
            ProjectionExpression="random_string",
        )
        assert validate_email_sent["Item"]["random_string"] == random_string
    except AssertionError as error:
        logger.info(
            (
                "Could not find a newsletter matching both email_sent and"
                "random_string!"
            )
        )
        raise error

    try:
        table.update_item(
            Key={"partitionKey": email, "sortKey": "NEWSLETTER_SIGNUP"},
            UpdateExpression="SET is_subscribed = :x",
            ExpressionAttributeValues={":x": False},
        )
    except botocore.exceptions.ClientError as error:
        logger.info("Email does not exist!")
        raise error

    return {"statusCode": 200, "body": "Success!"}
