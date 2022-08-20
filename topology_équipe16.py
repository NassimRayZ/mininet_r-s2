#!/usr/bin/python
"""
cette topologie exploite l'api mininet python
La topologie crée deux routeur et cinq sous-réseaux IP :
    - 10.16.0.0/24 (r1-eth0, IP : 10.16.0.1)
    - 10.16.1.0/24 (r1-eth1, IP : 10.16.1.1)
    - 10.16.2.0/24 (r2-eth0, IP : 10.16.2.1)
    - 10.16.3.0/24 (r2-eth1, IP : 10.16.3.1)
    - 10.16.100.0/24 (r1-eth2, IP : 10.16.100.1; r2-eth2, IP : 10.16.100.2)
Chaque sous-réseau est composé d'un seul hôte connecté à un routeur.


La topologie s'appuie sur les entrées de routage par défaut qui sont
automatiquement créées pour chaque interface de routeur, ainsi que des
ainsi que les paramètres 'defaultRoute' pour les interfaces hôtes.


Des routes supplémentaires peuvent être ajoutées au routeur ou aux hôtes en
en exécutant les commandes 'ip route' ou 'route' sur le routeur ou les hôtes.


On peut aussi modifier les addresse IP à l'aide des commandes 'ip address' ou
'ifconfig'
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink


# La classe de routeur utilisée
class LinuxRouter(Node):

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class NetworkTopo(Topo):

    def build(self, **_opts):
        # La création des routeurs à l'aide de la méthode 'addNode()'

        r1 = self.addNode("r1", cls=LinuxRouter, ip=None)
        r2 = self.addNode("r2", cls=LinuxRouter, ip=None)

        # La méthode 'addLink()' gère les liens entre les machines

        self.addLink(
            r1,
            r2,
            intfName1="r1-eth2",
            intfName2="r2-eth2",
            params1={"ip": "10.16.100.1/30"},
            params2={"ip": "10.16.100.2/30"},
        )

        # La création des hôtes à l'aide de la méthode 'addHost()'

        h1 = self.addHost(name="h1",
                          ip="10.16.0.2/24",
                          defaultRoute="via 10.16.0.1")
        h2 = self.addHost(name="h2",
                          ip="10.16.1.2/24",
                          defaultRoute="via 10.16.1.1")
        h3 = self.addHost(name="h3",
                          ip="10.16.2.2/24",
                          defaultRoute="via 10.16.2.1")
        h4 = self.addHost(name="h4",
                          ip="10.16.3.2/24",
                          defaultRoute="via 10.16.3.1")

        # La méthode 'addLink()' gère les liens entre les machines

        self.addLink(h1,
                     r1,
                     intfName2="r1-eth0",
                     params2={"ip": "10.16.0.1/24"})

        self.addLink(h2,
                     r1,
                     intfName2="r1-eth1",
                     params2={"ip": "10.16.1.1/24"})
        self.addLink(h3,
                     r2,
                     intfName2="r2-eth0",
                     params2={"ip": "10.16.2.1/24"})
        self.addLink(h4,
                     r2,
                     intfName2="r2-eth1",
                     params2={"ip": "10.16.3.1/24"})


def run():

    #on lance la topologie mininet

    topo = NetworkTopo()
    net = Mininet(topo=topo)
    net.start()

    # Ajouter le routage statique pour atteindre des réseaux qui ne sont pas directement connectés.
    # L'utilisation de la commande "ip route add net-id via @prochaine-saut dev interface"

    info(
        net['r1'].cmd("ip route add 10.16.2.0/24 via 10.16.100.2 dev r1-eth2"))
    info(
        net['r1'].cmd("ip route add 10.16.3.0/24 via 10.16.100.2 dev r1-eth2"))
    info(
        net['r2'].cmd("ip route add 10.16.0.0/24 via 10.16.100.1 dev r2-eth2"))
    info(
        net['r2'].cmd("ip route add 10.16.1.0/24 via 10.16.100.1 dev r2-eth2"))

    # Pour chaque interface de chaque machine dans la topologie
    # on utilise la commande "tc" pour fixer les débit des liens
    # à 10Gbps (DF)

    for i in range(4):
        info(net[f'h{i+1}'].cmd(
            f"tc qdisc add dev h{i+1}-eth0 root netem  rate 10gbit "))
    for i in range(6):
        info(net[f'r{i%2+1}'].cmd(
            f"tc qdisc add dev r{i%2+1}-eth{i%3} root netem rate 10gbit "))
    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
