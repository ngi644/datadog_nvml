# datadog_nvml

NVIDIA GPU Monitoring for Datadog

NVIDIAのGPUの状態をモニタリングする `Agent Check` スクリプトです．
`nvidia-ml-py` モジュールを利用しています．

## 現在のモニタ項目

現在は以下の項目についてGPU毎に取得します．

### Metrics

- gpu.total: トータルメモリ
- gpu.used: 使用中メモリ
- gpu.free: 空きメモリ
- gpu.temp: 温度

### Tags

- name: GPU名(例: GEFORCE_GTX_660)


# REQUIRES

nvidia-ml-py モジュールが必須です．

- https://pypi.python.org/pypi/nvidia-ml-py

```
$ sudo /opt/datadog-agent/embedded/bin/pip install nvidia-ml-py
```

# SETUP

同梱されている二つのファイルを以下のディレクトリにコピーします．

- nvml.py: /etc/dd-agent/checks.d
- nvml.yaml.default: /etc/dd-agent/conf.d

```
$ sudo cp nvml.py /etc/dd-agent/checks.d
$ sudo cp nvml.yaml.default /etc/dd-agent/conf.d
```

Datadogを再起動します．

```
$ sudo service datadog-agent restart
```

