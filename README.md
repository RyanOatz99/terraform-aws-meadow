# Meadow

A Grassroots Membership System

## What is Meadow?

Meadow is a membership system that is built using Serverless Framework and (Python) Functions, and runs on AWS. It allows organisations of any size to take advantage of the instant elasticity of AWS Serverless technologies.

## Should I know anything before using it?

Yes - it is _very easy_ to accidentally spend a lot of money in AWS! If this is a surprise to you, Meadow is not meant for you - ask a friendly local Cloud Ops Engineer for help deploying Meadow. Meadow is designed to be used by everyone - but it is not designed to be deployed by anyone. We of course won't be held responsible for any costs, security issues or errant thunderstorms that arise from deploying Meadow to your AWS Cloud.

## Okay, I'll be careful! How do I deploy it?

1. Configure your AWS credentials as you would for aws-cli (if you already have them configured then skip this step).
1. Configure the tool by modifying the following json dictionary and adding it to the SSM Parameter store, under the key `MeadowDictionary`:

        {
            "organisation": "Your Organisation Name",
            "table": "a-valid-dynamodb-table-name",
            "domain": "your-organisation.com",
            "region": "yr-dply-1"
        }

1. Add your sending domain to SES (and for production, get yourself out of the sandbox).
1. Run `make sls-deploy`

That's it! To remove it from your account, use `make sls-remove` - and to get details about your deployment use `make sls-info`. Behind the scenes Serverless Framework is creating CloudFormation Stack, which you can view in AWS directly (though we do not recommend manipulating these stacks manually).

## How do I get started with development?

Meadow uses an extensive makefile - be sure to have the latest version of Python installed and get started with `make install`.

We use `black`, `isort` and `flake8` to ensure conformity - these can be run against your code with `make black`, `make isort` and `make flake8` respectively (or run all three with `make conformity-tests`). Code will not be accepted if it fails these tests - but `black` and `isort` will also automatically fix your code for you!

Unit tests are placed in `tests/unit/` and can be run with `make unit-tests`. No code will be accepted if they do not have sufficient coverage and we encourage a Test-Driven Development approach to this (but if you don't know how to do this then talk to us in the respective issue and we'll give guidance).

Feature tests are placed in `tests/features/` and can be run with `make feature-tests`. Note that feature tests are end-to-end and rely on an active cloud deployment of Meadow, deployed with `sls-deploy`. Do not run tests against production deployments(!) since some testing may be destructive.

### Fixing bugs

Bugs should be reported as Issues in the issue tracker. All bugs should be caught as tests - so be sure to edit the relevant feature or unit test that should have captured that behaviour, preferably _before_ you go ahead and fix it. 

### Adding new features

Meadow is built using Behaviour-Driven Development - particularly, we use pytest-bdd to specify new features. As such, it's really easy to get started:

1. Create a new `.feature` file in `tests/features/` (or copy an existing one). Be sure to give it a sensible name describing your feature.
1. Add a description of your feature at the top, after a `Feature: ` tag. This should specify the type of user that would be using this feature.
1. Use `Scenario: ` to specify high-level scenarios that describe what a user might do with this feature, and what they would expect to happen. Describe using `Given`, `When`, `Then` syntax - and remember, a feature usually has more than one scenario.
1. Create step definitions that define how to test each step in your new feature's scenarios, by creating a file in `tests/features/step_defs` and populating it using the necessary decorators (e.g. `@scenario` and `@given`). Again, it's recommended that you use existing step definitions as a template - and remember, all python test files must start `test_`.
1. Once this is done you may start implementing the features:
    - Add new functions (AWS Lambdas) and resources to `serverless.yml`
    - Write unit tests for your functions in `tests/unit` (again, remember to prefix new files with `test_`)
    - Write your functions in `handlers/`
1. Feel free to open up a Pull Request early and keep updating it as you go along - this allows people to comment and offer guidance on how best to implement your feature within the wider project.

In practice, most features will start off as raised Issues - workshop your Feature and Scenarios with the community so that we can ensure good discovery and formulation before you go ahead and start coding!

## License

MIT License