# 1. Security Group pour les serveurs WEB (Autoriser SSH et HTTP depuis LB/Internet)
resource "aws_security_group" "web_sg" {
  vpc_id      = aws_vpc.main.id
  name        = "web-sg-fun-aws"
  description = "Autorise SSH (22) et HTTP (80) depuis le LB/Internet"

  # Règle Ingress (Entrée) - SSH (pour debug)
  ingress {
    description = "SSH depuis Internet"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Règle Ingress (Entrée) - HTTP (depuis le Load Balancer)
  ingress {
    description     = "HTTP depuis le Load Balancer"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id] # Référence au SG de l'ALB
  }

  # Règle Egress (Sortie) - Tout le trafic (via NAT GW pour le privé, IGW pour le public)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "web-sg-fun-aws"
  }
}

# 2. Security Group pour les serveurs DB (Autoriser uniquement le trafic interne)
resource "aws_security_group" "db_sg" {
  vpc_id      = aws_vpc.main.id
  name        = "db-sg-fun-aws"
  description = "Autorise le trafic DB (3306) depuis les serveurs WEB/API"

  # Règle Ingress (Entrée) - DB (MySQL/Postgres - Exemple 3306)
  ingress {
    description     = "DB depuis les serveurs WEB/API"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.web_sg.id] # Autorise le trafic depuis le SG des serveurs WEB
  }

  # Règle Egress (Sortie) - Tout le trafic (via NAT GW)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "db-sg-fun-aws"
  }
}

# 3. Security Group pour l'ALB (Autoriser HTTP)
resource "aws_security_group" "alb_sg" {
  vpc_id      = aws_vpc.main.id
  name        = "alb-sg-fun-aws"
  description = "Autorise HTTP (80) pour l'ALB"

  ingress {
    description = "HTTP depuis Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "alb-sg-fun-aws"
  }
}
