#!/usr/bin/env python
#  coding: utf-8 
from datetime import time
import socketserver
import os
from urllib.parse import unquote
from email.utils import formatdate

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

#   Copyright 2021 Danila Seliayeu
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

class MyWebServer(socketserver.BaseRequestHandler):
    
    def __init__(self, request, client_address, server):
        self.base = os.path.realpath("./www")
        super().__init__(request, client_address, server)

    def handle(self):
        # make sure there is data -- return if not
        self.data = self.request.recv(1024).decode("utf-8")
        if (not self.data or len(self.data) < 4): return

        # assume properly formatted
        while self.data[-4:] != "\r\n\r\n":
            self.data += self.request.recv(1024).decode("utf-8")

        # get relevant information and alert to stdout that there was connection
        print("Got request:", self.data)
        statusLine = "\n".join(self.data.split("\n")[:1])
        method, path, protocol = statusLine.split(" ")
        path = unquote(path)

        # make sure method is legal
        if (method == "POST" or method == "PUT" or method == "DELETE"): 
            self.request.sendall(bytearray("HTTP/1.1 405 Method Not Allowed\r\n\r\n", "utf-8"))
            return

        # redirect if wacky path
        if (os.path.isdir(self.base + path) and path[-1] != "/"):
            self.redirect(path)
            return

        # check for security before sending files
        if (self.isValidPath(path) and os.path.isfile((self.base + path))):
            self.servefile(self.base + path, path.split(".")[-1])
        elif (self.isValidPath(path) and os.path.isfile(self.base + path + "index.html")):
            self.servefile(self.base + path + "index.html", "html")
        else:
            self.request.sendall(bytearray("HTTP/1.1 404 File Not Found\r\n\r\n", "utf-8"))
        return

    def isValidPath(self, path):
        # make sure the path is at least as long as the currentpath
        if len(str(os.path.abspath(self.base + path))) < len(str(self.base)):
            return False
        # make sure base directories are matching
        if str(os.path.abspath(self.base + path))[0:len(str(self.base))] != str(self.base):
            return False
        return True
        
    def getMimeType(self, extension):
        if extension == "html" or extension == "css":
            return "text/" + extension
        return "application/octet-stream"

    def servefile(self, filename, type):
        print("Serving " + filename)
        with open(filename) as f:
            size = os.path.getsize(filename)
            response = "HTTP/1.1 200 OK\r\nContent-Type: " + self.getMimeType(type)  + ";charset=UTF-8\r\n"
            response += "Content-Length: " + str(size) + "\r\n"
            # the following line of code is modified from the line written in https://stackoverflow.com/a/225177 by user Ber
            # to remove a print statement and concatenate "Date: " and "\r\n". this code is licences under CC BY-CA 2.5 which
            # can be found here https://creativecommons.org/licenses/by-sa/2.5/
            response += "Date: " + formatdate(timeval=None, localtime=False, usegmt=True) + "\r\n"
            response += "Connection: close\r\n"
            response += "\r\n"
            print(response)
            self.request.sendall(bytearray(response, "utf-8"))
            data = f.read(size)
            self.request.sendall(bytearray(data, "utf-8"))

    def redirect(self, path):
        # redirect with a 301
        print("\nRedirecting...")
        self.request.sendall(bytearray("HTTP/1.1 301 Moved Permanently\r\nLocation: http://" + HOST + ":" + str(PORT) + path + "/\r\n\r\n", "utf-8"))

if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", 8080
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((HOST, PORT), MyWebServer) as server:
        server.serve_forever()
