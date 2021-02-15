import json
import logging

import boto3
import botocore


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
