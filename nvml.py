# encoding: utf-8

# project
from checks import AgentCheck

# psutil
import psutil

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
                tags = dict(name="{}-{}".format(name,device_id))
                d_tags = self._dict2list(tags)
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                util_rate = pynvml.nvmlDeviceGetUtilizationRates(handle)
                cps = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                # utilization info
                self.gauge('nvml.util.gpu', util_rate.gpu, tags=d_tags)
                self.gauge('nvml.util.memory', util_rate.memory, tags=d_tags)
                # memory info
                self.gauge('nvml.mem.total', mem.total, tags=d_tags)
                self.gauge('nvml.mem.used', mem.used, tags=d_tags)
                self.gauge('nvml.mem.free', mem.free, tags=d_tags)
                # temperature info
                self.gauge('nvml.temp.', temp, tags=d_tags)
                for ps in cps:
                    p_tags = tags.copy()
                    p_tags['pid'] = ps.pid
                    p_tags['name'] = psutil.Process(ps.pid).name()
                    p_tags = self._dict2list(p_tags)
                    self.gauge('nvml.process.used_gpu_memory', ps.usedGpuMemory, tags=p_tags)
            status = AgentCheck.OK
            msg = u'Ok'
        except:
            status = AgentCheck.CRITICAL
            msg = u'Error'
        finally:
            pynvml.nvmlShutdown()

        self.service_check('nvml.check', status, message=msg)
