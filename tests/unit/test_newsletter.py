from handlers.newsletter import *
from tests.unit import *

def test_newsletter():
    response = signup(api_gateway_event({}), None)
    assert response == {'statusCode': 200, 'body': '"Thank you!"'}