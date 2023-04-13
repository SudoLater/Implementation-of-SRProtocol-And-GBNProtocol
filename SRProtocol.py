import socket
import threading
import math
import pickle
import random

from TransportProtocol import TransportProtocol


LOSS_RATE = 0.02


class SRProtocol(TransportProtocol):
    def __init__(self, local_address, remote_address, window_size=4, timeout=1, package_size=4096):
        self.local_address = local_address
        self.remote_address = remote_address

        self.window_size = window_size
        self.timeout = timeout
        self.package_size = package_size

    def send(self, data):
        send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        send_sock.settimeout(self.timeout)
        base = 0
        sent_package = {}
        while base < len(data):
            for i in range(self.window_size):
                try:
                    while sent_package[base + i] is not None and sent_package[base + i] == 'recv':
                        base += 1
                        if base == len(data):
                            raise RuntimeError
                except KeyError as e:
                    print(e)
                except RuntimeError as e:
                    print("All package have sent.")
                    send_sock.sendto(b'close', self.remote_address)
                    return
                except Exception as e:
                    print(e)

            for i in range(self.window_size):
                if base + i < len(data):
                    print(f'Sending packet {base + i}')
                    packet = (base + i).to_bytes(16, byteorder='big') + data[base + i]
                    if random.random() > LOSS_RATE:
                        send_sock.sendto(packet, self.remote_address)
                        sent_package[base + i] = ''
                    else:
                        pass
                else:
                    pass

            try:
                ack, _ = send_sock.recvfrom(1024)
                ack = pickle.loads(ack)
                print(f'Received ACK for packet {ack}')
                sent_package[ack] = 'recv'
                # base = ack + 1

            except socket.timeout:
                print(f'Timeout occurred. Resending the window {base}')

    def recv(self, function):
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        recv_sock.bind(self.local_address)
        recv_sock.settimeout(self.timeout)
        base = 0
        recv_packages = {}
        finished = False
        data = b''
        while not finished:
            try:
                packet, sender_address = recv_sock.recvfrom(self.package_size)
                seq_num = int.from_bytes(packet[:16], byteorder='big')
                datum = packet[16:]

                try:
                    if packet[:16].decode('UTF-8') == 'close':
                        finished = True
                        raise RuntimeError
                except UnicodeError as e:
                    pass
                except RuntimeError as e:
                    print("All packets received, closing connection")
                    for i in range(len(recv_packages)):
                        data += recv_packages[i]

                    function(data)
                    return

                if base <= seq_num < base + self.window_size:
                    print(f'Received packet {seq_num}')
                    recv_packages[seq_num] = datum

                    recv_sock.sendto(pickle.dumps(seq_num), sender_address)
                    print(f'Sending ACK for packet {seq_num}')

                else:
                    print(f'Out of order packet {seq_num} received.')

                for i in range(self.window_size):
                    try:
                        while recv_packages[base + i] is not None:
                            base += 1
                    except KeyError as e:
                        print(e)
                    except Exception as e:
                        print(e)
                print(f"Refresh recv window:{base}")
            except socket.timeout:
                pass

    def sender(self, data, joined=False):
        send_thread = threading.Thread(target=self.send, args=(self.split_packages(data),))  # args=(self.split_packages(data)))
        send_thread.start()
        if joined:
            send_thread.join()

    def receiver(self, function, joined=False):
        receive_thread = threading.Thread(target=self.recv, args=(function,))
        receive_thread.start()
        if joined:
            receive_thread.join()

    def split_packages(self, data):
        package_size = self.package_size - 16
        num_packets = math.ceil(len(data) / package_size)
        packets = []
        for i in range(num_packets):
            start = i * package_size
            end = start + package_size if start + package_size < len(data) else len(data)
            packets.append(data[start:end])
        return packets
