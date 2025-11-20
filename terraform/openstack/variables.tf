variable "image_id" {
  description = "ID de l'image (cirros, ubuntu, etc.) pour l'instance Nova"
  type        = string
  # NOTE: L'utilisateur doit remplacer cette valeur par un ID d'image valide
  default     = "a218522f-879e-437a-806a-049581898144"
}

variable "flavor_name" {
  description = "Nom du 'flavor' (taille) de l'instance Nova"
  type        = string
  default     = "s1.small"
}

variable "key_pair_name" {
  description = "Nom de la paire de clés SSH existante dans OpenStack"
  type        = string
  # NOTE: L'utilisateur doit remplacer cette valeur par le nom d'une clé existante
  default     = "my-openstack-key"
}

variable "external_network_id" {
  description = "ID du réseau externe (public) pour le routeur"
  type        = string
  # NOTE: L'utilisateur doit remplacer cette valeur par l'ID de son réseau externe
  default     = "external-network-uuid"
}

variable "external_network_name" {
  description = "Nom du réseau externe (public) pour la Floating IP"
  type        = string
  # NOTE: L'utilisateur doit remplacer cette valeur par le nom de son réseau externe
  default     = "external-network-name"
}
