from functools import partial

import requests
from pytest_bdd import given, scenario, then
from step_defs import build_number, test_domain

scenario = partial(scenario, "newsletter_signup.feature")


# Scenarios
@scenario("Reader signs up to receive the newsletter")
def test_newsletter_new_signup():
    pass


# Steps
@given("I sign up with a new email address", target_fixture="response")
def signup_page_url():
    url = "https://" + test_domain + "/newsletter_signup"
    email = "success+" + build_number + "@simulator.amazonses.com"
    data = {"email": email}
    try:
        response = requests.post(url, data=data)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    return response


@then("I should be thanked for signing up")
def entered_email(response):
    assert "Thank you" in response.text
