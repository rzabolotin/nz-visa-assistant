# Run project in AWS Cloud

# Launch an EC2 instance

We will use AWS CLI and you need to have it installed and configured. If you don't have it, you can follow the instructions [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html).

1. Create a new key pair if you don't have one.

```bash
aws ec2 create-key-pair --key-name llm-zoomcamp --query 'KeyMaterial' --output text > ~/.ssh/llm-zoomcamp.pem
chmod 400 ~/.ssh/llm-zoomcamp.pem


2. Create a security group

```bash
aws ec2 create-security-group --group-name llm-zoomcamp-sg --description "Group for LLM Zoomcamp"

aws ec2 authorize-security-group-ingress --group-name llm-zoomcamp-sg --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-name llm-zoomcamp-sg --protocol tcp --port 8080 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-name llm-zoomcamp-sg --protocol tcp --port 3000 --cidr 0.0.0.0/0

```
Write down the security group ID, you will need it in the next step

3. Launch an EC2 instance

```bash
aws ec2 run-instances \
  --image-id ami-089f365c7b6a04f00 \
  --count 1 \
  --instance-type t3.medium \
  --key-name llm-zoomcamp \
  --security-group-ids sg-0421e127d6c4c6264 \
  --block-device-mappings "[{\"DeviceName\":\"/dev/xvda\",\"Ebs\":{\"VolumeSize\":20,\"VolumeType\":\"gp2\"}}]"
```

Replace `sg-xxxxxxxx` with the security group ID you created in the previous step.
ami-089f365c7b6a04f00 is the latest Amazon Linux 2 AMI. You can find the latest AMI ID for Amazon Linux 2 [here](https://aws.amazon.com/amazon-linux-2/release-notes/).

4. Get the public IP of the instance

```bash
aws ec2 describe-instances --query 'Reservations[].Instances[].PublicIpAddress' --output text
```

5. SSH into the instance

```bash
ssh -i ~/.ssh/llm-zoomcamp.pem ec2-user@<public-ip>
```

6. Install Docker and Docker Compose

```bash
sudo yum update -y
sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo chkconfig docker on
sudo yum install -y git
sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Run the project

7. Clone the repository

```bash
git clone https://github.com/rzabolotin/nz-visa-assistant.git
    cd nz-visa-assistant/app
```

8. Fill in the `.env` file

```bash
cp .env.sample .env
vim .env
```

9. Run the project

```bash
 sudo /usr/local/bin/docker-compose up -d
```
