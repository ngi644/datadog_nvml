# encoding: utf-8

# project
from checks import AgentCheck

# pynvml
import pynvml

__version__ = '0.1.0'
__author__ = 'Takashi NAGAI'


class NvmlCheck(AgentCheck):

    def _dict2list(self, tags={}):
        return [u"{k}:{v}".format(k=k, v=v) for k, v in tags.items()]

    def check(self, instance):
        try:
            pynvml.nvmlInit()
            deviceCount = pynvml.nvmlDeviceGetCount()
            for device_id in xrange(deviceCount):
                handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
                name = pynvml.nvmlDeviceGetName(handle)
                tags = dict(name=name)
                d_tags = self._dict2list(tags)
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                cps = pynvml.pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                total = info.total
                free = info.free
                used = info.used
                self.gauge('nvml.gpu.total', total, tags=d_tags)
                self.gauge('nvml.gpu.used', used, tags=d_tags)
                self.gauge('nvml.gpu.free', free, tags=d_tags)
                self.gauge('nvml.gpu.temp', temp, tags=d_tags)
                for ps in cps:
                    p_tags = tags.copy
                    p_tags['pid'] = ps.pid
                    p_tags = self._dict2list(p_tags)
                    self.gauge('nvml.gpu.process', ps.usedGpuMemory, tags=p_tags)
            pynvml.nvmlShutdown()
            status = AgentCheck.OK
            msg = u'Ok'
        except:
            status = AgentCheck.CRITICAL
            msg = u'Error'

        self.service_check('nvml.check', status, message=msg)
