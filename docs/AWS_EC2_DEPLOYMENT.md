# Deploy RepoPilot on AWS EC2 with Qdrant Cloud

This deployment exposes only the frontend on port 80. Nginx forwards `/api`
requests internally to the FastAPI backend. Qdrant Cloud stores the vector index.

## 1. EC2 security group

Allow:

- TCP 22 only from your current public IP address.
- TCP 80 from `0.0.0.0/0` and `::/0` for the public demo.

Do not open ports 8000, 6333, or 6334 to the internet.

## 2. Connect and install Docker

For an Ubuntu EC2 instance, connect with your key pair and run:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
newgrp docker
docker --version
docker compose version
```

For Amazon Linux 2023, replace the first two installation commands with:

```bash
sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
newgrp docker
```

If `docker compose` is not available on Amazon Linux, install the Docker Compose plugin using Docker's official instructions for your operating system.

## 3. Clone and configure

```bash
git clone https://github.com/muffin-5/repopilot.git
cd repopilot
cp .env.aws.example .env
nano .env
```

In `.env`, enter your Gemini API key, Qdrant Cloud HTTPS endpoint, and Qdrant **database API key**. Do not use the Qdrant Cloud management key. Keep `.env` private:

```bash
chmod 600 .env
```

## 4. Start the demo

```bash
docker compose -f docker-compose.aws.yml up -d --build
docker compose -f docker-compose.aws.yml ps
curl http://localhost/health
```

Open `http://YOUR_EC2_PUBLIC_IP` in a browser. On first use, submit a small public repository to index. The first request can take longer because the embedding model is downloaded into the backend container.

If you previously started a build before the CPU-only configuration was pulled, stop it with `Ctrl+C`, pull the latest changes, and clear only the unused Docker build cache before rebuilding:

```bash
git pull
docker builder prune -af
docker compose -f docker-compose.aws.yml up -d --build
```

## 5. Useful operations

```bash
# View logs
docker compose -f docker-compose.aws.yml logs -f

# Deploy new GitHub changes
git pull
docker compose -f docker-compose.aws.yml up -d --build

# Stop without deleting indexed repositories
docker compose -f docker-compose.aws.yml down
```

The `repo_data` Docker volume persists cloned repositories and metadata. Your Qdrant collection persists in Qdrant Cloud.

## 6. Optional custom domain and HTTPS

After the plain HTTP demo works, point your domain's A record to the EC2 public IP and place a reverse proxy with a TLS certificate in front of the frontend. Do not add this before the basic deployment is working.
