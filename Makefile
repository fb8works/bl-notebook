all: lint test

lint:
	pre-commit run -a --hook-stage pre-commit

test:
	pre-commit run -a --hook-stage pre-push pytest-check

ifeq ($(OS),Windows_NT)
shell:
	venv=$$(poetry env info -p); if [ $$? -ne 0 ]; then poetry install; venv=$$(poetry env info -p); fi; powershell.exe -NoExit -File "$$venv\Scripts\activate.ps1"
else
SHELL=/bin/bash
shell:
	venv=$$(poetry env info -p); if [ $$? -ne 0 ]; then poetry install; venv=$$(poetry env info -p); fi; exec bash <(echo ". \"$$venv/bin/activate\""; echo "exec bash -i")
endif
