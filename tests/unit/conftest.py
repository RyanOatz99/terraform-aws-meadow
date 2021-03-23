import boto3
import pytest
from moto import mock_dynamodb2, mock_ses, mock_ssm


@pytest.fixture(scope="function")
def initialise():
    # Mock endpoints
    mockdynamodb2 = mock_dynamodb2()
    mockssm = mock_ssm()
    mockses = mock_ses()

    # Start endpoints
    mockdynamodb2.start()
    mockssm.start()
    mockses.start()
    boto3.setup_default_session()

    # Create mock verified SES users
    ses = boto3.client("ses")
    ses.verify_email_identity(EmailAddress="noreply@meadow.test")
    ses.verify_email_identity(EmailAddress="test@test.test")

    # Create mock users DynamoDB table
    ddb = boto3.client("dynamodb")
    ddb.create_table(
        AttributeDefinitions=[
            {"AttributeName": "partitionKey", "AttributeType": "S"},
            {"AttributeName": "sortKey", "AttributeType": "S"},
        ],
        TableName="meadow-users",
        KeySchema=[
            {
                "AttributeName": "partitionKey",
                "KeyType": "HASH",
            },
            {
                "AttributeName": "sortKey",
                "KeyType": "RANGE",
            },
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )

    # Create mock SSM
    ssm = boto3.client("ssm")
    ssm.put_parameter(
        Name="MeadowDictionary",
        Value=(
            '{ "organisation": "Meadow Testing","table": "meadow-users", '
            '"domain": "meadow.test", "region": "us-east-1", '
            '"honeypot_secret": "11111111" }'
        ),
        Type="String",
    )

    yield ddb, ssm, ses

    # Stop endpoints
    mockdynamodb2.stop()
    mockssm.stop()
    mockses.stop()
