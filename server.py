"""
Webserver that uses specific congestion control algorithm
"""

import argparse
import socketserver
import http.server
import socket


class Handler(http.server.SimpleHTTPRequestHandler):
    # Disable logging DNS lookups
    def address_string(self):
        return str(self.client_address[0])


def start_server(port: int, cc: str):
    httpd = socketserver.TCPServer(("", port), Handler, bind_and_activate=True)
    # we set the congestion control by hand before bind and active
    cc_buffer = cc.encode("ascii")
    # notice that socket.TCP_CONGESTION is only available 3.6+
    # also notice that setting socket TCP to congestion requires sudo access
    httpd.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_CONGESTION, cc_buffer)
    httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser("Simple web server with customized congestion control algorithm")
    parser.add_argument("-c", "--congestion-control", choices=["bbr", "cubic"], default="bbr", type=str, dest="cc")
    parser.add_argument("-p", "--port", required=True, type=int, dest="port")
    args = parser.parse_args()

    start_server(args.port, args.cc)


if __name__ == "__main__":
    main()
