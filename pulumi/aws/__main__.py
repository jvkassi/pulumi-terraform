"""Un projet Pulumi pour déployer une infrastructure web simple sur AWS."""

import pulumi
import pulumi_aws as aws
import pandas as pd
import os
from vm_component import AwsVmComponent # Import du composant

# --- Fonctions Utilitaires ---
def get_vms_config(cloud_name: str) -> list:
    """Lit le CSV et filtre les VMs pour le cloud spécifié."""
    # Le chemin est relatif au répertoire racine du projet (où se trouve vms.csv)
    csv_path = os.path.join(os.getcwd(), "..", "..", "vms.csv")
    df = pd.read_csv(csv_path)
    return df[df['cloud'] == cloud_name].to_dict('records')

# --- Configuration ---
# Récupération de la région AWS depuis la configuration Pulumi
config = pulumi.Config()
aws_region = config.get("aws_region") or "eu-west-3"
ami_id = config.get("ami_id") or "ami-04e60174829a65389" # Exemple d'AMI Ubuntu 22.04 LTS (eu-west-3)
key_pair_name = config.get("key_pair_name") or "my-ssh-key"

# Configuration du fournisseur AWS
aws_provider = aws.Provider("aws-provider", region=aws_region)

# --- Lecture du CSV ---
aws_vms = get_vms_config('aws')

