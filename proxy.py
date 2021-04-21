import ssl
import socket
import logging
import binascii
import threading

from argparse import ArgumentParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_dns_tls_server(dns, ca_path):
    # according to: https://tools.ietf.org/html/rfc7858

    # opening socket stream connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(100)

    # creating ssl default context and certificate validation
    ctx = ssl.create_default_context()
    ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = True
    ctx.load_verify_locations(ca_path)                            

    # connecting to dns tls cloudflare server
    wrapped_socket = ctx.wrap_socket(sock, server_hostname=dns)
    wrapped_socket.connect((dns, 853))

    logger.info("Server Peer Certificate: %s", str(wrapped_socket.getpeercert()))
    return wrapped_socket

def send_message(wrapped_socket, data): 

    # making complete tcp packet to send to the dns tls server

    # according to: https://tools.ietf.org/html/rfc1035#section-4.2.2
    
    tcp_msg = "\x00".encode() + chr(len(data)).encode() + data
    logger.info("TCP Packet to be Send to DNS-TLS Server: %s", str(tcp_msg))

    # sending the tcp packet
    wrapped_socket.send(tcp_msg)
    response = wrapped_socket.recv(1024)

    return response

def extract_result(response):

    # extracting and decoding response to get the rcode
    rcode = binascii.hexlify(response[:6]).decode("utf-8")
    rcode = rcode[11:] 

    # according to: https://tools.ietf.org/html/rfc6895#section-2.3
    
    if int(rcode, 16) == 1:
        logger.error("Error Processing the Request, RCODE = %s", rcode)
    else:
        logger.info("Proxy OK, RCODE = %s", rcode)
        result = response[2:]
        return result

def resolve(sock, data, address, dns, ca_path):

    # to establish the connection to dns tls server
    wrapped_socket = connect_dns_tls_server(dns, ca_path)

    # to send the message to dns tls server
    logger.info("Data Packet: %s", str(data))
    response = send_message(wrapped_socket, data)
    
    # if response in not null, sending result back to the client
    if response:
        logger.info("DNS-TLS Server Response: %s", str(response))
        result = extract_result(response)
        sock.sendto(result, address)
    else:
        logger.warn("Empty reply from server")

def main():

    # parsing different arguments
    parser = ArgumentParser(description="DNS-OVER-TLS Proxy")
    parser.add_argument(
        "-p",
        "--port",
        help="Port of the listening proxy [default: 53]",
        type=int,
        default=53,
        required=False,
    )
    parser.add_argument(
        "-a",
        "--address",
        help="Address of the proxy network interface to use [default: 0.0.0.0]",
        type=str,
        default="0.0.0.0",
        required=False,
    )
    parser.add_argument(
        "-d",
        "--dns",
        help="Domain name server with TLS support [default: 1.1.1.1]",
        type=str,
        default="1.1.1.1",
        required=False,
    )
    parser.add_argument(
        "-c",
        "--ca",
        help="Path to the root and intermediate certificates file [default: /etc/ssl/cert.pem]",
        type=str,
        default="/etc/ssl/cert.pem",
        required=False,
    )

    # storing parsed arguments in variables
    args = parser.parse_args()
    port = args.port
    host = args.address
    dns = args.dns
    ca_path = args.ca

    try:
        # binding datagram socket to specified host and port
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((host, port))
        
        # waiting for client to send the data (dns query)
        while True:
            data, address = sock.recvfrom(4096)

            # as soon as receieved data, starting thread to process the dns query
            threading.Thread(
                target=resolve, args=(sock, data, address, dns, ca_path)
            ).start()

    except Exception as e:
        logger.error(e)
    finally:
        sock.close()

if __name__ == "__main__":
    main()
