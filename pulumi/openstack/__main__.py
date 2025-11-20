"""Un projet Pulumi pour déployer une infrastructure web simple sur OpenStack."""

import pulumi
import pulumi_openstack as openstack
import pandas as pd
import os
from vm_component import OpenStackVmComponent # Import du composant

# --- Fonctions Utilitaires (Réutilisation de la fonction AWS) ---
def get_vms_config(cloud_name: str) -> list:
    """Lit le CSV et filtre les VMs pour le cloud spécifié."""
    # Le chemin est relatif au répertoire racine du projet (où se trouve vms.csv)
    csv_path = os.path.join(os.getcwd(), "..", "..", "vms.csv")
    df = pd.read_csv(csv_path)
    return df[df['cloud'] == cloud_name].to_dict('records')

# --- Configuration ---
config = pulumi.Config()
image_id = config.require("image_id")
key_pair_name = config.require("key_pair_name")
external_network_id = config.require("external_network_id")
external_network_name = config.require("external_network_name")

# --- Lecture du CSV ---
os_vms = get_vms_config('openstack')

# 1. Réseau
network = openstack.networking.Network("network-fun-os",
    name="network-fun-os",
    admin_state_up=True)

# 2. Sous-réseau
subnet = openstack.networking.Subnet("subnet-fun-os",
    network_id=network.id,
    cidr="192.168.1.0/24",
    ip_version=4,
    name="subnet-fun-os",
    dns_nameservers=["8.8.8.8", "8.8.4.4"])

# 3. Router (pour l'accès externe)
router = openstack.networking.Router("router-fun-os",
    name="router-fun-os",
    admin_state_up=True,
    external_network_id=external_network_id)

# 4. Attachement du sous-réseau au routeur
router_interface = openstack.networking.RouterInterface("router-interface",
    router_id=router.id,
    subnet_id=subnet.id)

# 5. Security Group pour les serveurs WEB/API
web_sg = openstack.networking.Secgroup("web-sg-fun-os",
    name="web-sg-fun-os",
    description="Autorise le trafic interne et le trafic du LB")

# 6. Security Group pour les serveurs DB
db_sg = openstack.networking.Secgroup("db-sg-fun-os",
    name="db-sg-fun-os",
    description="Autorise uniquement le trafic DB interne")

# Règle Ingress (Entrée) - SSH (pour debug)
ssh_rule = openstack.networking.SecgroupRule("ssh-rule",
    direction="ingress",
    ethertype="IPv4",
    protocol="tcp",
    port_range_min=22,
    port_range_max=22,
    remote_ip_prefix="0.0.0.0/0",
    security_group_id=web_sg.id)

# Règle Ingress (Entrée) - HTTP (depuis le Load Balancer)
http_lb_rule = openstack.networking.SecgroupRule("http-lb-rule",
    direction="ingress",
    ethertype="IPv4",
    protocol="tcp",
    port_range_min=80,
    port_range_max=80,
    # Autorise le trafic depuis le sous-réseau du LB (qui est le même que le subnet principal)
    remote_ip_prefix=subnet.cidr,
    security_group_id=web_sg.id)

# Règle Ingress (Entrée) - DB (MySQL/Postgres - Exemple 3306)
db_rule = openstack.networking.SecgroupRule("db-rule",
    direction="ingress",
    ethertype="IPv4",
    protocol="tcp",
    port_range_min=3306,
    port_range_max=3306,
    # Autorise le trafic depuis le SG des serveurs WEB/API
    remote_group_id=web_sg.id,
    security_group_id=db_sg.id)

# Règle Egress (Sortie) - Tout le trafic
egress_rule_web = openstack.networking.SecgroupRule("egress-rule-web",
    direction="egress",
    ethertype="IPv4",
    protocol="all",
    remote_ip_prefix="0.0.0.0/0",
    security_group_id=web_sg.id)

egress_rule_db = openstack.networking.SecgroupRule("egress-rule-db",
    direction="egress",
    ethertype="IPv4",
    protocol="all",
    remote_ip_prefix="0.0.0.0/0",
    security_group_id=db_sg.id)

# 7. Instances Nova (Création dynamique via Composant)
# Utilisation d'une compréhension de dictionnaire pour un code plus idiomatique
dynamic_servers = {
    vm['name']: OpenStackVmComponent(vm['name'],
        args={
            "vm_name": vm['name'],
            "vm_role": vm['role'],
            "image_id": image_id,
            "flavor_name": vm['type'],
            "key_pair_name": key_pair_name,
            "network_id": network.id,
            # Security Group : DB_SG pour les DBs, WEB_SG pour les autres
            "security_group_name": db_sg.name if vm['role'] == "db" else web_sg.name,
            "external_network_name": external_network_name,
            "disk_size_gb": int(vm['disk_size_gb']),
        })
    for vm in os_vms
}

# --- Ajout du Load Balancer (Octavia) ---

# 8. Load Balancer (Octavia)
web_lb = openstack.loadbalancer.LoadBalancer("web-lb-fun-os",
    name="web-lb-fun-os",
    vip_subnet_id=subnet.id)

# 9. Pool (Groupe de serveurs)
web_pool = openstack.loadbalancer.Pool("web-pool-fun-os",
    name="web-pool-fun-os",
    protocol="HTTP",
    lb_method="ROUND_ROBIN",
    loadbalancer_id=web_lb.id)

# 10. Health Monitor (Vérification de santé)
web_monitor = openstack.loadbalancer.Monitor("web-monitor-fun-os",
    pool_id=web_pool.id,
    type="HTTP",
    delay=5,
    timeout=3,
    max_retries=3,
    url_path="/index.html")

# 11. Listener (Écouteur)
http_listener = openstack.loadbalancer.Listener("http-listener-fun-os",
    name="http-listener-fun-os",
    protocol="HTTP",
    protocol_port=80,
    loadbalancer_id=web_lb.id,
    default_pool_id=web_pool.id)

# 12. Membres du Pool (Instances Web)
# On utilise une compréhension de liste pour créer les membres
# en s'assurant que l'instance est créée avant le membre du pool.
web_members = [
    openstack.loadbalancer.Member(f"web-member-{name}",
        pool_id=web_pool.id,
        # L'Output de l'instance garantit l'ordre de création
        address=server.instance.access_ip_v4,
        protocol_port=80)
    for name, server in dynamic_servers.items()
    if server.role == "web"
]

# 13. Floating IP pour le Load Balancer (Accès Public)
lb_fip = openstack.networking.Floatingip("lb-fip",
    pool=external_network_name)

# 14. Association de la Floating IP au Load Balancer
openstack.loadbalancer.FloatingIpAssociate("lb-fip-associate",
    floating_ip=lb_fip.address,
    loadbalancer_id=web_lb.id)

# --- Outputs ---
pulumi.export("lb_floating_ip", lb_fip.address)
pulumi.export("network_id", network.id)
pulumi.export("web_sg_id", web_sg.id)
pulumi.export("db_sg_id", db_sg.id)
