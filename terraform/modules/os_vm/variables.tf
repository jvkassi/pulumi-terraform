variable "vm_name" {
  description = "Nom de la VM"
  type        = string
}

variable "vm_role" {
  description = "Rôle de la VM (web, db, api, etc.)"
  type        = string
}

variable "image_id" {
  description = "ID de l'image pour l'instance Nova"
  type        = string
}

variable "flavor_name" {
  description = "Nom du 'flavor' (taille) de l'instance Nova"
  type        = string
}

variable "key_pair_name" {
  description = "Nom de la paire de clés SSH existante dans OpenStack"
  type        = string
}

variable "network_id" {
  description = "ID du réseau interne"
  type        = string
}

variable "security_group_name" {
  description = "Nom du Security Group"
  type        = string
}

variable "external_network_name" {
  description = "Nom du réseau externe (public) pour la Floating IP"
  type        = string
}

variable "disk_size_gb" {
  description = "Taille du disque de la VM en GB"
  type        = number
  default     = 10
}
