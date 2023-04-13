from GBNProtocol import GBNProtocol
from SRProtocol import SRProtocol


def write_in_file(data):
    with open("./Peer2/demo.docx", "wb") as f:
        f.write(data)


if __name__ == '__main__':
    local_addr = ('localhost', 8001)
    remote_addr = ('localhost', 8000)

    with open("./Peer2/HITICS-Lab2实验报告.doc", "rb") as f:
        data = f.read()

    connection = SRProtocol(local_addr, remote_addr)
    connection.sender(data)
    connection.receiver(function=write_in_file, joined=True)
