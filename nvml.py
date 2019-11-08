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

# These values are not exposed through Pynvml, but are reported in the throttle
# reasons. The reason values are defined in
# https://github.com/NVIDIA/gpu-monitoring-tools/blob/master/bindings/go/nvml/nvml.h
# Indicates that the clocks are throttled because the GPU is part of a sync
# boost group, which syncs the clocks to the minimum clocks across the group.
# Corresponds to nvmlClocksThrottleReasonSyncBoost.
GPU_THROTTLE_SYNCBOOST = 0x10
# Indicates that the GPU core or memory temperature is above max. Corresponds to
# nvmlClocksThrottleReasonSwThermalSlowdown.
GPU_THROTTLE_THERMAL_SLOWDOWN_SOFTWARE = 0x20
# Indicates that the clocks are throttled by 50% or more due to very high
# temperature. Corresponds to nvmlClocksThrottleReasonHwThermalSlowdown.
GPU_THROTTLE_THERMAL_SLOWDOWN_HARDWARE = 0x40
# Indicates that the clocks are throttled by 50% or more by the power supply.
# Corresponds to nvmlClocksThrottleReasonHwPowerBrakeSlowdown.
GPU_THROTTLE_POWER_BRAKE_SLOWDOWN_HARDWARE = 0x80
# Indicates that the clocks are throttled by the current display settings.
# Corresponds to nvmlClocksThrottleReasonDisplayClockSetting.
GPU_THROTTLE_DISPLAY_CLOCKS_SETTINGS = 0x100


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
        # Number of active GPUs
        self.gauge('nvml.gpus.number', deviceCount)
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
                pwr = pynvml.nvmlDeviceGetPowerUsage(handle) // 1000
                self.gauge('nvml.power.', pwr, tags=d_tags)
            except pynvml.NVMLError as err:
                msg_list.append(u'nvmlDeviceGetPowerUsage:{}'.format(err))
            # fan info
            try:
                fan = pynvml.nvmlDeviceGetFanSpeed(handle)
                self.gauge('nvml.fan.', fan, tags=d_tags)
            except pynvml.NVMLError as err:
                msg_list.append(u'nvmlDeviceGetFanSpeed:{}'.format(err))
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
            # Clocks throttling info
            # Divide by the mask so that the value is either 0 or 1 per GPU
            try:
                throttle_reasons = (
                    pynvml.nvmlDeviceGetCurrentClocksThrottleReasons(handle))
                self.gauge('nvml.throttle.appsettings', (throttle_reasons &
                    pynvml.nvmlClocksThrottleReasonApplicationsClocksSetting) /
                    pynvml.nvmlClocksThrottleReasonApplicationsClocksSetting,
                    tags=d_tags)
                self.gauge('nvml.throttle.display', (throttle_reasons &
                    GPU_THROTTLE_DISPLAY_CLOCKS_SETTINGS) /
                    GPU_THROTTLE_DISPLAY_CLOCKS_SETTINGS,
                    tags=d_tags)
                self.gauge('nvml.throttle.hardware', (throttle_reasons &
                    pynvml.nvmlClocksThrottleReasonHwSlowdown) /
                    pynvml.nvmlClocksThrottleReasonHwSlowdown,
                    tags=d_tags)
                self.gauge('nvml.throttle.idle', (throttle_reasons &
                    pynvml.nvmlClocksThrottleReasonGpuIdle) /
                    pynvml.nvmlClocksThrottleReasonGpuIdle,
                    tags=d_tags)
                self.gauge('nvml.throttle.power.hardware', (throttle_reasons &
                    GPU_THROTTLE_POWER_BRAKE_SLOWDOWN_HARDWARE) /
                    GPU_THROTTLE_POWER_BRAKE_SLOWDOWN_HARDWARE,
                    tags=d_tags)
                self.gauge('nvml.throttle.power.software', (throttle_reasons &
                    pynvml.nvmlClocksThrottleReasonSwPowerCap) /
                    pynvml.nvmlClocksThrottleReasonSwPowerCap,
                    tags=d_tags)
                self.gauge('nvml.throttle.syncboost', (throttle_reasons &
                    GPU_THROTTLE_SYNCBOOST) / GPU_THROTTLE_SYNCBOOST,
                    tags=d_tags)
                self.gauge('nvml.throttle.temp.hardware', (throttle_reasons &
                    GPU_THROTTLE_THERMAL_SLOWDOWN_HARDWARE) /
                    GPU_THROTTLE_THERMAL_SLOWDOWN_HARDWARE,
                    tags=d_tags)
                self.gauge('nvml.throttle.temp.software', (throttle_reasons &
                    GPU_THROTTLE_THERMAL_SLOWDOWN_SOFTWARE) /
                    GPU_THROTTLE_THERMAL_SLOWDOWN_SOFTWARE,
                    tags=d_tags)
                self.gauge('nvml.throttle.unknown', (throttle_reasons &
                    pynvml.nvmlClocksThrottleReasonUnknown) /
                    pynvml.nvmlClocksThrottleReasonUnknown,
                    tags=d_tags)
            except pynvml.NVMLError as err:
                msg_list.append(
                    u'nvmlDeviceGetCurrentClocksThrottleReasons:{}'.format(err))
        if msg_list:
            status = AgentCheck.CRITICAL
            msg = u','.join(msg_list)
        else:
            status = AgentCheck.OK
            msg = u'Ok'
        pynvml.nvmlShutdown()

        self.service_check('nvml.check', status, message=msg)
