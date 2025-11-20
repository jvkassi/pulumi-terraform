output "lb_floating_ip" {
  description = "Adresse IP flottante du Load Balancer Octavia"
  value       = openstack_networking_floatingip_v2.lb_fip.address
}

output "web_sg_id" {
  description = "ID du Security Group Web"
  value       = openstack_networking_secgroup_v2.web_sg.id
}

output "db_sg_id" {
  description = "ID du Security Group DB"
  value       = openstack_networking_secgroup_v2.db_sg.id
}

output "network_id" {
  description = "ID du réseau créé"
  value       = openstack_networking_network_v2.network.id
}
