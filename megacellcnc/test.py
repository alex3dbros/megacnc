import socket
import netaddr


def portscan(port, host, res_dict):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)  # Timeout for the socket operation
    result = sock.connect_ex((host, port))
    if result == 0:
        res_dict[host] = result
    sock.close()


res_dict = {}

portscan(80, "192.168.1.198", res_dict)

if "192.168.1.198" in res_dict:
    print("True")

print(res_dict)