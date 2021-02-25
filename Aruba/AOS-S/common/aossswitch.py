# Author:           Philipp Koch <github@philipp-koch.net>
# Title:            Aruba AOS-S Rest API Switch Class
# Description:      This is a helper class for using with the AOS-S rest API.
#                   This class represents the switch and gives you easy function for
#                   login, logout, and calling an API endpoint.
import json         # JSON Parser
import requests     # HTTP Calls
from requests.adapters import HTTPAdapter
import time

import logging
logging.basicConfig(level=logging.DEBUG)


class AOSSSwitch:
    def __init__(self, protocol: str, switchadress: str, username: str, password: str, version: str):
        """Logs into the REST API

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

        version : str
            API schema version

        Returns
        -------
        None
        """
        self.base_url = protocol+"://"+switchadress+"/rest/"+version
        api_url = self.base_url+"/login-sessions"
        credentials = {'userName': username, 'password': password}
        # print(json.dumps(credentials))
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=1,
                              pool_maxsize=0, max_retries=2, pool_block=False)
        self.session.mount(api_url, adapter)
        time.sleep(0.25)
        response = self.session.post(api_url, json=credentials, timeout=5)
        if response.status_code == 201:
            #print("Login to switch: {} was successful".format(switchadress))
            time.sleep(0.25)
            return
        else:
            raise ConnectionError("Login to switch failed! HTTP Code: " +
                                  str(response.status_code) + " " + response.content)

    def logout(self) -> None:
        """Destroys the active session on the switch. This is important since the number of active sessions is limited 
        """
        api_url = self.base_url+"/login-sessions"
        time.sleep(0.25)
        response = self.session.delete(api_url, timeout=5)
        if response.status_code == 204:
            self.session.close()
            return
            #print("Logged out!")
        else:
            self.session.close()
            raise ConnectionError("Logout was not successful " +
                                  response.status_code + " " + response.content)

    def api_action(self, url: str, method: str, payload: str) -> requests.Response:
        """ Gets the PoE enabled status of a given port

        Parameters
        ----------
        url : str
            the relative URL to the API call 

        method: str
            the HTTP Method to use: GET, PUT, POST, DELETE

        payload: str
            the JSON payload data passed to the API call


        Returns
        -------
        response
            returns the API call response. Parse with response.json()
        """
        # API gets unstable on a 2530 switch I used for testing
        time.sleep(0.5)
        api_url = self.base_url+url
        if method == "GET":
            return self.session.get(api_url, json=payload, timeout=5)
        if method == "PUT":
            return self.session.put(api_url, json=payload, timeout=5)
        if method == "POST":
            return self.session.post(api_url, json=payload, timeout=5)
        if method == "DELETE":
            return self.session.delete(api_url, json=payload, timeout=5)
