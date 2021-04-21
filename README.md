# DNS-OVER-TLS Proxy

Simple proxy that captures plain text DNS requests from the host, redirects the query over an ecrypted channel to a DNS server that supports TLS, and replies back to the client with the answer.

## Getting Started

This project is to design and develop a DNS proxy. A DNS proxy is a DNS forwarder that acts as a DNS resolver for client programs but requires an upstream DNS server, Cloudflare DNS server is used in this project as upstream DNS server, to perform the DNS lookup. The proxy receives queries from the clients and forward it to the cloudflare DNS server for the results.

## Design Choices and Implementation

As, the default port/protocol for DNS queries is 53/UDP, the application binds a datagram type socket to the host. This port could be changed to a different one if desired (see [Usage](#usage)). Upon receiving a query, the program starts a new thread to process it. It then begins to wrap a new TCP socket using SSL and verify the certificate over port 853. The full message is formatted and sent to the server over the encrypted connection. When it gets the reply, it checks the answer for errors specifically on the RCODE bits. If the query was successful, forwards back the result to the client minus the first 2 bits. The application can run both as a standalone script or a Docker container.

## Query Flow Diagram

                           
                            ___________________
      ______________       |  ______    _____  |        _______________ 
     |              |      | |DNS   |  |TLS  | |       |  Cloudflare   | 
     |   Clients    |----->| |Server|..|Tran | |-----> |DNS (TLS)- 853 |
     |______________|      | |_(53)_|  |sport| |       |_______________|
                           |___________________|
                           

## Usage

If instead of using the default port 53, you want to have the proxy on a different port, use the -p flag. The same applies if you want to use a different CA bundle through the -c flag. You can use the default DNS, or use any other server that supports TLS by passing the -d flag.

**You can look for different available options by typing:**

```
  ./proxy --help
```

## Local Setup

The program uses built-in Python libraries and can be used directly from a terminal if desired. Just clone the repo and you're all set.

```
  python ./proxy.py
```

## Docker Setup

**It also works as a Docker container**

To run this project:

- Create docker image by using Dockerfile which is in the root directory by run this command:
```
  docker build -t dot-proxy .
```

- Run the container by using the docker image which we created in the previous step by run this command:
```
  docker run --rm -p 53:53/tcp -p 53:53/udp dot-proxy
```

***Note: For making sure that no process is running on the specified port you can do that:***

`
  sudo lsof -i:53
`

## Docker Compose Setup

**With docker compose, you don't need to build image and run the container on your own, compose will do it all for you, here are simple steps to follow:**

- Running a container

```
  docker-compose up 
  
        OR 
  
  docker-compose up --build (if you want to rebuild the images)
```
- Destroying a container

```
  docker-compose down
```

## Ansible Setup

**Ansible can be used to maintain and manage the docker-compose as a service:**

- Running a command

```
  sudo ansible-playbook setup.yml
```

<i>Make sure ansible is installed on your system.</i>

## Testing:

You can test this by making a simple **dig** request
```
  dig @localhost -p 53 google.com
```
You can also watch the logs on the proxy terminal for different debugging purposes.

# Answers to the Asked Questions

### **Security Concerns**

Everything has its pros and cons. Here we are using TLS/TCP to secure our pipelines and send DNS queries over those encrypted pipeline. But there are also some known security concerns with TLS, when browser send request to the DNS proxy server and then proxy server will create TCP connection with Upstream DNS server, man-in-the-middle can spoof traffic between browser and dns server, can add/edit datagram and send it over the TCP connection. 

If this proxy being deployed in an infrastructure such as AWS EC2 Instance then, we have to manage the security of that server as well, that allowing traffic flow in and out to the proxy being deployed on the server.

### **Microservices Architecture**

In Microservices architecture, since different applications doesn't need separate DNS resolvers, this can be deployed as a standalone container to serve all the DNS needs of all the containers in the cluster. Multiple instances can be made available for redundancy and therefore high availability.

If we consider AWS Cloud, then we can deploy and integrate this proxy in a distributed environment using AWS ECS Fargate Service and Task Defination, through which we can also achieve auto-scaling for the deployed proxy while distributing load via load balancer.

### **Improvements**

There are alot more things that we can add in this project:
* Can reduce overhead of TLS connection and the handshake process again and again on each request, by checking the client address. Application should have to maintain the socket connections for the specific time period.
* We can also add other available DNS-OVER-TLS Servers like Quad9 and Cleanbrowsing.
* Block IP, if dns server is getting too much requests from the same IP in the specific time period.

Regarding other improvements, Terraform can be used for the provisioning of infrastructure and Ansible can be used for the configuration of the application (proxy).