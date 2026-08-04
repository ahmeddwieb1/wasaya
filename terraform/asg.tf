#
# resource "aws_autoscaling_group" "example" {
#   vpc_zone_identifier = [aws_subnet.public_1.id, aws_subnet.public_2.id]
#   target_group_arns   = [aws_lb_target_group.wasaya_tg.arn]
#
#   launch_template {
#     id      = aws_launch_template.example.id
#     version = "$Latest"
#   }
#
#   min_size         = 2
#   max_size         = 4
#   desired_capacity = 2
#
#   lifecycle {
#     ignore_changes = [desired_capacity]
#   }
#   }
