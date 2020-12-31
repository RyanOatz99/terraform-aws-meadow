from handlers.newsletter import signup
from tests.unit import api_gateway_event


def test_newsletter():
    response = signup(api_gateway_event({}), None)
    assert response == {"statusCode": 200, "body": '"Thank you!"'}
