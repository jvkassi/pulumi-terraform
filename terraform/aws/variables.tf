variable "aws_region" {
  description = "Région AWS pour le déploiement"
  type        = string
  default     = "eu-west-3" # Région par défaut (Paris)
}

variable "ami_id" {
  description = "ID de l'AMI pour l'instance EC2 (Ubuntu 22.04 LTS)"
  type        = string
  default     = "ami-04e60174829a65389" # Exemple d'AMI Ubuntu 22.04 LTS (eu-west-3)
}

variable "instance_type" {
  description = "Type d'instance EC2"
  type        = string
  default     = "t2.micro"
}

variable "key_pair_name" {
  description = "Nom de la paire de clés SSH existante"
  type        = string
  # NOTE: L'utilisateur doit remplacer cette valeur par le nom d'une clé existante
  default     = "my-ssh-key"
}
