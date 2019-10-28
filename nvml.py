# encoding: utf-8

# the following try/except block will make the custom check compatible with any Agent version
try:
    # first, try to import the base class from old versions of the Agent...
    from checks import AgentCheck
except ImportError:
    # ...if the above failed, the check is running in Agent version 6 or later
    from datadog_checks.checks import AgentCheck

# psutil
import psutil

# pynvml
import pynvml

__version__ = '0.1.5'
__author__ = 'Takashi NAGAI, Alejandro Ferrari'


class NvmlCheck(AgentCheck):

    def _dict2list(self, tags={}):
        return [u"{k}:{v}".format(k=k, v=v) for k, v in tags.items()]

    def check(self, instance):
        pynvml.nvmlInit()

        msg_list = []
        try:
            deviceCount = pynvml.nvmlDeviceGetCount()
        except:
            deviceCount = 0
        for device_id in xrange(deviceCount):
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
            name = pynvml.nvmlDeviceGetName(handle)
            tags = dict(name="{}-{}".format(name, device_id))
            d_tags = self._dict2list(tags)
            # temperature info
            try:
                temp = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU)
                self.gauge('nvml.temp.', temp, tags=d_tags)
            except pynvml.NVMLError as err:
                msg_list.append(u'nvmlDeviceGetTemperature:{}'.format(err))
            # power info
            try:
                pwr = pynvml.nvmlDeviceGetPowerUsage(handle)
                self.gauge('nvml.power.', pwr, tags=d_tags)
            except pynvml.NVMLError as err:
                msg_list.append(u'nvmlDeviceGetPowerUsage:{}'.format(err))
            # memory info
            try:
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                self.gauge('nvml.mem.total', mem.total, tags=d_tags)
                self.gauge('nvml.mem.used', mem.used, tags=d_tags)
                self.gauge('nvml.mem.free', mem.free, tags=d_tags)
            except pynvml.NVMLError as err:
                msg_list.append(u'nvmlDeviceGetMemoryInfo:{}'.format(err))
            # utilization GPU/Memory info
            try:
                util_rate = pynvml.nvmlDeviceGetUtilizationRates(handle)
                self.gauge('nvml.util.gpu', util_rate.gpu, tags=d_tags)
                self.gauge('nvml.util.memory', util_rate.memory, tags=d_tags)
            except pynvml.NVMLError as err:
                msg_list.append(
                    u'nvmlDeviceGetUtilizationRates:{}'.format(err))
            # utilization Encoder info
            try:
                util_encoder = pynvml.nvmlDeviceGetEncoderUtilization(handle)
                self.log.debug('nvml.util.encoder %s' % long(util_encoder[0]))
                self.gauge('nvml.util.encoder', long(
                    util_encoder[0]), tags=d_tags)
            except pynvml.NVMLError as err:
                msg_list.append(
                    u'nvmlDeviceGetEncoderUtilization:{}'.format(err))
            # utilization Decoder info
            try:
                util_decoder = pynvml.nvmlDeviceGetDecoderUtilization(handle)
                self.log.debug('nvml.util.decoder %s' % long(util_decoder[0]))
                self.gauge('nvml.util.decoder', long(
                    util_decoder[0]), tags=d_tags)
            except pynvml.NVMLError as err:
                msg_list.append(
                    u'nvmlDeviceGetDecoderUtilization:{}'.format(err))
            # Compute running processes
            try:
                cps = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                for ps in cps:
                    p_tags = tags.copy()
                    p_tags['pid'] = ps.pid
                    p_tags['name'] = pynvml.nvmlSystemGetProcessName(ps.pid)
                    p_tags = self._dict2list(p_tags)
                    self.gauge('nvml.process.used_gpu_memory',
                               ps.usedGpuMemory, tags=p_tags)
            except pynvml.NVMLError as err:
                msg_list.append(
                    u'nvmlDeviceGetComputeRunningProcesses:{}'.format(err))
        if msg_list:
            status = AgentCheck.CRITICAL
            msg = u','.join(msg_list)
        else:
            status = AgentCheck.OK
            msg = u'Ok'
        pynvml.nvmlShutdown()

        self.service_check('nvml.check', status, message=msg)
