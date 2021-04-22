import os

test_domain = os.environ["TEST_DOMAIN"]
build_number = os.environ.get("CIRCLE_BUILD_NUM", "local-build")
test_gmail_username = os.environ["TEST_GMAIL_USERNAME"]
email = test_gmail_username + "+" + build_number + "@gmail.com"
honeypot_secret = 11111111
barn_bucket = os.environ["BARN_BUCKET"]
