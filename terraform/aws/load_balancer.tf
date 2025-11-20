# 1. Application Load Balancer (ALB)
resource "aws_lb" "web_alb" {
  name               = "web-alb-fun-aws"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public.id]

  tags = {
    Name = "web-alb-fun-aws"
  }
}

# 2. Target Group (Groupe Cible)
resource "aws_lb_target_group" "web_tg" {
  name     = "web-tg-fun-aws"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/index.html"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

# 3. Listener (Écouteur)
resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.web_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web_tg.arn
  }
}

# 4. Enregistrement des Instances dans le Target Group
resource "aws_lb_target_group_attachment" "web_attachment" {
  for_each         = { for k, v in module.aws_vms : k => v.instance_id if v.role == "web" }
  target_group_arn = aws_lb_target_group.web_tg.arn
  target_id        = each.value
  port             = 80
}
