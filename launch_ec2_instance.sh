#!/bin/bash

# Variables
IMAGE_NAME="grainger_recommendations_chatbot"
REPOSITORY_URI="public.ecr.aws/e2o8h8p3/$IMAGE_NAME"
REGION="us-east-1"
KEY_PAIR_NAME="grainger_recs"
SECURITY_GROUP_NAME="grainger_recommendations_sg"
INSTANCE_TYPE="t2.medium"
AMI_ID="ami-0e5d65fb7cb2158eb"
USER_DATA_FILE="user_data.sh"
MY_PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)

# Get the default VPC ID
echo "Retrieving the default VPC ID..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text)

if [ -z "$VPC_ID" ]; then
    echo "No default VPC found. Exiting."
    exit 1
fi

# Step 0: Create a security group or get the existing one
echo "Checking for existing security group..."
SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$SECURITY_GROUP_NAME" "Name=vpc-id,Values=$VPC_ID" --query "SecurityGroups[*].GroupId" --output text)

if [ -z "$SECURITY_GROUP_ID" ]; then
    echo "Creating security group..."
    SECURITY_GROUP_ID=$(aws ec2 create-security-group --group-name $SECURITY_GROUP_NAME --description "Security group for grainger recommendations app" --vpc-id $VPC_ID --query 'GroupId' --output text)
    echo "Security group created with ID: $SECURITY_GROUP_ID"
else
    echo "Security group '$SECURITY_GROUP_NAME' already exists with ID: $SECURITY_GROUP_ID"
fi

# Authorize SSH, HTTP, and HTTPS access
echo "Authorizing SSH, HTTP, and HTTPS access..."
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 22 --cidr $MY_PUBLIC_IP/32
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 443 --cidr 0.0.0.0/0

# Step 1: Build the Docker Image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Step 2: Authenticate Docker to ECR
echo "Authenticating Docker to ECR..."
aws ecr-public get-login-password --region $REGION | docker login --username AWS --password-stdin public.ecr.aws

# Step 3: Tag and Push Image to ECR
echo "Tagging Docker image..."
docker tag $IMAGE_NAME:latest $REPOSITORY_URI:latest

echo "Pushing Docker image to ECR..."
docker push $REPOSITORY_URI:latest

# Step 4: Create User Data Script
cat << EOF > $USER_DATA_FILE
#!/bin/bash
yum update -y
yum install -y docker
service docker start
usermod -a -G docker ec2-user
# Authenticate Docker to ECR and run the container
$(aws ecr-public get-login-password --region $REGION | docker login --username AWS --password-stdin public.ecr.aws)
docker pull $REPOSITORY_URI:latest
docker run -d -p 80:8505 $REPOSITORY_URI:latest
EOF

# Step 5: Launch EC2 Instance
echo "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances --image-id $AMI_ID --count 1 --instance-type $INSTANCE_TYPE --key-name $KEY_PAIR_NAME --security-group-ids $SECURITY_GROUP_ID --user-data file://$USER_DATA_FILE --query "Instances[0].InstanceId" --output text)

# Wait until the instance is running
echo "Waiting for instance to be in 'running' state..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get the public IP of the instance
EC2_PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query "Reservations[0].Instances[0].PublicIpAddress" --output text)

echo "EC2 instance launched. Public IP: $EC2_PUBLIC_IP"

# Step 6: Output the public URL
echo "Your application is available at: http://$EC2_PUBLIC_IP"
