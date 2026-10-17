terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_ami" "deep_learning" {
  most_recent = true
  owners      = ["898082745236"] # AWS Deep Learning AMIs

  filter {
    name   = "name"
    values = ["Deep Learning Base Proprietary Nvidia Driver GPU AMI (Ubuntu 20.04) *"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "training" {
  name        = "${var.project_name}-training-sg"
  description = "Security group for Video2Knowledge training instance"
  vpc_id      = var.vpc_id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "Backend API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "Frontend"
    from_port   = 5173
    to_port     = 5173
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-training-sg"
  }
}

resource "aws_instance" "training" {
  ami                         = var.use_gpu ? data.aws_ami.deep_learning.id : data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  key_name                    = var.key_pair_name
  vpc_security_group_ids      = [aws_security_group.training.id]
  subnet_id                   = var.subnet_id
  associate_public_ip_address = true

  root_block_device {
    volume_size = var.volume_size
    volume_type = "gp3"
    throughput  = 250
    iops        = 3000
    encrypted   = true

    tags = {
      Name = "${var.project_name}-training-vol"
    }
  }

  user_data = <<-USERDATA
    #!/bin/bash
    exec > /var/log/user-data.log 2>&1

    apt-get update
    apt-get install -y python3-pip unzip

    curl -fsSL https://get.docker.com | sh
    usermod -aG docker ubuntu
    chmod 666 /var/run/docker.sock

    pip3 install huggingface_hub --break-system-packages

    cd /home/ubuntu
    git clone https://github.com/laxmi1707/PatternRecognSystem-Video2Text.git
    chown -R ubuntu:ubuntu PatternRecognSystem-Video2Text

    echo "Setup complete." > /home/ubuntu/READY
    chown ubuntu:ubuntu /home/ubuntu/READY
  USERDATA

  tags = {
    Name = "${var.project_name}-training"
  }
}
