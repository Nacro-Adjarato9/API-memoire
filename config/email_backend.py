"""Backend SMTP qui force la resolution DNS en IPv4.

Certains hebergeurs (dont Render) ont un support IPv6 sortant incomplet :
smtplib resout smtp.gmail.com en IPv6 en priorite et la connexion echoue avec
'[Errno 101] Network is unreachable', alors que la meme adresse en IPv4
fonctionne. On force donc explicitement IPv4 pour cette connexion SMTP
uniquement (pas d'impact sur le reste de l'application).
"""
import smtplib
import socket

from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend


class IPv4SMTP(smtplib.SMTP):
    def _get_socket(self, host, port, timeout):
        if timeout is not None and not timeout:
            raise ValueError("Non-blocking socket (timeout=0) is not supported")
        addr_info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        family, socktype, proto, _, sockaddr = addr_info[0]
        sock = socket.socket(family, socktype, proto)
        if timeout is not None:
            sock.settimeout(timeout)
        sock.connect(sockaddr)
        return sock


class IPv4SMTP_SSL(smtplib.SMTP_SSL):
    def _get_socket(self, host, port, timeout):
        if timeout is not None and not timeout:
            raise ValueError("Non-blocking socket (timeout=0) is not supported")
        addr_info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        family, socktype, proto, _, sockaddr = addr_info[0]
        sock = socket.socket(family, socktype, proto)
        if timeout is not None:
            sock.settimeout(timeout)
        sock.connect(sockaddr)
        return self.context.wrap_socket(sock, server_hostname=host)


class EmailBackend(DjangoSMTPBackend):
    @property
    def connection_class(self):
        return IPv4SMTP_SSL if self.use_ssl else IPv4SMTP
