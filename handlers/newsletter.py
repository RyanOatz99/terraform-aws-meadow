import json


def signup(event, context):
    return {"statusCode": 200, "body": json.dumps("Thank you!")}
