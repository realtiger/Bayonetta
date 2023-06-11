import time

from watchtower import settings

logger = settings.LOGGER

class InvalidSystemClock(Exception):
    """
    时钟回拨异常
    """
    pass


class Snow:
    """
    雪花算法生成全局自增唯一id
    """

    def __init__(self, server_id=0, datacenter_id=0, sequence=0):
        # 64位ID的划分
        server_id_bits = 5
        datacenter_id_bits = 5
        sequence_bits = 12

        # 最大取值计算 机房和机器的ID
        max_server_id = -1 ^ (-1 << server_id_bits)  # 2**5-1 0b11111
        max_datacenter_id = -1 ^ (-1 << datacenter_id_bits)

        # sanity check
        # 最大编号可为00-31  实际使用范围 00-29  备用 30 31
        if server_id > max_server_id or server_id < 0:
            raise ValueError('worker_id值越界')

        if datacenter_id > max_datacenter_id or datacenter_id < 0:
            raise ValueError('datacenter_id值越界')

        # 移位偏移计算
        self.server_id_shift = sequence_bits
        self.datacenter_id_shift = sequence_bits + server_id_bits
        self.timestamp_left_shift = sequence_bits + server_id_bits + datacenter_id_bits

        # 序号循环掩码
        self.sequence_mask = -1 ^ (-1 << sequence_bits)

        # Twitter元年时间戳
        self.tw_epoch = 1288834974657

        self.server_id = server_id
        self.datacenter_id = datacenter_id
        self.sequence = sequence

        # 上次计算的时间戳
        self.last_timestamp = int(time.time() * 1000)

    def get_id(self):
        """
        获取雪花算法生成的id
        :return:
        """
        # 生成整数时间戳
        now_timestamp = int(time.time() * 1000)

        # 时钟回拨
        if now_timestamp < self.last_timestamp:
            logger.error(f'clock is moving backwards. Rejecting requests until {self.last_timestamp}')
            raise InvalidSystemClock

        if now_timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & self.sequence_mask
            # sequence 大于 4096强制停1ms
            if self.sequence == 0:
                while True:
                    now_timestamp = int(time.time() * 1000)
                    if now_timestamp > self.last_timestamp:
                        break
        else:
            self.sequence = 0

        new_id = ((now_timestamp - self.tw_epoch) << self.timestamp_left_shift) | \
                 (self.datacenter_id << self.datacenter_id_shift) | \
                 (self.server_id << self.server_id_shift) | self.sequence

        return new_id


class SnowShort:
    """
    雪花算法生成全局自增唯一id
    为了适应前段js显示，修改雪花算法，将显示位数缩小为53位
    时间戳(41位)-工作机器id(6位)-序列号(6位)：最大支持64个workerId, 每毫秒生成64个序列号
    """

    def __init__(self, server_id=0, datacenter_id=0, sequence=0):
        # 53位ID的划分
        server_id_bits = 4
        datacenter_id_bits = 2
        sequence_bits = 6

        # 最大取值计算 机房和机器的ID
        max_server_id = -1 ^ (-1 << server_id_bits)  # 2**5-1 0b11111
        max_datacenter_id = -1 ^ (-1 << datacenter_id_bits)

        # sanity check
        if server_id > max_server_id or server_id < 0:
            raise ValueError('worker_id值越界')

        if datacenter_id > max_datacenter_id or datacenter_id < 0:
            raise ValueError('datacenter_id值越界')

        # 移位偏移计算
        self.server_id_shift = sequence_bits
        self.datacenter_id_shift = sequence_bits + server_id_bits
        self.timestamp_left_shift = sequence_bits + server_id_bits + datacenter_id_bits

        # 序号循环掩码
        self.sequence_mask = -1 ^ (-1 << sequence_bits)

        # 基准时间戳，人为规定为 2023/01/11 00:00:00
        self.tw_epoch = 1673366400000

        self.server_id = server_id
        self.datacenter_id = datacenter_id
        self.sequence = sequence

        # 上次计算的时间戳
        self.last_timestamp = int(time.time() * 1000)

    def get_id(self):
        """
        获取雪花算法生成的id
        :return:
        """
        # 生成整数时间戳
        now_timestamp = int(time.time() * 1000)

        # 时钟回拨
        if now_timestamp < self.last_timestamp:
            logger.error(f'clock is moving backwards. Rejecting requests until {self.last_timestamp}')
            raise InvalidSystemClock

        if now_timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & self.sequence_mask
            # sequence 大于 4096强制停1ms
            if self.sequence == 0:
                while True:
                    now_timestamp = int(time.time() * 1000)
                    if now_timestamp > self.last_timestamp:
                        break
        else:
            self.sequence = 0

        new_id = ((now_timestamp - self.tw_epoch) << self.timestamp_left_shift) | \
                 (self.datacenter_id << self.datacenter_id_shift) | \
                 (self.server_id << self.server_id_shift) | self.sequence

        return new_id


snow = SnowShort(server_id=settings.SERVER_ID, datacenter_id=settings.DATACENTER_ID)
