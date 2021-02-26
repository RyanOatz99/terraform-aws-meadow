import base64

import botocore

from handlers import initialise


def validate(event, context):
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

    # Check email exists, random_string matches, then set validated to True
    try:
        table.update_item(
            Key={"partitionKey": email, "sortKey": "newsletter"},
            UpdateExpression="SET validated = :x",
            ExpressionAttributeValues={":x": True, ":y": random_string},
            ConditionExpression="attribute_exists(partitionKey) AND random_string = :y",
        )
    except botocore.exceptions.ClientError as error:
        logger.info("Email does not exist, or random_string does not match!")
        raise error

    return {"statusCode": 200, "body": "Success!"}
