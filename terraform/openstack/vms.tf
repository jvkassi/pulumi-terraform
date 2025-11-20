# --- Données Dynamiques à partir du CSV ---
locals {
  vms_data = csvdecode(file("../../vms.csv"))
  os_vms   = { for vm in local.vms_data : vm.name => vm if vm.cloud == "openstack" }
}

# 1. Instances Nova (Création dynamique via Module)
module "os_vms" {
  for_each            = local.os_vms
  source              = "../modules/os_vm"
  vm_name             = each.key
  vm_role             = each.value.role
  image_id            = var.image_id
  flavor_name         = each.value.type
  key_pair_name       = var.key_pair_name
  network_id          = openstack_networking_network_v2.network.id
  # Security Group : DB_SG pour les DBs, WEB_SG pour les autres
  security_group_name = each.value.role == "db" ? openstack_networking_secgroup_v2.db_sg.name : openstack_networking_secgroup_v2.web_sg.name
  external_network_name = var.external_network_name
  disk_size_gb        = tonumber(each.value.disk_size_gb)
}
