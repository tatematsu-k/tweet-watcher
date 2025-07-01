# AWS SAM Makefile

.PHONY: build deploy validate local-api local-lambda logs docker-build docker-run

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

docker-build:
	docker build -t tweet-watcher-dev .

docker-run:
	docker run --rm -it -v $$(pwd):/app -p 3000:3000 --env-file .env tweet-watcher-dev
