Feature: Allow Readers to subscribe to and unsubscribe from newsletters

    Scenario: Reader signs up to receive the newsletter
        Given I sign up with a new email address
        Then I should be thanked for signing up
#        And I should receive a confirmation email
#
#    Scenario: Reader tries to sign up to receive the newsletter again within 14 days
#        Given I sign up with the same email address again
#        Then I should be thanked for signing up
#        And I should not receive a confirmation email
#
#    Scenario: Reader tries to sign up with an invalid email address
#        Given I sign up with an invalid email address
#        Then I should be told that my email address is invalid
#
#    Scenario: Reader uses the confirmation email to opt-in to receiving newsletters
#        Given I click the verify link in my confirmation email
#        Then I should be redirected to a web page thanking me for confirming
#        And I should receive the latest newsletter by email
#
#    Scenario: Reader unsubscribes from the newsletter
#        Given I click the unsubscribe link in any newsletter
#        Then I should be redirected to a web page confirming that I have unsubscribed
#        And I should receive an email confirming that I have unsubscribed