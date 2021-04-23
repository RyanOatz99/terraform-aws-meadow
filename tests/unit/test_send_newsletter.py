from handlers.handler import send_newsletter


def test_send_newsletter_happy_path(initialise):
    send_newsletter(
        {
            "newsletter_slug": "20210421",
            "newsletter_subject": "Meadow Testing Newsletter",
        },
        None,
    )
