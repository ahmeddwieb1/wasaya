resource "aws_db_subnet_group" "wasaya" {
  name       = "wasaya-db-subnet-group"
  subnet_ids = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

resource "aws_db_instance" "wasaya" {
  identifier = "wasaya-db"

  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "wasaya"
  username = "root"
  password = "rootpassword"

  # Networking
  db_subnet_group_name   = aws_db_subnet_group.wasaya.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  skip_final_snapshot    = true

  lifecycle {
    prevent_destroy = false
  }
}
