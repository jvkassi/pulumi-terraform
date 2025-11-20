# Configuration du fournisseur OpenStack
terraform {
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 1.50.0"
    }
  }
}

provider "openstack" {
  # La configuration est lue à partir des variables d'environnement (OS_*)
  # ou du fichier clouds.yaml.
}
