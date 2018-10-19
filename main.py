#!/usr/bin/env python3

import requests.packages.urllib3
from flask import Flask
from flask import request
import requests
import json
import route_get

requests.packages.urllib3.disable_warnings()

app = Flask(__name__)

# Set some basic variables to use for the app itself
bot_email = 'yourbot@webex.bot'  # Email for your bot
access_token = 'Your access token here'
base_url = 'https://api.ciscospark.com/v1/'
server = 'x.x.x.x'  # Server that's running the bot
port = 10010
headers = {"Authorization": "Bearer {}".format(access_token), "Content-Type": "application/json"}


# Main function that's used to grab messages and get data from a router
@app.route('/', methods=['POST'])
def index():
    # Grab message and room ID to use to reply to as bot can be used in any room it's added to
    message_id = request.json.get('data').get('id')
    room_id = request.json.get('data').get('roomId')
    msg_details = requests.get(base_url+"messages/"+message_id, headers=headers)

    # Grab the text and originating email from the message itself
    message, email = get_message(msg_details)

    # Check that bot isn't the original sender of the message and that only internal users can query devices
    if email == bot_email:
        return ''

    if 'example.com' in email:  # Check to make sure only registered users can invoke the bot

        # If message is none, send 'help' info, otherwise, complete task as requested

        if '/help' in message:
            return_info = get_help()

        elif '/route' in message:
            return_info = get_route_info(message)

        elif '/ping' in message:
            return_info = ping(message)

        elif '/traceroute' in message:
            return_info = traceroute(message)

        elif '/downdevices' in message:
            return_info = sw_query()

        elif '/tshoot' in message:
            send_to_teams('Troubleshooting might take a while, stand by...\r\n', room_id)
            return_info = troubleshoot(message)

        else:
            return_info = get_help()

        send_to_teams(return_info, room_id)
    return ''


# Send the reply message from the bot back into the room the query was sent from
def send_to_teams(message, room_id):
    payload = {"roomId": room_id, "text": message}
    return requests.post("https://api.ciscospark.com/v1/messages/", data=json.dumps(payload),
                                    headers=headers)


# Try to get text from the sender's message as well as their email
def get_message(response):
    senders_message = response.json().get('text')
    senders_email = response.json().get('personEmail')
    return senders_message, senders_email


# Process route info from input
def get_route_info(address):
    add_check = route_get.DeviceCheck()
    if address.split(' ')[-1] != ' ':
        real_address = address.split(' ')[-1]
        result = add_check.route_check(real_address)
        if result is not '404':
            try:
                base = result["Cisco-IOS-XE-bgp-oper:bgp-route-entry"]["bgp-path-entries"]["bgp-path-entry"][0]
                prefix = result["Cisco-IOS-XE-bgp-oper:bgp-route-entry"]['prefix']
                if 'xxxx' in base['as-path'] or 'xxxx' in base['as-path']:  # Just checking if route is external
                    result = ('\r\nBGP information for {}:'
                              '\r\n'
                              '\r\nNext hop: {}'
                              '\r\nMetric: {}'
                              '\r\nLocal pref: {}'
                              '\r\nAS path: {}'
                              '\r\nOrigin: {}'
                              '\r\nNOTE: Prefix/Route is external to xxxx'  # External checking is optional
                              .format(prefix, base["nexthop"], base["metric"], base["local-pref"],
                                      base["as-path"], base["origin"]))
                else:
                    result = ('\r\nBGP information for {}:'
                                 '\r\n'
                                 '\r\nNext hop: {}'
                                 '\r\nMetric: {}'
                                 '\r\nLocal pref: {}'
                                 '\r\nAS path: {}'
                                 '\r\nOrigin: {}'
                                 .format(prefix, base["nexthop"], base["metric"], base["local-pref"],
                                         base["as-path"], base["origin"]))

            # If malformed address or wrong input, getting route info will fail
            except TypeError:
                result = 'Error fetching data, try again'

        # If you /route and leave a space with no info, should get 404
        else:
            result = 'Input an IPv4 address to check for route information'

    return result


# Uses Netmiko to log into the 'route server' to run a ping against an address. Timeout is set to 1 second
def ping(address):
    ping_check = route_get.DeviceCheck()
    if address.split(' ')[-1] != ' ':
        real_address = address.split(' ')[-1]
        result = ping_check.icmp(real_address)
        return result


# Uses Netmiko to log into the 'route server' and run a traceroute to an address. Uses 1 second timeout and 15 hops max
def traceroute(address):
    trace_check = route_get.DeviceCheck()
    if address.split(' ')[-1] != ' ':
        real_address = address.split(' ')[-1]
        result = trace_check.traceroute(real_address)
        return result


def troubleshoot(address):
    tshoots = route_get.DeviceCheck()
    if address.split(' ')[-1] != ' ':
        real_address = address.split(' ')[-1]
        pings, traceroutes = tshoots.icmp_traceroute(real_address)
        return_message = [get_route_info(address), '\r\nPing results:', pings,
                          '\r\nTraceroute results:', traceroutes]

        return '\r\n'.join(return_message)


# Makes an API call to Solarwinds for only network devices that are down (switches, routers, WLCs, and firewalls)
def sw_query():
    query = route_get.SwQuery()
    down_devices = query.device_query()
    if down_devices['results']:
        devices = []
        for row in down_devices['results']:
            devices.append(row['Caption'])
        return '\r\n'.join(devices)
    else:
        return 'No down devices'


def get_help():
    message = ('Current options are:'
               '\r\n/help - lists commands possible'
               '\r\n/route - lists BGP route information for a specific address'
               '\r\n/ping - attempt to ping the specified address (may take a while to complete)'
               '\r\n/traceroute - attempt to traceroute to the specified address (may take a while to complete)'
               '\r\n/downdevices - view a list of current down devices in Solarwinds'
               '\r\n/tshoot - attempt to do basic troubleshooting on a device (may take a long while to complete)')
    return message


if __name__ == "__main__":
    app.run(host=server, port=port, debug=True)
