# Author:           Philipp Koch <github@philipp-koch.net>
# Title:            Aruba AOS-S 16.08 Rest API v6 DEMO
# Description:      Creates a VLAN on a number of switches and tags it to uplink ports
# Prerequisites:    HTTP oder HTTPs enabled: "web-management [plaintext|ssl]"
#                   REST enabled: "rest-interface"

import json                        # JSON Parser
from requests import Response      # HTTP Calls
import argparse                    # Named Commandline arguments
from common.aossswitch import AOSSSwitch


def create_vlan(switch: AOSSSwitch, vlan_id=0, vlan_name="") -> int:
    """ Creates the VLAN with the given ID and given name. If no ID is given, the lowest free one will be used. Returns that ID

    Parameters
    ----------
    switch : AOSSSwitch
        the switch on which to perform the action on 

    vlan_id: int, optional
        the ID of the VLAN to be created, lowest free ID im empty

    vlan_name : str, optional
        the name of the new VLAN. Needs to be unique to the switch

    Returns
    -------
    int
        the VLAN ID which was created
    """
    api_url = "/vlans"
    # Get all VLANS
    response = switch.api_action(api_url, "GET", "")
    if response.status_code == 200:
        if vlan_id == 0:
            # Search for free VLAN ID
            # For all used VLANs the Index=VLANID will be set to 1
            usedVlans = [0] * 4096
            jsonresponse = response.json()
            for vlan in jsonresponse['vlan_element']:
                # print(vlan['vlan_id'])
                usedVlans[vlan['vlan_id']] = 1
            i = 1
            while usedVlans[i] != 0:
                # print(i)
                i += 1
            vlan_id = i
            #print("Free VLAN ID: ", vlan_id)
        # Create new VLAN
        payload = json = {'vlan_id': vlan_id, 'name': vlan_name}
        response = switch.api_action(api_url, "POST", payload)
        if response.status_code == 201:
            #print("VLAN created with ID and name:", vlan_id, vlan_name)
            return vlan_id
        else:
            print("Error while creating VLAN "+str(vlan_id),
                  response.status_code, response.content)
            return None
    else:
        print("Error while getting VLANs",
              response.status_code, response.content)
        return None


def tag_vlan_to_uplinks(switch: AOSSSwitch, vlan_id: int) -> list:
    """ Taggs the given VLAN ID to any uplink port. Uplinks are seen as ports with MORE than 1 tagged vlan 

    Parameters
    ----------
    switch : AOSSSwitch
        the switch on which to perform the action on 

    vlan_id : int
        the id of the vlan to be tagged to all uplinks

    Returns
    -------
    str[]
        the list of ports to which the vlan was succesfully tagged
    """
    api_url = "/vlans-ports"
    # Get all VLAN-Ports
    response = switch.api_action(api_url, "GET", "")
    if response.status_code == 200:
        # Saves all ports with tagged VLANs and the number of tagged VLANs
        ports_with_tagged_vlans = {}
        jsonresponse = response.json()
        for port in jsonresponse['vlan_port_element']:
            if port["port_mode"] == "POM_TAGGED_STATIC":
                # Set tagged count to 1 if first encounter or increment by 1 if found another time
                if port["port_id"] in ports_with_tagged_vlans:
                    ports_with_tagged_vlans[port["port_id"]] += 1
                else:
                    ports_with_tagged_vlans[port["port_id"]] = 1
        # print(ports_with_tagged_vlans)
        # Saves to which ports the new VLAN was tagged succesfully
        ports_vlan_tagged_to = []
        for port in ports_with_tagged_vlans:
            # Checks which ports have already more than one VLAN tagged. Ports with only one tag are ignored. Probably phones.
            if ports_with_tagged_vlans[port] > 1:
                payload = {'vlan_id': vlan_id, 'port_id': port,
                           'port_mode': 'POM_TAGGED_STATIC'}
                response = switch.api_action(api_url, "POST", payload)
                if response.status_code == 201:
                    #print("Tagged Vlan "+str(vlan_id)+" to port "+port)
                    ports_vlan_tagged_to.append(port)
                else:
                    print("Error while tagging VLAN to port",
                          response.status_code, response.content)
                    return None
        ports_vlan_tagged_to.sort()
        return ports_vlan_tagged_to
    else:
        print("Error while getting VLANs-Ports",
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
    '--vlanID', help='The VLAN ID to create', type=int, default=0, choices=range(0, 4096))
parser.add_argument('--vlanName', help='The VLAN name/description', default="")

args = parser.parse_args()

vlan_id = args.vlanID
vlan_name = args.vlanName

version = "v6"                  # API Version used in URL
switch = AOSSSwitch(args.protocol, args.switch,
                    args.username, args.password, version)


# Creates a VLAN with the lowest free ID and name "Test"
vlan_id = create_vlan(switch, vlan_id, vlan_name)
# Prints the created ID to console
print("Added VLAN with the ID: ", vlan_id)
# Taggs the VLANs to all ports with more than 1 VLAN already tagged
portlist = tag_vlan_to_uplinks(switch, vlan_id)
# Prints to which ports the VLAN was successfully tagged
print("VLAN tagged to the following ports:", portlist)
# Terminates the session
switch.logout()
