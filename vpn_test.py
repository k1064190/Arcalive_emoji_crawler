import os
import re
import time
import subprocess

def VPN(action, vpn_path, myvpn=None):
    valid_actions = ["connect", "disconnect_all"]
    if action not in valid_actions:
        return
    else:
        if myvpn:
            command = f'"{vpn_path}" --command {action} {myvpn}'
        else:
            command = f'"{vpn_path}" --command {action}'
        subprocess.Popen(command, shell=True)

def IPAddress():
    ipconfig = os.popen('ipconfig').read()
    ipv4 = re.findall(r'IPv4.*?(\d+\.\d+\.\d+\.\d+)', ipconfig)
    return ipv4

def WaitUntilVPNConnected():
    s = time.time()
    while len(IPAddress()) == 1:
        time.sleep(3)
        if (time.time() - s) > 15:
            break
    if len(IPAddress()) > 1:
        time.sleep(5)

def WaitUntilVPNDisconnected():
    s = time.time()
    while len(IPAddress()) > 1:
        time.sleep(5)
        if (time.time() - s) > 20:
            break
    if len(IPAddress()) == 1:
        time.sleep(5)


if __name__ == "__main__":
    vpn_path = r"C:\Program Files\OpenVPN\bin\openvpn-gui.exe"
    myvpn_dir = "proton"
    myvpn = os.listdir(myvpn_dir)
    # myvpn = [os.path.join(os.getcwd(), myvpn_dir, vpn) for vpn in myvpn if vpn.endswith(".ovpn")]

    print("myvpn : ", myvpn)
    print("IP Address : ", IPAddress())

    VPN("connect", vpn_path, myvpn[2])
    WaitUntilVPNConnected()

    print("IP Address : ", IPAddress())

    VPN("disconnect_all", vpn_path)
    WaitUntilVPNDisconnected()

    print("IP Address : ", IPAddress())
