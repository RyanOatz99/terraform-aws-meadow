import os
import requests
from functools import partial
from pytest_bdd import scenario, given, when, then

test_domain = os.environ['TEST_DOMAIN']
build_number = os.environ['CIRCLE_BUILD_NUM']

scenario = partial(scenario, "newsletter_signup.feature")

# Scenarios
@scenario('Reader signs up to receive the newsletter')
def test_newsletter_new_signup():
    pass

# Steps
@given("I sign up with a new email address", target_fixture='response')
def signup_page_url():
    url = 'https://' + test_domain + '/newsletter_signup'
    email = 'success+' + build_number + '@simulator.amazonses.com'
    data = {
        'email': email
    }
    response = requests.post(url, data = data)
    return response

@then("I should be thanked for signing up")
def entered_email(response):
    if "Thank you" in response:
        assert True
    else:
        assert False
