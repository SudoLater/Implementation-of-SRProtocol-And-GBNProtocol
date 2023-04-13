from abc import ABC, abstractmethod


# 定义传输协议的接口
class TransportProtocol(ABC):
    # 阻塞传输
    @abstractmethod
    def send(self, data):
        pass

    # 阻塞接受
    @abstractmethod
    def recv(self, function):
        pass

    # 非阻塞传输
    @abstractmethod
    def sender(self, data, joined):
        pass

    # 非阻塞接受
    @abstractmethod
    def receiver(self, function, joined):
        pass

    # 分割数据包
    @abstractmethod
    def split_packages(self, data):
        pass
