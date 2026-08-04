resource "aws_lb" "test" {
  name               = "test-lb-tf"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public_1.id, aws_subnet.public_2.id]


  }
resource "aws_lb_target_group" "wasaya_tg" {
  name     = "tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.mainVPC.id
  health_check {
    path                = "/health"
    port = 8000
    protocol = "HTTP"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.test.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.wasaya_tg.arn
  }
}