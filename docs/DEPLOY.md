# Deployment

CI/CD is handled via GitHub Actions (`.github/workflows/ci-cd.yml`).

## Flow

| Event | What happens |
|---|---|
| PR targeting `main` | Tests run. Merge is blocked if they fail. |
| Merge to `main` | Tests run, then auto-deploy to VM. |

## Deploy Script

The deploy script lives on the VM at `/opt/deploy/deploy-platform.sh`. It is **not** stored in this repo. To modify it, SSH into the VM directly.

It does the following:
1. `git pull` latest from `main`
2. `docker compose up -d --build`
3. `docker image prune -f`

## Secrets

Stored as GitHub org-level secrets under `Husky-Quantitative-Group`. No repo-level secrets are needed.

| Secret | Purpose |
|---|---|
| `VM_HOST` | VM IP address |
| `VM_USER` | SSH username |
| `VM_SSH_KEY` | SSH private key |
| `VM_PORT` | SSH port |


## Deployment Script
```bash
#!/bin/bash
set -e

REPO="hqg-platform"
PATH_TO_REPO="/home/software/$REPO"

echo "[$REPO] Starting deploy..."

cd $PATH_TO_REPO
git pull

docker compose up -d --build
docker image prune -f

echo "[$REPO] Deploy complete."

```


## Manual Deploy

If you need to deploy manually, SSH into the VM and run:

```bash
bash /opt/deploy/deploy-platform.sh
```