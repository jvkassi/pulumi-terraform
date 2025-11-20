# Module pour créer une instance EC2 et son volume EBS attaché (si rôle 'db')

# 1. Instance EC2
resource "aws_instance" "vm" {
  ami           = var.ami_id
  instance_type = var.instance_type
  key_name      = var.key_pair_name
  subnet_id     = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  user_data = <<-EOF
              #!/bin/bash
              echo "Hello from AWS EC2 - Orchestré par Terraform (Module)! Je suis ${var.vm_name} (${var.vm_role})" > index.html
              nohup busybox httpd -f -p 80 &
              EOF

  tags = {
    Name = var.vm_name
    Role = var.vm_role
  }

  root_block_device {
    volume_size = var.disk_size_gb
  }
}

# 2. Volume EBS (si rôle 'db')
resource "aws_ebs_volume" "db_volume" {
  count             = var.vm_role == "db" ? 1 : 0
  availability_zone = var.availability_zone
  size              = var.disk_size_gb # Taille dynamique
  type              = "gp3"
  tags = {
    Name = "volume-${var.vm_name}"
    Role = var.vm_role
  }
}

# 3. Attachement du Volume à l'Instance (si rôle 'db')
resource "aws_volume_attachment" "db_attach" {
  count       = var.vm_role == "db" ? 1 : 0
  device_name = "/dev/sdh"
  volume_id   = aws_ebs_volume.db_volume[0].id
  instance_id = aws_instance.vm.id
}

# --- Outputs du Module ---
output "instance_id" {
  value = aws_instance.vm.id
}

output "public_ip" {
  value = aws_instance.vm.public_ip
}

output "role" {
  value = var.vm_role
}
