all: install

install: nvidia-ml-py
	@echo "Copying files..."
	@sudo -u dd-agent -- cp -a nvml.py /etc/datadog-agent/checks.d/nvml.py
	@sudo -u dd-agent -- cp -a nvml.yaml.default /etc/datadog-agent/conf.d/nvml.yaml.default
	@echo "Done."
	@echo "Restarting daemon..."
	@sudo systemctl restart datadog-agent
	@echo "Done."

nvidia-ml-py:
	@sudo -u dd-agent -H -- /opt/datadog-agent/embedded/bin/pip install -r requirements.txt

check:
	@sudo -u dd-agent -- datadog-agent check nvml

.PHONY: install nvidia-ml-py check
