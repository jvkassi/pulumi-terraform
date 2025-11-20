# Module pour créer une instance Nova et son volume Cinder attaché (si rôle 'db')

# 1. Instance Nova
resource "openstack_compute_instance_v2" "vm" {
  name            = var.vm_name
  image_id        = var.image_id
  flavor_name     = var.flavor_name
  key_pair        = var.key_pair_name
  security_groups = [var.security_group_name]

  network {
    uuid = var.network_id
  }

  user_data = <<-EOF
              #!/bin/bash
              echo "Hello from OpenStack Nova - Orchestré par Terraform (Module)! Je suis ${var.vm_name} (${var.vm_role})" > index.html
              nohup busybox httpd -f -p 80 &
              EOF

  metadata = {
    role = var.vm_role
  }
}

# 2. Floating IP (pour l'accès public)
resource "openstack_networking_floatingip_v2" "fip" {
  pool = var.external_network_name
}

# 3. Association de la Floating IP à l'Instance
resource "openstack_compute_floatingip_associate_v2" "fip_associate" {
  floating_ip = openstack_networking_floatingip_v2.fip.address
  instance_id = openstack_compute_instance_v2.vm.id
}

# 4. Volume Cinder (si rôle 'db')
resource "openstack_blockstorage_volume_v3" "db_volume" {
  count = var.vm_role == "db" ? 1 : 0
  name  = "volume-${var.vm_name}"
  size  = var.disk_size_gb # Taille dynamique
}

# 5. Attachement du Volume à l'Instance (si rôle 'db')
resource "openstack_compute_volume_attach_v2" "db_attach" {
  count       = var.vm_role == "db" ? 1 : 0
  instance_id = openstack_compute_instance_v2.vm.id
  volume_id   = openstack_blockstorage_volume_v3.db_volume[0].id
  device      = "/dev/vdb"
}

# --- Outputs du Module ---
output "instance_id" {
  value = openstack_compute_instance_v2.vm.id
}

output "floating_ip" {
  value = openstack_networking_floatingip_v2.fip.address
}

output "role" {
  value = var.vm_role
}
