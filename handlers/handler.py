import base64
import json
import logging
import random
import string
import urllib.parse
from datetime import datetime

import boto3
import botocore
from boto3.dynamodb.conditions import Key
from jinja2 import Template


def initialise():
    # Initialise Logger
    logger = logging.getLogger()

    # Connect to SSM and load in the Meadow Dictionary
    ssm = boto3.client("ssm")
    try:
        meadow = json.loads(
            ssm.get_parameter(Name="MeadowDictionary")["Parameter"]["Value"]
        )
    except botocore.exceptions.ClientError as error:
        logger.info("Could not retrieve MeadowDictionary SSM Parameter")
        raise error
    # Connect to the DynamoDB table
    dynamodb = boto3.resource("dynamodb")
    try:
        table = dynamodb.Table(meadow["table"])
    except botocore.exceptions.ClientError as error:
        logger.info("Could not connect to DynamoDB Table")
        raise error

    return logger, meadow, table


def signup(event, context):
    # Initialise
    logger, meadow, table = initialise()

    # Connect to SES
    ses = boto3.client("ses", region_name=meadow["region"])

    # Load details from event
    try:
        body = base64.b64decode(event["body"].encode("utf-8"))
        body = urllib.parse.parse_qs(body.decode("utf-8"))
        email = body["email"][0]
        secret = body["secret"][0]
    except KeyError as error:
        logger.info("Could not load email from body")
        raise error

    try:
        assert secret == meadow["honeypot_secret"]
    except AssertionError as error:
        logger.info("Secret does not match or does not exist")
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
        return {
            "statusCode": 301,
            "headers": {
                "Location": "https://"
                + meadow["website_domain"]
                + "/newsletter_validating"
            },
        }

    # Send Validation Email
    # This needs an EXTENSIVE rewrite once we start sending newsletters!
    SENDER = meadow["organisation"] + " <noreply@" + meadow["meadow_domain"] + ">"
    SUBJECT = (
        "Confirm your request to recieve the " + meadow["organisation"] + " newsletter"
    )
    CHARSET = "UTF-8"

    s3 = boto3.resource("s3")
    combined_template = (
        s3.Object(meadow["barn"], "transactional/validate.j2")
        .get()["Body"]
        .read()
        .decode("utf-8")
    )
    validation_html_template = Template(
        combined_template.split("---TEXT-HTML-SEPARATOR---")[0]
    )
    validation_text_template = Template(
        combined_template.split("---TEXT-HTML-SEPARATOR---")[1]
    )

    email_sent_date = datetime.now().strftime("%Y%m%d%H%M%S")

    validation_url = (
        "https://"
        + meadow["meadow_domain"]
        + "/validate?email="
        + base64.urlsafe_b64encode(email.encode()).decode("ascii")
        + "&random_string="
        + random_string
    )

    unsubscribe_url = (
        "https://"
        + meadow["meadow_domain"]
        + "/unsubscribe?email="
        + base64.urlsafe_b64encode(email.encode()).decode("ascii")
        + "&random_string="
        + random_string
        + "&email_sent="
        + email_sent_date
    )

    BODY_HTML = validation_html_template.render(
        validation_path=validation_url, unsubscribe_path=unsubscribe_url
    )

    BODY_TEXT = validation_text_template.render(
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
                    "Html": {
                        "Charset": CHARSET,
                        "Data": BODY_HTML,
                    },
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
    return {
        "statusCode": 301,
        "headers": {
            "Location": "https://" + meadow["website_domain"] + "/newsletter_validating"
        },
    }


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
            ExpressionAttributeValues={":x": "false"},
        )
    except botocore.exceptions.ClientError as error:
        logger.info("Email does not exist!")
        raise error

    return {
        "statusCode": 301,
        "headers": {
            "Location": "https://"
            + meadow["website_domain"]
            + "/newsletter_unsubscribed"
        },
    }


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

    # Check email exists, random_string matches, then subscribe the user
    try:
        table.update_item(
            Key={"partitionKey": email, "sortKey": "NEWSLETTER_SIGNUP"},
            UpdateExpression="SET is_subscribed = :x",
            ExpressionAttributeValues={":x": "true", ":y": random_string},
            ConditionExpression="attribute_exists(partitionKey) AND random_string = :y",
        )
    except botocore.exceptions.ClientError as error:
        logger.info("Email does not exist, or random_string does not match!")
        raise error

    return {
        "statusCode": 301,
        "headers": {
            "Location": "https://" + meadow["website_domain"] + "/newsletter_success"
        },
    }


def send_newsletter(event, context):
    # Initialise
    logger, meadow, table = initialise()

    # Load details from event
    try:
        newsletter_slug = event["newsletter_slug"]
        newsletter_subject = event["newsletter_subject"]
    except KeyError as error:
        logger.info("Could not load newsletter details from event")
        raise error

    # Load email template from bucket
    s3 = boto3.resource("s3")
    try:
        combined_template = (
            s3.Object(meadow["barn"], "newsletters/" + newsletter_slug + ".j2")
            .get()["Body"]
            .read()
            .decode("utf-8")
        )
    except botocore.exceptions.ClientError as error:
        logger.info("Could not load template from s3 bucket")
        raise error

    # Check for split point and separate HTML and text templates
    try:
        assert "---TEXT-HTML-SEPARATOR---" in combined_template
    except AssertionError as error:
        logger.info("Template does not contain correct separator")
        raise error

    validation_html_template = Template(
        combined_template.split("---TEXT-HTML-SEPARATOR---")[0]
    )
    validation_text_template = Template(
        combined_template.split("---TEXT-HTML-SEPARATOR---")[1]
    )

    # Load subscribers from users table
    try:
        subscribers = table.query(
            IndexName="is_subscribed",
            KeyConditionExpression=Key("is_subscribed").eq("true"),
        )
    except KeyError as error:
        logger.info("Could not load subscribers from users table")
        raise error

    # Connect to SES
    ses = boto3.client("ses", region_name=meadow["region"])

    # Set common newsletter attributes
    email_sent_date = datetime.now().strftime("%Y%m%d%H%M%S")
    SENDER = meadow["organisation"] + " <noreply@" + meadow["meadow_domain"] + ">"
    SUBJECT = newsletter_subject
    CHARSET = "UTF-8"

    # Iterate over subscribers and send them the newsletter
    for subscriber in subscribers["Items"]:

        # Add the email to a more descriptive variable name
        email = subscriber["partitionKey"]

        # Create random string for each user (for unsubscribes)
        random_string = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=32)
        )

        # Create Unsubscribe address
        unsubscribe_url = (
            "https://"
            + meadow["meadow_domain"]
            + "/unsubscribe?email="
            + base64.urlsafe_b64encode(email.encode()).decode("ascii")
            + "&random_string="
            + random_string
            + "&email_sent="
            + email_sent_date
        )

        # Render HTML and Text body for the newsletter
        BODY_HTML = validation_html_template.render(unsubscribe_path=unsubscribe_url)
        BODY_TEXT = validation_text_template.render(unsubscribe_path=unsubscribe_url)

        # Attempt to send the newsletter
        try:
            ses.send_email(
                Destination={
                    "ToAddresses": [
                        email,
                    ],
                },
                Message={
                    "Body": {
                        "Html": {
                            "Charset": CHARSET,
                            "Data": BODY_HTML,
                        },
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
            logger.info("Could not send newsletter:" + error)
            continue

    return 0
