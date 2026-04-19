data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "bastion" {
  count      = var.public_key != "" ? 1 : 0
  key_name   = var.key_pair_name
  public_key = var.public_key

  tags = { Name = "shopcloud-${var.environment}-bastion-key" }
}

resource "aws_instance" "bastion" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  key_name               = var.public_key != "" ? aws_key_pair.bastion[0].key_name : var.key_pair_name

  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    # Harden SSH
    sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    systemctl restart sshd
  EOF

  tags = { Name = "shopcloud-${var.environment}-bastion" }
}

resource "aws_eip" "bastion" {
  instance = aws_instance.bastion.id
  domain   = "vpc"

  tags = { Name = "shopcloud-${var.environment}-bastion-eip" }
}
