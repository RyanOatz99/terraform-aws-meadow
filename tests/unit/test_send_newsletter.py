import pytest

from handlers.handler import send_newsletter


def subscriber_record() -> dict:
    return {
        "partitionKey": {"S": "test@test.test"},
        "sortKey": {"S": "EMAIL_SENT#20210226010203"},
        "random_string": {"S": "12345678"},
        "is_subscribed": {"S": "true"},
    }


def test_send_newsletter_happy_path(initialise):
    event = {
        "newsletter_slug": "20210421",
        "newsletter_subject": "Meadow Testing Newsletter",
    }
    response = send_newsletter(event, None)
    assert response == 0


def test_send_newsletter_cannot_load_slug_details_from_event(initialise):
    with pytest.raises(KeyError, match="newsletter_slug"):
        send_newsletter({"newsletter_subject": "Meadow Testing Newsletter"}, None)


def test_send_newsletter_cannot_load_subject_details_from_event(initialise):
    with pytest.raises(KeyError, match="newsletter_subject"):
        send_newsletter({"newsletter_slug": "20210421"}, None)


def test_send_newsletter_slug_is_empty(initialise):
    with pytest.raises(
        ValueError, match="Newsletter slug and newsletter subject cannot be empty."
    ):
        event = {
            "newsletter_slug": " ",
            "newsletter_subject": "Meadow Testing Newsletter",
        }
        send_newsletter(event, None)


def test_send_newsletter_subject_is_empty(initialise):
    with pytest.raises(
        ValueError, match="Newsletter slug and newsletter subject cannot be empty."
    ):
        event = {
            "newsletter_slug": "123456",
            "newsletter_subject": " ",
        }
        send_newsletter(event, None)


def test_send_newsletter_template_separate_is_incorrect(
    initialiseTemplateWithIncorrectSeperator,
):
    with pytest.raises(Exception, match="Template does not contain correct separator"):
        event = {
            "newsletter_slug": "20210421",
            "newsletter_subject": "Meadow Testing Newsletter",
        }
        send_newsletter(event, None)


def test_send_newsletter_template_body_is_empty(initialiseTemplateWithoutBody):
    with pytest.raises(Exception, match="Template does not contain correct separator"):
        event = {
            "newsletter_slug": "20210421",
            "newsletter_subject": "Meadow Testing Newsletter",
        }
        send_newsletter(event, None)


def test_send_newsletter_html_template_is_empty(initialiseWithEmptyHtmlTemplate):
    with pytest.raises(Exception, match="Newsletter HTML template cannot be empty."):
        event = {
            "newsletter_slug": "20210421",
            "newsletter_subject": "Meadow Testing Newsletter",
        }
        send_newsletter(event, None)


def test_send_newsletter_text_template_is_empty(initialiseWithEmptyTextTemplate):
    with pytest.raises(Exception, match="Newsletter text template cannot be empty."):
        event = {
            "newsletter_slug": "20210421",
            "newsletter_subject": "Meadow Testing Newsletter",
        }
        send_newsletter(event, None)


def test_send_newsletter_cannot_load_subscribers(initialiseWithIncorrectIndex):
    with pytest.raises(Exception, match="Could not load subscribers from users table"):
        event = {
            "newsletter_slug": "20210421",
            "newsletter_subject": "Meadow Testing Newsletter",
        }
        send_newsletter(event, None)


def test_send_newsletter_email_send_fails_without_raising_error(initialiseWithoutSes):
    ddb = initialiseWithoutSes[0]
    # Populate with test user
    ddb.put_item(
        TableName="meadow-users",
        Item=subscriber_record(),
    )
    ddb.put_item(
        TableName="meadow-users",
        Item=subscriber_record(),
    )
    event = {
        "newsletter_slug": "20210421",
        "newsletter_subject": "Meadow Testing Newsletter",
    }
    # Send fails but we expect no exception to be raised, only logged.
    response = send_newsletter(event, None)
    assert response == 0
