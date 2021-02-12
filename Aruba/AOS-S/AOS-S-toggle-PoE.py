# Author:           Philipp Koch <github@philipp-koch.net>
# Title:            Aruba AOS-S Rest API PoE toggle
# Description:      Toggles a Switch Ports PoE Status
# Prerequisites:    HTTP oder HTTPs enabled: "web-management [plaintext|ssl]"
#                   REST enabled: "rest-interface"

import json                     # JSON Parser
from requests import Response   # HTTP Calls
import argparse                 # Named Commandline arguments
from common.aossswitch import AOSSSwitch

# Some common to functions to reuse later for all sorts of API Calls


def get_poe_enabled(switch: AOSSSwitch, port: str) -> bool:
    """ Gets the PoE enabled status of a given port

    Parameters
    ----------
    switch : AOSSSwitch
        the switch on which to perform the action on 

    port: str
        The port for which to retrieve the status


    Returns
    -------
    bool
        PoE enabled or not
    """
    response = switch.api_action("/ports/"+port+"/poe", "GET", "")
    if response.status_code == 200:
        json_response = response.json()
        return json_response['is_poe_enabled']
    else:
        print("Error while getting port PoE infos",
              response.status_code, response.content)
        return None


def set_poe_enabled(switch: AOSSSwitch, port: str, action: bool) -> bool:
    """ Gets the PoE enabled status of a given port

    Parameters
    ----------
    cookie : str
        the sessionID cookie need for authorization 

    port: str
        The port for which to set the status

    action: bool
        The desired is poe enabled value


    Returns
    -------
    bool
        PoE enabled or not
    """
    response = switch.api_action("/ports/"+port+"/poe", "PUT", {
        'is_poe_enabled': action})
    if response.status_code == 200:
        return action
    else:
        print("Error while setting PoE enabled on Port " + port,
              response.status_code, response.content)
        return None


parser = argparse.ArgumentParser(
    description="Change the PoE status on a given AOS-S Switch on a given port")

parser.add_argument(
    '--switch', help='IP or DNS  of the switch', required=True)
parser.add_argument('--username', help='Loginuser', default="manager")
parser.add_argument('--password', help='Password for the user', required=True)
parser.add_argument('--protocol', help='HTTP or HTTP',
                    choices=['http', 'https'], default="http")
parser.add_argument(
    '--port', help='The swichtport to change the PoE state of', required=True)
parser.add_argument('--action', choices=['on', 'off', 'toggle'],
                    help='What to do with the PoE state of the port', default="toggle")

args = parser.parse_args()

port = args.port
action = args.action

version = "v6"                  # API Version used in URL
switch = AOSSSwitch(args.protocol, args.switch,
                    args.username, args.password, version)


# Decide what to do
if action == 'toggle':
    current_poe_enabled = get_poe_enabled(switch, port)
    desired_poe_enabled = not current_poe_enabled
if action == 'on':
    desired_poe_enabled = True
if action == 'off':
    desired_poe_enabled = False

# Change the PoE enabled value
set_poe_enabled(switch, port, desired_poe_enabled)

# Terminates the session
switch.logout()
