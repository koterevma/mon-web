prepare-env:
	-@mkdir venv && python3 -m venv venv

setup: prepare-env
	. venv/bin/activate
	pip install --no-cache-dir -U pip wheel
	pip install -r requirements.txt --no-cache-dir
