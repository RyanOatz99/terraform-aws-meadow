import os

test_domain = os.environ["TEST_DOMAIN"]
build_number = os.environ.get("CIRCLE_BUILD_NUM", "local-build")
