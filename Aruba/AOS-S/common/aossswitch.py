# Author:           Philipp Koch <github@philipp-koch.net>
# Title:            Aruba AOS-S Rest API Switch Class
# Description:      This is a helper class for using with the AOS-S rest API.
#                   This class represents the switch and gives you easy function for
#                   login, logout, and calling an API endpoint.
import json         # JSON Parser
import requests     # HTTP Calls
import time


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
        #print(json.dumps(credentials))
        self.session = requests.Session()
        response = self.session.post(api_url, json=credentials)
        if response.status_code == 201:
            #print("Login to switch: {} was successful".format(switchadress))
            time.sleep(0.5)
            return
        else:
            raise ConnectionError("Login to switch failed! HTTP Code: "+
                  response.status_code + " " + response.content)

    def logout(self) -> None:
        """Destroys the active session on the switch. This is important since the number of active sessions is limited 
        """
        api_url = self.base_url+"/login-sessions"
        time.sleep(0.5)
        response = self.session.delete(api_url)
        if response.status_code == 204:
            del self.session
            return
            #print("Logged out!")
        else:
            raise ConnectionError("Logout was not successful "+
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
            return self.session.get(api_url, json=payload)
        if method == "PUT":
            return self.session.put(api_url, json=payload)
        if method == "POST":
            return self.session.post(api_url, json=payload)
        if method == "DELETE":
            return self.session.delete(api_url, json=payload)