# 1. Réseau (VPC)
vpc = aws.ec2.Vpc("vpc-fun-aws",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={
        "Name": "vpc-fun-aws",
    },
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 2. Sous-réseau Public (pour les Load Balancers et les VMs Web/API publiques)
subnet_public = aws.ec2.Subnet("subnet-public-fun-aws",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    availability_zone=pulumi.Output.concat(aws_region, "a"),
    tags={
        "Name": "subnet-public-fun-aws",
    },
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 3. Sous-réseau Privé (pour les VMs DB)
subnet_private = aws.ec2.Subnet("subnet-private-fun-aws",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    map_public_ip_on_launch=False,
    availability_zone=pulumi.Output.concat(aws_region, "a"),
    tags={
        "Name": "subnet-private-fun-aws",
    },
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 4. Internet Gateway
igw = aws.ec2.InternetGateway("igw-fun-aws",
    vpc_id=vpc.id,
    tags={
        "Name": "igw-fun-aws",
    },
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 5. Elastic IP pour la NAT Gateway
nat_eip = aws.ec2.Eip("nat-eip-fun-aws",
    vpc=True,
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 6. NAT Gateway (dans le sous-réseau public)
nat_gw = aws.ec2.NatGateway("nat-gw-fun-aws",
    allocation_id=nat_eip.id,
    subnet_id=subnet_public.id,
    tags={
        "Name": "nat-gw-fun-aws",
    },
    opts=pulumi.ResourceOptions(provider=aws_provider, depends_on=[igw]))

# 7. Route Table pour le trafic Public (via Internet Gateway)
route_table_public = aws.ec2.RouteTable("route-table-public-fun-aws",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        ),
    ],
    tags={
        "Name": "route-table-public-fun-aws",
    },
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 8. Association du Route Table au Sous-réseau Public
aws.ec2.RouteTableAssociation("route-table-association-public",
    subnet_id=subnet_public.id,
    route_table_id=route_table_public.id,
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 9. Route Table pour le trafic Privé (via NAT Gateway)
route_table_private = aws.ec2.RouteTable("route-table-private-fun-aws",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            nat_gateway_id=nat_gw.id,
        ),
    ],
    tags={
        "Name": "route-table-private-fun-aws",
    },
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 10. Association du Route Table au Sous-réseau Privé
aws.ec2.RouteTableAssociation("route-table-association-private",
    subnet_id=subnet_private.id,
    route_table_id=route_table_private.id,
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 11. Security Group pour l'ALB (Autoriser HTTP)
alb_sg = aws.ec2.SecurityGroup("alb-sg-fun-aws",
    vpc_id=vpc.id,
    description="Autorise HTTP (80) pour l'ALB",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="HTTP depuis Internet",
            from_port=80,
            to_port=80,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    tags={
        "Name": "alb-sg-fun-aws",
    },
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 12. Security Group pour les serveurs WEB/API
web_sg = aws.ec2.SecurityGroup("web-sg-fun-aws",
    vpc_id=vpc.id,
    description="Autorise SSH (22) et HTTP (80) depuis le LB/Internet",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="SSH depuis Internet",
            from_port=22,
            to_port=22,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
        # Règle Ingress (Entrée) - HTTP (depuis le Load Balancer)
        aws.ec2.SecurityGroupIngressArgs(
            description="HTTP depuis le Load Balancer",
            from_port=80,
            to_port=80,
            protocol="tcp",
            security_groups=[alb_sg.id],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    tags={
        "Name": "web-sg-fun-aws",
    },
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 13. Security Group pour les serveurs DB
db_sg = aws.ec2.SecurityGroup("db-sg-fun-aws",
    vpc_id=vpc.id,
    description="Autorise le trafic DB (3306) depuis les serveurs WEB/API",
    ingress=[
        # Règle Ingress (Entrée) - DB (MySQL/Postgres - Exemple 3306)
        aws.ec2.SecurityGroupIngressArgs(
            description="DB depuis les serveurs WEB/API",
            from_port=3306,
            to_port=3306,
            protocol="tcp",
            security_groups=[web_sg.id], # Autorise le trafic depuis le SG des serveurs WEB
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    tags={
        "Name": "db-sg-fun-aws",
    },
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 14. Instances EC2 (Création dynamique via Composant)
# Utilisation d'une compréhension de dictionnaire pour un code plus idiomatique
dynamic_servers = {
    vm['name']: AwsVmComponent(vm['name'],
        args={
            "vm_name": vm['name'],
            "vm_role": vm['role'],
            "ami_id": ami_id,
            "instance_type": vm['type'],
            "key_pair_name": key_pair_name,
            # Sous-réseau : Privé pour les DBs, Public pour les autres (Web/API)
            "subnet_id": subnet_private.id if vm['role'] == "db" else subnet_public.id,
            # Security Group : DB_SG pour les DBs, WEB_SG pour les autres
            "security_group_id": db_sg.id if vm['role'] == "db" else web_sg.id,
            "availability_zone": subnet_public.availability_zone,
            "disk_size_gb": int(vm['disk_size_gb']),
        },
        opts=pulumi.ResourceOptions(provider=aws_provider))
    for vm in aws_vms
}

# 15. Application Load Balancer (ALB)
web_alb = aws.lb.LoadBalancer("web-alb-fun-aws",
    internal=False,
    load_balancer_type="application",
    security_groups=[alb_sg.id],
    subnets=[subnet_public.id], # Utilisation du subnet public
    tags={
        "Name": "web-alb-fun-aws",
    },
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 16. Target Group (Groupe Cible)
web_tg = aws.lb.TargetGroup("web-tg-fun-aws",
    port=80,
    protocol="HTTP",
    vpc_id=vpc.id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        path="/index.html",
        protocol="HTTP",
        matcher="200",
        interval=30,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=2,
    ),
    tags={
        "Name": "web-tg-fun-aws",
    },
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 17. Listener (Écouteur)
http_listener = aws.lb.Listener("http-listener",
    load_balancer_arn=web_alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[aws.lb.ListenerDefaultActionArgs(
        type="forward",
        target_group_arn=web_tg.arn,
    )],
    opts=pulumi.ResourceOptions(provider=aws_provider))

# 18. Enregistrement des Instances dans le Target Group
web_servers_to_register = [
    server.instance_id
    for server in dynamic_servers.values()
    if server.role == "web"
]

# On utilise une boucle simple car Pulumi gère l'ordre via les Outputs
for i, instance_id in enumerate(web_servers_to_register):
    aws.lb.TargetGroupAttachment(f"web-attachment-{i}",
        target_group_arn=web_tg.arn,
        target_id=instance_id,
        port=80,
        opts=pulumi.ResourceOptions(provider=aws_provider))

# --- Outputs ---
# Utilisation d'une compréhension de dictionnaire pour les Outputs
public_ips = {name: server.public_ip for name, server in dynamic_servers.items()}
pulumi.export("web_server_public_ips", public_ips)
pulumi.export("alb_dns_name", web_alb.dns_name)
pulumi.export("vpc_id", vpc.id)
pulumi.export("private_subnet_id", subnet_private.id)
pulumi.export("nat_gateway_id", nat_gw.id)
pulumi.export("web_sg_id", web_sg.id)
pulumi.export("db_sg_id", db_sg.id)
