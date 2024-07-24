#!/bin/bash
yum update -y
yum install -y docker
service docker start
usermod -a -G docker ec2-user
# Authenticate Docker to ECR and run the container
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
docker pull public.ecr.aws/e2o8h8p3/grainger_recommendations_chatbot:latest
docker run -d -p 80:8505 public.ecr.aws/e2o8h8p3/grainger_recommendations_chatbot:latest > /var/log/docker_run.log 2>&1
