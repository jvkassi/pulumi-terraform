# --- Données Dynamiques à partir du CSV ---
locals {
  vms_data = csvdecode(file("../../vms.csv"))
  aws_vms  = { for vm in local.vms_data : vm.name => vm if vm.cloud == "aws" }
}

# 1. Instances EC2 (Création dynamique via Module)
module "aws_vms" {
  for_each            = local.aws_vms
  source              = "../modules/aws_vm"
  vm_name             = each.key
  vm_role             = each.value.role
  ami_id              = var.ami_id
  instance_type       = each.value.type
  key_pair_name       = var.key_pair_name
  # Sous-réseau : Privé pour les DBs, Public pour les autres (Web/API)
  subnet_id           = each.value.role == "db" ? aws_subnet.private.id : aws_subnet.public.id
  # Security Group : DB_SG pour les DBs, WEB_SG pour les autres
  security_group_id   = each.value.role == "db" ? aws_security_group.db_sg.id : aws_security_group.web_sg.id
  availability_zone   = aws_subnet.public.availability_zone # AZ est la même pour les deux subnets
  disk_size_gb        = tonumber(each.value.disk_size_gb)
}
