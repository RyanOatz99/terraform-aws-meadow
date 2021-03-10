import base64
import json
import random
import string
from datetime import datetime

import boto3
import botocore
from jinja2 import Template

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
            Item={
                "partitionKey": email,
                "sortKey": "NEWSLETTER_SIGNUP",
                "random_string": random_string,
            },
            ConditionExpression="attribute_not_exists(partitionKey)",
        )
    except botocore.exceptions.ClientError:
        logger.info("Email already exists!")
        # Never tell the user what happened, any error should be internal
        return {"statusCode": 200, "body": "Success!"}

    # Send Validation Email
    # This needs an EXTENSIVE rewrite once we start sending newsletters!
    SENDER = "Meadow Validation <noreply@" + meadow["domain"] + ">"
    SUBJECT = (
        "Confirm your request to recieve the " + meadow["organisation"] + " newsletter"
    )
    CHARSET = "UTF-8"

    with open("handlers/email_content/validate_TEXT.j2") as file:
        body_template = Template(file.read())

    email_sent_date = datetime.now().strftime("%Y%m%d%H%M%S")

    validation_url = (
        "https://"
        + event["headers"]["host"]
        + "/validate?email="
        + base64.urlsafe_b64encode(email.encode()).decode("ascii")
        + "&random_string="
        + random_string
    )

    unsubscribe_url = (
        "https://"
        + event["headers"]["host"]
        + "/unsubscribe?email="
        + base64.urlsafe_b64encode(email.encode()).decode("ascii")
        + "&random_string="
        + random_string
        + "&email_sent="
        + email_sent_date
    )

    BODY_TEXT = body_template.render(
        validation_path=validation_url, unsubscribe_path=unsubscribe_url
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
        table.put_item(
            Item={
                "partitionKey": email,
                "sortKey": "EMAIL_SENT#" + email_sent_date,
                "random_string": random_string,
            },
            ConditionExpression="attribute_not_exists(partitionKey)",
        )
    except botocore.exceptions.ClientError as error:
        logger.info("Could not send validation email")
        raise error

    # Never tell the user what happened, any error should be internal
    return {"statusCode": 200, "body": "Success!"}
