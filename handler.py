import json

def newsletter_signup(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps("Thank you!")
    }