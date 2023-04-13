import socket
import threading
import math
import pickle
import random

from TransportProtocol import TransportProtocol


LOSS_RATE = 0.02


class GBNProtocol(TransportProtocol):
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
        next_seq_num = 0
        while base < len(data):
            while next_seq_num < base + self.window_size and next_seq_num < len(data):
                print(f'Sending packet {next_seq_num}')
                packet = next_seq_num.to_bytes(16, byteorder='big') + data[next_seq_num]
                if random.random() > LOSS_RATE:
                    send_sock.sendto(packet, self.remote_address)
                next_seq_num += 1

            try:
                ack, _ = send_sock.recvfrom(1024)
                ack = pickle.loads(ack)
                print(f'ack is {ack}')
                base = ack + 1
                print(f'Received ACK for packet {ack}')

            except socket.timeout:
                print('Timeout occurred. Resending the window')
                next_seq_num = base
        send_sock.sendto(b'close', self.remote_address)

    def recv(self, function):
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        recv_sock.bind(self.local_address)
        recv_sock.settimeout(self.timeout)
        expected_seq_num = 0
        finished = False
        data = []
        while not finished:
            try:
                packet, sender_address = recv_sock.recvfrom(self.package_size)
                seq_num = int.from_bytes(packet[:16], byteorder='big')
                datum = packet[16:]

                try:
                    if packet[:16].decode('UTF-8') == 'close':
                        print("All packets received, closing connection")
                        finished = True
                        break
                except UnicodeError as e:
                    pass

                if seq_num == expected_seq_num:
                    print(f'Received packet {seq_num}')
                    data.append(datum)

                    print(f'seq_num is {seq_num}')

                    recv_sock.sendto(pickle.dumps(seq_num), sender_address)
                    print(f'Sending ACK for packet {seq_num}')
                    expected_seq_num += 1

                else:
                    print(f'Out of order packet {seq_num} received. Discarding and sending ACK for packet {expected_seq_num - 1}')
                    recv_sock.sendto(pickle.dumps(expected_seq_num - 1), sender_address)

            except socket.timeout:
                pass

        function(b''.join(data))

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
        print(num_packets)
        for i in range(num_packets):
            start = i * package_size
            end = start + package_size if start + package_size < len(data) else len(data)
            packets.append(data[start:end])
        print(len(packets[0]))
        return packets
