# 🚀 Projet Multi-Cloud "Fun & Impressionnant" avec Pulumi et Terraform (Dynamique CSV)

Bienvenue dans ce projet d'orchestration d'infrastructure multi-cloud, conçu pour être à la fois **robuste**, **éducatif** et **fun** !

Ce dépôt contient l'implémentation d'une architecture simple mais complète (un serveur web et une base de données) déployée sur deux plateformes cloud distinctes : **Amazon Web Services (AWS)** et **OpenStack**.

Nous utilisons deux outils d'Infrastructure as Code (IaC) leaders du marché :
1.  **Terraform** (HCL) : Pour une approche déclarative standard.
2.  **Pulumi** (Python) : Pour une approche programmatique moderne.

---

## 🗺️ Architecture Cible (Dynamique par CSV)

L'objectif est de déployer une infrastructure dynamique. Les spécifications des VMs sont lues à partir du fichier `vms.csv`.

| Composant | Description |
| :--- | :--- |
| **Fichier `vms.csv`** | Source de vérité pour la création des VMs (nom, cloud, type/flavor, rôle). |
| **Réseau** | Création d'un réseau de base (VPC/Network) sur chaque cloud. |
| **Instances** | Création de multiples instances EC2 (AWS) ou Nova (OpenStack) en fonction du `vms.csv`. |
| **Réseau AWS** | **VPC** avec **Sous-réseau Public** et **Sous-réseau Privé** (pour les DBs). |
| **Connectivité** | **NAT Gateway** (pour l'accès Internet des VMs privées) et **Internet Gateway**. |
| **Security Groups** | **Granulaires** : `web_sg` (autorise LB/SSH) et `db_sg` (autorise uniquement `web_sg` sur le port DB). |
| **Load Balancer** | **ALB** (Application Load Balancer) | **Octavia** (Load Balancer as a Service) |
| **Stockage/DB** | Un volume de stockage (EBS/Cinder) est attaché uniquement aux VMs dont le rôle est `db`. |

### 📄 Fichier `vms.csv`

Ce fichier est la source de vérité pour la création des VMs. Il contient les colonnes suivantes :

| Colonne | Description |
| :--- | :--- |
| `name` | Nom unique de la VM. |
| `cloud`| Cloud cible (`aws` ou `openstack`). |
| `role` | Rôle de la VM (`web`, `db`, `api`, etc.). |
| `type` | Type d'instance (ex: `t2.micro` sur AWS, `m1.small` sur OpenStack). |
| `disk_size_gb` | **NOUVEAU** : Taille du disque racine et du volume de données (si rôle `db`) en Gigaoctets (Go). |

**Exemple :**
```csv
name,cloud,type,role,disk_size_gb
web-prod-01,aws,t2.micro,web,10
db-staging-01,aws,t2.medium,db,50
web-test-01,openstack,m1.small,web,10
api-test-01,openstack,m1.small,api,10
```

---

## 🛠️ Prérequis Indispensables

Pour exécuter ce code, vous devez disposer des éléments suivants :

### 1. Outils Locaux

| Outil | Version Recommandée | Installation |
| :--- | :--- | :--- |
| **Git** | Dernière | `sudo apt install git` |
| **Terraform** | v1.0+ | [Documentation Terraform](https://developer.hashicorp.com/terraform/install) |
| **Pulumi** | v3.0+ | [Documentation Pulumi](https://www.pulumi.com/docs/get-started/install/) |
| **Python** | 3.9+ | `sudo apt install python3 python3-pip` |
| **Dépendances Python** | - | `pip install -r requirements.txt` (nécessite `pandas` pour la lecture CSV et la refactorisation Pulumi) |

### 2. Configuration des Clouds

#### ☁️ AWS (Amazon Web Services)

Vous devez avoir configuré vos identifiants AWS. Le code utilisera la configuration par défaut de votre environnement.

*   **Méthode 1 (Recommandée) :** Fichier `~/.aws/credentials`
    ```ini
    [default]
    aws_access_key_id = VOTRE_CLE_ID
    aws_secret_access_key = VOTRE_CLE_SECRETE
    ```
*   **Méthode 2 :** Variables d'environnement
    ```bash
    export AWS_ACCESS_KEY_ID="VOTRE_CLE_ID"
    export AWS_SECRET_ACCESS_KEY="VOTRE_CLE_SECRETE"
    export AWS_REGION="eu-west-3" # Exemple
    ```

#### ☁️ OpenStack

Vous devez disposer d'un fichier de configuration OpenStack.

*   **Fichier `clouds.yaml` :** Ce fichier contient les informations de connexion à votre cloud OpenStack. Il est généralement généré depuis l'interface Horizon (télécharger le fichier de configuration OpenStack RC).
*   **Variables d'environnement :** Le code Terraform et Pulumi s'attendent à ce que les variables d'environnement OpenStack soient sourcées.
    ```bash
    # Exemple de sourcing du fichier RC
    source /chemin/vers/votre/openstack-rc.sh
    ```

---

## 📂 Structure du Projet

Le projet est maintenant **modulaire**, **structuré** et **découpé** pour une lisibilité maximale :

```
.
├── README.md               # Ce fichier
├── vms.csv                 # Le fichier source pour la création dynamique des VMs
├── terraform/              # Code d'infrastructure avec Terraform (HCL)
│   ├── modules/            # Modules réutilisables
│   │   ├── aws_vm/         # Module pour créer une VM AWS (EC2 + EBS)
│   │   └── os_vm/          # Module pour créer une VM OpenStack (Nova + Cinder + FIP)
│   ├── aws/                # Infrastructure AWS (découpée pour la lisibilité)
│   │   ├── main.tf         # Configuration du provider
│   │   ├── network.tf      # VPC, Subnets (Public/Privé), IGW, NAT GW, Route Tables
│   │   ├── security_groups.tf # SGs granulaires (web, db, alb)
│   │   ├── vms.tf          # Définition des VMs (lecture CSV + module)
│   │   ├── load_balancer.tf # Définition de l'ALB
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── openstack/          # Infrastructure OpenStack (découpée pour la lisibilité)
│       ├── main.tf         # Configuration du provider
│       ├── network.tf      # Network, Subnet, Router
│       ├── security_groups.tf # SGs granulaires (web, db)
│       ├── vms.tf          # Définition des VMs (lecture CSV + module)
│       ├── load_balancer.tf # Définition d'Octavia LB
│       ├── variables.tf
│       └── outputs.tf
└── pulumi/                 # Code d'infrastructure avec Pulumi (Python)
    ├── aws/                # Infrastructure AWS (utilise le composant AwsVmComponent)
    │   ├── __main__.py     # Code principal (inclut toutes les ressources)
    │   ├── vm_component.py # Composant Python pour la VM AWS
    │   └── Pulumi.yaml
    ├── openstack/          # Infrastructure OpenStack (utilise le composant OpenStackVmComponent)
    │   ├── __main__.py     # Code principal (inclut toutes les ressources)
    │   ├── vm_component.py # Composant Python pour la VM OpenStack
    │   └── Pulumi.yaml
    └── requirements.txt    # Dépendances Python (pulumi-*, pandas)
```

---

## 🛠️ Instructions d'Exécution

### 1. Terraform

Naviguez dans le dossier de votre choix (`terraform/aws` ou `terraform/openstack`).

```bash
# Initialisation
terraform init

# Planification (vérification)
terraform plan

# Déploiement
terraform apply
```

### 2. Pulumi

Naviguez dans le dossier de votre choix (`pulumi/aws` ou `pulumi/openstack`).

```bash
# Créer un environnement virtuel et installer les dépendances
cd pulumi/aws # ou openstack
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt # Nécessite l'installation de pandas et des SDK Pulumi (dans requirements.txt)

# Note : Les composants Pulumi (vm_component.py) sont importés localement.
# Le code Pulumi a été refactorisé pour utiliser des fonctions utilitaires et des compréhensions de dictionnaire Python,
# le rendant plus idiomatique et "Software Engineering".
# Assurez-vous que le fichier vm_component.py est présent dans le même dossier que __main__.py.

# Initialisation du stack Pulumi
pulumi stack init dev

# Configuration des variables (si nécessaire)
# pulumi config set aws:region eu-west-3

# Déploiement
pulumi up
```

Amusez-vous bien ! 🚀
