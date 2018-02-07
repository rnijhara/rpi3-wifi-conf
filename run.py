#!/usr/bin/env python

import os
from bluetooth import *
from wifi import Cell, Scheme
import subprocess
import time




wpa_supplicant_conf = "/etc/wpa_supplicant/wpa_supplicant.conf"
sudo_mode = "sudo "


def wifi_connect(ssid, psk):
    # write wifi config to file
    cmd = 'wpa_passphrase {ssid} {psk} | sudo tee -a {conf} > /dev/null'.format(
            ssid=str(ssid).replace('!', '\!'),
            psk=str(psk).replace('!', '\!'),
            conf=wpa_supplicant_conf
        )
    cmd_result = ""
    cmd_result = os.system(cmd)
    print cmd + " - " + str(cmd_result)

    # reconfigure wifi
    cmd = sudo_mode + 'wpa_cli -i wlan0 reconfigure'
    cmd_result = os.system(cmd)
    print cmd + " - " + str(cmd_result)

    time.sleep(10)

    cmd = 'iwconfig wlan0'
    cmd_result = os.system(cmd)
    print cmd + " - " + str(cmd_result)

    cmd = 'ifconfig wlan0'
    cmd_result = os.system(cmd)
    print cmd + " - " + str(cmd_result)

    p = subprocess.Popen(['hostname', '-I'], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    out, err = p.communicate()

    if out:
        ip_address = out
    else:
        ip_address = "<Not Set>"

    return ip_address



def ssid_discovered():
    Cells = Cell.all('wlan0')

    wifi_info = 'Found ssid : \n'

    for current in range(len(Cells)):
        wifi_info +=  Cells[current].ssid + "\n"


    wifi_info+="!"

    print wifi_info
    return wifi_info


def handle_client(client_sock) :
    # get ssid
    client_sock.send(ssid_discovered())
    print "Waiting for SSID..."


    ssid = client_sock.recv(1024)
    if ssid == '' :
        return

    print "ssid received"
    print ssid

    # get psk
    client_sock.send("waiting-psk!")
    print "Waiting for PSK..."


    psk = client_sock.recv(1024)
    if psk == '' :
        return

    print "psk received"

    print psk

    ip_address = wifi_connect(ssid, psk)

    print "ip address: " + ip_address

    client_sock.send("ip-address:" + ip_address + "!")

    return



try:
    while True:
        server_sock=BluetoothSocket( RFCOMM )
        server_sock.bind(("",PORT_ANY))
        server_sock.listen(1)

        port = server_sock.getsockname()[1]

        uuid = "815425a5-bfac-47bf-9321-c5ff980b5e11"

        advertise_service( server_sock, "RPi Wifi config",
                           service_id = uuid,
                           service_classes = [ uuid, SERIAL_PORT_CLASS ],
                           profiles = [ SERIAL_PORT_PROFILE ])


        print "Waiting for connection on RFCOMM channel %d" % port

        client_sock, client_info = server_sock.accept()
        print "Accepted connection from ", client_info

        handle_client(client_sock)

        client_sock.close()
        server_sock.close()

        # finished config
        print 'Finished configuration\n'


except (KeyboardInterrupt, SystemExit):
    print '\nExiting\n'
