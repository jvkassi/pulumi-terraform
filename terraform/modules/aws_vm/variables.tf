variable "vm_name" {
  description = "Nom de la VM"
  type        = string
}

variable "vm_role" {
  description = "Rôle de la VM (web, db, api, etc.)"
  type        = string
}

variable "ami_id" {
  description = "ID de l'AMI pour l'instance EC2"
  type        = string
}

variable "instance_type" {
  description = "Type d'instance EC2"
  type        = string
}

variable "key_pair_name" {
  description = "Nom de la paire de clés SSH existante"
  type        = string
}

variable "subnet_id" {
  description = "ID du sous-réseau public"
  type        = string
}

variable "security_group_id" {
  description = "ID du Security Group"
  type        = string
}

variable "availability_zone" {
  description = "Zone de disponibilité"
  type        = string
}

variable "disk_size_gb" {
  description = "Taille du disque de la VM en GB"
  type        = number
  default     = 10
}
