import re

x = """[
    {
        "addr": "103.229.122.253",
        "services": 'x',
        "email":"siva.m@gmail.com"
        "lastsend": 1578797285,
        "lastrecv": 1578797285,
        "conntime": 1577841460,
    },
    {
        "addr": "22.23.222.147",
        "services": 'y',
        "lastsend": 1578797395,
        "lastrecv": 1578797395,
        "conntime": 1577841462,
    },
    {
        "addr": "ab.xy",
        "services": 'z',
        "lastsend": 1578797381,
        "lastrecv": 1578797381,
        "conntime": 1577936686,
        "banscore": 0
    }
]"""



ips = re.findall(r'[0-9]{1,3}+\.[0-9]{1,3}+\.[0-9]{1,3}+\.[0-9]{1,3}+', x)
print(ips)


email_addresses = re.findall(r'[A-Za-z0-9.]+\@[a-zA-Z0-9]+\.[A-Za-z0-9]{1,5}+', x)
print(email_addresses)