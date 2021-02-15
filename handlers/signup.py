import base64
import json
import random
import string

import boto3
import botocore

from handlers import initialise


def signup(event, context):
    # Initialise
    logger, meadow, table = initialise()

    # Connect to SES
    ses = boto3.client("ses", region_name=meadow["region"])

    # Load details from event
    try:
        email = json.loads(event["body"])["email"]
    except KeyError as error:
        logger.info("Could not load email from body")
        raise error

    # Add email and random_string to table, if it doesn't already exist
    random_string = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=32)
    )
    try:
        table.put_item(
            Item={"email": email, "random_string": random_string},
            ConditionExpression="attribute_not_exists(email)",
        )
    except botocore.exceptions.ClientError:
        logger.info("Email already exists!")
        # Never tell the user what happened, any error should be internal
        return {"statusCode": 200, "body": "Success!"}

    # Send Validation Email
    SENDER = "Meadow Validation <noreply@" + meadow["domain"] + ">"
    SUBJECT = (
        "Confirm your request to recieve the " + meadow["organisation"] + " newsletter"
    )
    CHARSET = "UTF-8"

    with open("handlers/email_content/validate_TEXT") as file:
        BODY_TEXT = file.read()

    BODY_TEXT = (
        BODY_TEXT
        + "https://"
        + event["headers"]["host"]
        + "/validate?email="
        + base64.urlsafe_b64encode(email.encode()).decode("ascii")
        + "&random_string="
        + random_string
    )

    try:
        ses.send_email(
            Destination={
                "ToAddresses": [
                    email,
                ],
            },
            Message={
                "Body": {
                    "Text": {
                        "Charset": CHARSET,
                        "Data": BODY_TEXT,
                    },
                },
                "Subject": {
                    "Charset": CHARSET,
                    "Data": SUBJECT,
                },
            },
            Source=SENDER,
        )
        table.update_item(
            Key={"email": email},
            UpdateExpression="SET validation_sent = :x",
            ExpressionAttributeValues={":x": True},
        )
    except botocore.exceptions.ClientError as error:
        logger.info("Could not send validation email")
        raise error

    # Never tell the user what happened, any error should be internal
    return {"statusCode": 200, "body": "Success!"}
