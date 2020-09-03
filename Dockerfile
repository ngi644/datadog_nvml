FROM datadog/agent:latest

ENV NVIDIA_VISIBLE_DEVICES=all

RUN mkdir -p /etc/datadog-agent/checks.d/ && \
    mkdir -p /etc/datadog-agent/conf.d/nvml.d && \
    /opt/datadog-agent/embedded/bin/pip install nvidia-ml-py3==7.352.0

ADD https://raw.githubusercontent.com/ngi644/datadog_nvml/master/nvml.py /etc/datadog-agent/checks.d/nvml.py
ADD https://raw.githubusercontent.com/ngi644/datadog_nvml/master/nvml.yaml.default /etc/datadog-agent/conf.d/nvml.d/nvml.yaml

RUN chown -R dd-agent /etc/datadog-agent/checks.d/nvml.py && \
    chown -R dd-agent /etc/datadog-agent/conf.d/nvml.d/nvml.yaml
