output "web_server_public_ips" {
  description = "Adresses IP publiques des serveurs web AWS (via module)"
  value       = { for k, v in module.aws_vms : k => v.public_ip if v.role != "db" }
}

output "alb_dns_name" {
  description = "Nom DNS du Load Balancer (ALB)"
  value       = aws_lb.web_alb.dns_name
}

output "private_subnet_id" {
  description = "ID du sous-réseau privé (pour les DBs)"
  value       = aws_subnet.private.id
}

output "nat_gateway_id" {
  description = "ID de la NAT Gateway"
  value       = aws_nat_gateway.nat_gw.id
}

output "web_sg_id" {
  description = "ID du Security Group Web"
  value       = aws_security_group.web_sg.id
}

output "db_sg_id" {
  description = "ID du Security Group DB"
  value       = aws_security_group.db_sg.id
}

output "vpc_id" {
  description = "ID du VPC créé"
  value       = aws_vpc.main.id
}
