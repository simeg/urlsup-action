.PHONY: dockerfile publish-dockerfile

BIN_NAME  = urlsup
VERSION   = 2.0.0
DOCKER    = $(shell which docker)

dockerfile:
	$(DOCKER) build -t simeg/urlsup:latest -t simeg/urlsup:$(VERSION) -f Dockerfile .

publish-dockerfile: dockerfile
	$(DOCKER) push simeg/urlsup:2.0.0 &&
	$(DOCKER) push simeg/urlsup:latest
