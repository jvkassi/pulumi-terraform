# 1. Réseau
resource "openstack_networking_network_v2" "network" {
  name           = "network-fun-os"
  admin_state_up = "true"
}

# 2. Sous-réseau
resource "openstack_networking_subnet_v2" "subnet" {
  network_id   = openstack_networking_network_v2.network.id
  cidr         = "192.168.1.0/24"
  ip_version   = 4
  name         = "subnet-fun-os"
  dns_nameservers = ["8.8.8.8", "8.8.4.4"]
}

# 3. Router (pour l'accès externe)
resource "openstack_networking_router_v2" "router" {
  name                = "router-fun-os"
  admin_state_up      = true
  external_network_id = var.external_network_id # Doit être fourni par l'utilisateur
}

# 4. Attachement du sous-réseau au routeur
resource "openstack_networking_router_interface_v2" "router_interface" {
  router_id = openstack_networking_router_v2.router.id
  subnet_id = openstack_networking_subnet_v2.subnet.id
}
