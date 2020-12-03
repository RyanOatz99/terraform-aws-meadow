Feature: Allow readers to subscribe to, unsubscribe from, and receive newsletters

    Scenario: Reader signs up to receive the newsletter
        Given I am on the signup page
        And I have not signed up before
        When I enter my email address
        Then I should be thanked for signing up
        And I should receive a confirmation email

    Scenario: Reader tries to sign up to receive the newsletter again within 14 days
        Given I am on the signup page
        And I have entered my email before
        When I enter my email address
        Then I should be thanked for signing up
        And I should not receive a confirmation email

    Scenario: Reader uses the confirmation email to opt-in to receiving newsletters
        Given I am in my email client
        And I have the confirmation email open
        When I click on the confirmation button
        Then I should be redirected to a web page thanking me for confirming
        And I should receive the latest newsletter by email

    Scenario: Reader unsubscribes from the newsletter
        Given I am in my email client
        And I have any newsletter open
        When I click on the unsubscribe button
        Then I should be redirected to a web page confirming that I have unsubscribed
        And I should receive an email confirming that I have unsubscribed

    Scenario: Editor sends a newsletter
        Given I am in the Content Management System
        When I tag a post as "newsletter"
        And I publish the newsletter
        Then The newsletter should be sent to all subscribers