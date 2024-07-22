#!/bin/bash
yum update -y
yum install -y docker
service docker start
usermod -a -G docker ec2-user
# Authenticate Docker to ECR and run the container
Login Succeeded
docker pull public.ecr.aws/e2o8h8p3/grainger_recommendations_chatbot:latest
docker run -d -p 80:8505 public.ecr.aws/e2o8h8p3/grainger_recommendations_chatbot:latest
