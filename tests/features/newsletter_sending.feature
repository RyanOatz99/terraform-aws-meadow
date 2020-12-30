#Feature: Allow Editors to send newsletters
#
#    Scenario: Editor sends a newsletter
#        Given I am in the Content Management System
#        When I tag a post as "newsletter"
#        And I publish the newsletter
#        Then The newsletter should be sent to all subscribers
#
#    Scenario: Reader receives the newsletter and clicks "Mark as Spam"
#        Given I am in my email client
#        And I have any newsletter open
#        When I click on "Mark as Spam" in my email client
#        Then I should be unsubscribed from the newsletter