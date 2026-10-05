.PHONY: test

# pytest exits 5 when it collects no tests; treat that as a pass until tests/ has some.
test:
	@python -m pytest tests; rc=$$?; if [ $$rc -eq 5 ]; then echo "no tests yet in tests/"; exit 0; fi; exit $$rc
