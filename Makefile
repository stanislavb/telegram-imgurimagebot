build:
	docker build --force-rm -t $(shell basename $(CURDIR)) .
run:
	docker run -it $(shell basename $(CURDIR)) $(TOKEN) --imgur_id $(IMGUR_ID) --imgur_secret $(IMGUR_SECRET)
rmi:
	docker rmi $(shell basename $(CURDIR))
