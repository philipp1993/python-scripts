# Author:           Philipp Koch <github@philipp-koch.net>
# Title:            Aruba AOS-S 16.08 Rest API v6 DEMO
# Description:      Creates a VLAN on a number of switches and tags it to uplink ports
# Prerequisites:    HTTP oder HTTPs enabled: "web-management [plaintext|ssl]"
#                   REST enabled: "rest-interface"

import json         # JSON Parser
import requests     # HTTP Calls

# Some common to functions to reuse later for all sorts of API Calls


def login(protocol: str, switchadress: str, username: str, password: str) -> str:
    """Logs into the REST API and returns the sessionID cookie used with further commands

    Parameters
    ----------
    protocol : str
        http or https
    switchadress : str
        the ip or dns name of the Aruba Switch
    username : str
        username for the switch with manager privileges
    password : str
        password for the given user

    Returns
    -------
    str
        the sessionID cookie
    """
    api_url = protocol+"://"+switchadress+"/rest/"+version+"/login-sessions"
    credentials = {'userName': username, 'password': password}
    response = requests.post(api_url, json=credentials)
    if response.status_code == 201:
        #print("Login to switch: {} was successful".format(switchadress))
        session = response.json()
        return session['cookie']
    else:
        print("Login to switch failed! HTTP Code:",
              response.status_code, response.content)
        return None


def logout(cookie: str) -> None:
    """Destroys the active session on the switch. This is important since the number of active sessions is limited 

    Parameters
    ----------
    cookie : str
        the sessionID cookie need for authorization 
    """
    api_url = protocol+"://"+switchadress+"/rest/"+version+"/login-sessions"
    headers = {'cookie': cookie}
    response = requests.delete(api_url, headers=headers)
    if response.status_code == 204:
        #print("Logged out!")
        return None
    else:
        print("Logout is not successful", response.status_code, response.content)


def create_vlan(cookie: str, vlan_id=0, vlan_name="") -> int:
    """ Creates the VLAN with the given ID and given name. If no ID is given, the lowest free one will be used. Returns that ID

    Parameters
    ----------
    cookie : str
        the sessionID cookie need for authorization 
    vlan_id: int, optional
        the ID of the VLAN to be created, lowest free ID im empty
    vlan_name : str, optional
        the name of the new VLAN. Needs to be unique to the switch

    Returns
    -------
    int
        the VLAN ID which was created
    """
    api_url = protocol+"://"+switchadress+"/rest/"+version+"/vlans"
    headers = {'cookie': cookie}
    # Get all VLANS
    response = requests.get(api_url, headers=headers)
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
        response = requests.post(api_url, headers=headers, json={
                                 'vlan_id': vlan_id, 'name': vlan_name})
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


def tag_vlan_to_uplinks(cookie: str, vlan_id: int) -> list:
    """ Taggs the given VLAN ID to any uplink port. Uplinks are seen as ports with MORE than 1 tagged vlan 

    Parameters
    ----------
    cookie : str
        the sessionID cookie need for authorization 
    vlan_id : int
        the id of the vlan to be tagged to all uplinks

    Returns
    -------
    str[]
        the list of ports to which the vlan was succesfully tagged
    """
    api_url = protocol+"://"+switchadress+"/rest/"+version+"/vlans-ports"
    headers = {'cookie': cookie}
    # Get all VLAN-Ports
    response = requests.get(api_url, headers=headers)
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
                response = requests.post(api_url, headers=headers, json={
                                         'vlan_id': vlan_id, 'port_id': port, 'port_mode': 'POM_TAGGED_STATIC'})
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


# Example
# The following code runs on a single switch. You should add a loop of some sort here to itterate over all your switches.

switchadress = "10.76.135.162"  # IP or DNS Name
username = "manager"            # Username with "manager" rights
password = "Aruba123!"          # password
protocol = "http"               # http oder https
version = "v6"                  # API Version used in URL

# Login and save session cookie
cookie = login(protocol, switchadress, username, password)
# Print session cookie to console
print(cookie)
# Creates a VLAN with the lowest free ID and name "Test"
vlan_id = create_vlan(cookie, 0, "Test")
# Prints the created ID to console
print("Added VLAN with the ID: ", vlan_id)
# Taggs the VLANs to all ports with more than 1 VLAN already tagged
portlist = tag_vlan_to_uplinks(cookie, vlan_id)
# Prints to which ports the VLAN was successfully tagged
print("VLAN auf folgende Ports getagged:", portlist)
# Terminates the session
logout(cookie)
