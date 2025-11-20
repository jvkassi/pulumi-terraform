# 1. Security Group pour les serveurs WEB/API
resource "openstack_networking_secgroup_v2" "web_sg" {
  name        = "web-sg-fun-os"
  description = "Autorise le trafic interne et le trafic du LB"
}

# 2. Security Group pour les serveurs DB
resource "openstack_networking_secgroup_v2" "db_sg" {
  name        = "db-sg-fun-os"
  description = "Autorise uniquement le trafic DB interne"
}

# Règle Ingress (Entrée) - SSH (pour debug)
resource "openstack_networking_secgroup_rule_v2" "ssh_rule" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.web_sg.id
}

# Règle Ingress (Entrée) - HTTP (depuis le Load Balancer)
resource "openstack_networking_secgroup_rule_v2" "http_lb_rule" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  # Autorise le trafic depuis le sous-réseau du LB (qui est le même que le subnet principal)
  remote_ip_prefix  = openstack_networking_subnet_v2.subnet.cidr
  security_group_id = openstack_networking_secgroup_v2.web_sg.id
}

# Règle Ingress (Entrée) - DB (MySQL/Postgres - Exemple 3306)
resource "openstack_networking_secgroup_rule_v2" "db_rule" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 3306
  port_range_max    = 3306
  # Autorise le trafic depuis le SG des serveurs WEB/API
  remote_group_id   = openstack_networking_secgroup_v2.web_sg.id
  security_group_id = openstack_networking_secgroup_v2.db_sg.id
}

# Règle Egress (Sortie) - Tout le trafic (pour les deux SGs)
resource "openstack_networking_secgroup_rule_v2" "egress_rule_web" {
  direction         = "egress"
  ethertype         = "IPv4"
  protocol          = "all"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.web_sg.id
}

resource "openstack_networking_secgroup_rule_v2" "egress_rule_db" {
  direction         = "egress"
  ethertype         = "IPv4"
  protocol          = "all"
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.db_sg.id
}
