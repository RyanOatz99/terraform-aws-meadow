from time import sleep

import requests
from pytest_bdd import given, scenarios, then
from simplegmail import Gmail
from step_defs import email, test_domain
from urlextract import URLExtract

scenarios("newsletter_signup.feature")


# Steps
@given("I sign up with a new email address", target_fixture="response")
@given("I sign up with the same email address again", target_fixture="response")
def signup_page_url():
    url = "https://" + test_domain + "/signup"
    data = {"email": email}
    try:
        response = requests.post(url, json=data)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    return response


@then("I should be thanked for signing up")
@then("I should get a Success message")
def entered_email(response):
    assert "Success!" in response.text
    assert response.status_code == 200


@then("I should receive a confirmation email")
def received_confirmation():
    gmail = Gmail()
    retry = 20
    match = False
    while retry != 0 and match is False:
        sleep(5)
        messages = gmail.get_unread_inbox()
        for message in messages:
            if message.recipient == email:
                match = True
        retry = retry - 1
    assert match is True


@then("I should not receive a confirmation email")
def not_received_confirmation():
    gmail = Gmail()
    match = False
    sleep(60)
    messages = gmail.get_unread_inbox()
    for message in messages:
        if message.recipient == email:
            match = match + 1
    assert match == 1


@given("I click the verify link in my confirmation email", target_fixture="validation")
def clicked_confirmation():
    gmail = Gmail()
    extractor = URLExtract()
    messages = gmail.get_unread_inbox()
    for message in messages:
        if message.recipient == email and "Confirm your request" in message.subject:
            urls = extractor.find_urls(message.plain)

    try:
        validation = requests.get(urls[0])
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    return validation


@then("I should be redirected to a web page thanking me for confirming")
def email_validated(validation):
    assert "Success!" in validation.text
    assert validation.status_code == 200


@given("I click the unsubscribe link in any email", target_fixture="response")
def click_unsubscribe():
    gmail = Gmail()
    extractor = URLExtract()
    messages = gmail.get_unread_inbox()
    for message in messages:
        if message.recipient == email and "Confirm your request" in message.subject:
            urls = extractor.find_urls(message.plain)

    try:
        validation = requests.get(urls[1])
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    return validation
