from time import sleep

import boto3
import requests
from pytest_bdd import given, scenarios, then
from simplegmail import Gmail
from step_defs import barn_bucket, email, honeypot_secret, test_domain
from urlextract import URLExtract

scenarios("newsletter.feature")


# Steps
@given("I sign up with a new email address", target_fixture="signup")
@given("I sign up with the same email address again", target_fixture="signup")
def signup_page_url():
    url = "https://" + test_domain + "/signup"
    form = {"email": email, "secret": honeypot_secret}
    try:
        signup = requests.post(url, data=form, allow_redirects=False)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    return signup


@then("I should be told to validate my email address")
def entered_email(signup):
    assert "newsletter_validating" in signup.headers["location"]
    assert signup.status_code == 301


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
        validation = requests.get(urls[0], allow_redirects=False)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    return validation


@then("I should be redirected to a web page thanking me for confirming")
def email_validated(validation):
    assert "newsletter_success" in validation.headers["location"]
    assert validation.status_code == 301


@given("I click the unsubscribe link in any email", target_fixture="unsubscribed")
def click_unsubscribe():
    gmail = Gmail()
    extractor = URLExtract()
    messages = gmail.get_unread_inbox()
    for message in messages:
        if message.recipient == email and "Confirm your request" in message.subject:
            urls = extractor.find_urls(message.plain)

    try:
        unsubscribed = requests.get(urls[1], allow_redirects=False)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    return unsubscribed


@then("I should be told I have successfully unsubscribed")
def email_unsubscribed(unsubscribed):
    assert "newsletter_unsubscribed" in unsubscribed.headers["location"]
    assert unsubscribed.status_code == 301


@given("A newsletter is uploaded to be sent")
def send_newsletter():
    s3 = boto3.client("s3")
    mock_email = """
    This is a cool newsletter!

    To unsubscribe, click here: {{ unsubscribe_path }}
    ---TEXT-HTML-SEPARATOR---
    This is a cool newsletter!

    To unsubscribe, click here: {{ unsubscribe_path }}
    """.encode(
        "utf-8"
    )
    s3.put_object(Body=mock_email, Bucket=barn_bucket, Key="newsletters/20210421.j2")


@given("that newsletter is triggered to be sent")
def invoke_send_newsletter():
    aws_lambda = boto3.client("lambda", region_name="us-east-1")
    aws_lambda.invoke(
        FunctionName="send_newsletter",
        Payload=(
            b'{"newsletter_slug": "20210421","newsletter_subject":'
            b'"The Meadow Testing Monthly Newsletter"}'
        ),
    )


@then("I should receive the newsletter")
def newsletter_sent():
    gmail = Gmail()
    retry = 20
    match = False
    while retry != 0 and match is False:
        sleep(5)
        messages = gmail.get_unread_inbox()
        for message in messages:
            if (
                message.recipient == email
                and "The Meadow Testing Monthly Newsletter" in message.subject
            ):
                match = True
        retry = retry - 1
    assert match is True
