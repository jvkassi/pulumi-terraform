# 1. Load Balancer (Octavia)
resource "openstack_lb_loadbalancer_v2" "web_lb" {
  name          = "web-lb-fun-os"
  vip_subnet_id = openstack_networking_subnet_v2.subnet.id
}

# 2. Pool (Groupe de serveurs)
resource "openstack_lb_pool_v2" "web_pool" {
  name        = "web-pool-fun-os"
  protocol    = "HTTP"
  lb_method   = "ROUND_ROBIN"
  loadbalancer_id = openstack_lb_loadbalancer_v2.web_lb.id
}

# 3. Health Monitor (Vérification de santé)
resource "openstack_lb_monitor_v2" "web_monitor" {
  pool_id     = openstack_lb_pool_v2.web_pool.id
  type        = "HTTP"
  delay       = 5
  timeout     = 3
  max_retries = 3
  url_path    = "/index.html"
}

# 4. Listener (Écouteur)
resource "openstack_lb_listener_v2" "http_listener" {
  name            = "http-listener-fun-os"
  protocol        = "HTTP"
  protocol_port   = 80
  loadbalancer_id = openstack_lb_loadbalancer_v2.web_lb.id
  default_pool_id = openstack_lb_pool_v2.web_pool.id
}

# 5. Membres du Pool (Instances Web)
resource "openstack_lb_member_v2" "web_members" {
  for_each      = { for k, v in module.os_vms : k => v.instance_id if v.role == "web" }
  pool_id       = openstack_lb_pool_v2.web_pool.id
  # L'adresse IP interne est récupérée du module
  address       = module.os_vms[each.key].access_ip_v4
  protocol_port = 80
}

# 6. Floating IP pour le Load Balancer (Accès Public)
resource "openstack_networking_floatingip_v2" "lb_fip" {
  pool = var.external_network_name
}

# 7. Association de la Floating IP au Load Balancer
resource "openstack_lb_floatingip_associate_v2" "lb_fip_associate" {
  floating_ip_id = openstack_networking_floatingip_v2.lb_fip.id
  loadbalancer_id = openstack_lb_loadbalancer_v2.web_lb.id
}
