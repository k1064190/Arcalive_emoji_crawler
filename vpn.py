import os
import re
import subprocess
import time


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
        time.sleep(5)
        if (time.time() - s) > 20:
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

def checkVPNConnected():
    if len(IPAddress()) > 1:
        return True
    return False
