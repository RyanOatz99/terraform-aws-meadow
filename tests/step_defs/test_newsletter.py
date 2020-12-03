import random
from pytest_bdd import scenario, given, when, then

@scenario('newsletter.feature', 'Reader signs up to receive the newsletter')
def test_newsletter():
    pass

@given("I am on the signup page")
def signup_page():
    url = website_endpoint + '/newsletter_signup'

@given("I have not signed up before")
def new_user():
    # Creating a random email address, unlikely to be in the database
    email = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) + '@' + test_domain

@when("I enter my email address")
def enter_email():
    assert blah
    # Enter email into web page

@then("I should be thanked for signing up")
def entered_email():
    "thank you" in response.text.lowercase()

@then("")
def received_optin_request():
    # Email received