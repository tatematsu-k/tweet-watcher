# AWS SAM Makefile

.PHONY: build deploy validate local-api local-lambda logs

build:
	sam build

deploy:
	sam deploy --guided

validate:
	sam validate

local-api:
	sam local start-api

local-lambda:
	sam local invoke "HelloWorldFunction" -e events/event.json

logs:
	sam logs -n HelloWorldFunction --stack-name "tweet-watcher" --tail
