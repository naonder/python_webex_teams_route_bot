#!/usr/bin/env python3

import json
import requests
import netmiko
import socket
from orionsdk import SwisClient


class DeviceCheck:
    def __init__(self):
        # URL and address will be up to you - device running RESTConf as well as device to run ping/traceroute from
        with open('/path/to/creds.json') as credentials:
            self.creds = json.load(credentials)
        self.name = self.creds['username']
        self.passwrd = self.creds['password']
        self.base_url = 'https://x.x.x.x/restconf/data/Cisco-IOS-XE-bgp-oper:bgp-state-data/bgp-route-vrfs/' \
                        'bgp-route-vrf=default/bgp-route-afs/bgp-route-af=ipv4-unicast/bgp-route-filters/' \
                        'bgp-route-filter=bgp-rf-all/bgp-route-entries/bgp-route-entry'
        self.device_address = 'x.x.x.x'
        self.ios = 'cisco_ios'

    def route_check(self, host):
        address = socket.gethostbyname(host)
        requests.packages.urllib3.disable_warnings()
        headers = {'Content-Type': 'application/json', 'Accept': 'application/yang-data+json'}
        url = '{}={}'.format(self.base_url, address)
        response = requests.get(url, auth=(self.name, self.passwrd), headers=headers, verify=False)
        print(response.status_code)
        if response.status_code != 404:
            return response.json()
        else:
            return '404'

    def icmp(self, address):
        connection = netmiko.ConnectHandler(username=self.name, password=self.passwrd,
                                            device_type=self.ios, ip=self.device_address)
        result = connection.send_command('ping {} timeout 1'.format(address))
        connection.disconnect()
        return result

    def traceroute(self, address):
        connection = netmiko.ConnectHandler(username=self.name, password=self.passwrd,
                                            device_type=self.ios, ip=self.device_address)
        result = connection.send_command('traceroute {} timeout 1 ttl 1 15 probe 2'.format(address))
        connection.disconnect()
        return result

    def icmp_traceroute(self, address):
        connection = netmiko.ConnectHandler(username=self.name, password=self.passwrd,
                                            device_type=self.ios, ip=self.device_address)
        ping = connection.send_command('ping {} timeout 1'.format(address))
        print(ping)
        traceroute = connection.send_command('traceroute {} timeout 1 ttl 1 15 probe 2'.format(address))
        print(traceroute)
        connection.disconnect()
        return ping, traceroute


class SwQuery:
    def __init__(self):
        with open('/path/to/creds.json') as credentials:
            self.creds = json.load(credentials)
        self.npm_server = 'x.x.x.x'  # Your server that's running Solarwinds
        self.username = self.creds['sw_username']
        self.password = self.creds['sw_password']
        requests.packages.urllib3.disable_warnings()
        self.swis = SwisClient(self.npm_server, self.username, self.password)

    def device_query(self):
        # Query for down routers and switches
        device_query = '''Your query here'''

        results = self.swis.query(device_query)

        return results


# Just for testing purposes
if __name__ == '__main__':
    query = SwQuery()
    down_devices = query.device_query()
    if down_devices['results']:
        devices = []
        for row in down_devices['results']:
            devices.append(row['Caption'])
        print(devices)
    else:
        print('no devices')
