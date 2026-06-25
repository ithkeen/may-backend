# 部署领域

本项目采用 GitHub Actions + GHCR + Docker Compose 部署。

## 部署目标

每次代码合并或推送到 `main` 后，GitHub Actions 自动完成以下流程：

```text
push main
  -> GitHub Actions 构建 Docker 镜像
  -> 推送到 GHCR，也就是 GitHub Container Registry
  -> SSH 到服务器
  -> docker compose pull
  -> docker compose up -d
  -> 部署完成后通过服务器地址或域名访问
```

## 部署位置

初版部署到单台 Linux 云服务器，推荐 Ubuntu 22.04 或 Ubuntu 24.04。

服务器需要：

- 安装 Docker 和 Docker Compose。
- 开放 SSH 端口，默认 `22`。
- 开放应用访问端口，默认 `8000`。
- 准备部署目录，默认 `/opt/may-backend`。

## 部署契约

应用容器必须满足：

- 监听 `0.0.0.0:8000`。
- 通过环境变量读取配置。
- 不依赖容器本地临时状态保存业务数据。
- 日志写入容器内 `/app/logs`，并挂载到服务器部署目录下的 `logs/`。

当前镜像默认启动命令：

```bash
uvicorn may_backend.app:create_app --factory --host 0.0.0.0 --port 8000
```

后续如果服务入口变化，只需要调整 `Dockerfile` 的 `CMD` 或 `docker-compose.prod.yml` 的 `command`。

## 文件说明

```text
Dockerfile
  构建生产镜像。

.dockerignore
  控制 Docker 构建上下文，避免把本地环境、日志、密钥打进镜像。

docker-compose.prod.yml
  服务器生产运行配置，包含应用端口映射和日志目录挂载。

.env.example
  环境变量示例。服务器上的真实配置文件为 /opt/may-backend/.env。

.github/workflows/deploy.yml
  GitHub Actions 自动部署流程。
```

## GitHub Secrets

在 GitHub 仓库中进入：

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

配置：

```text
DEPLOY_HOST=服务器 IP
DEPLOY_USER=服务器用户名
DEPLOY_PORT=22
DEPLOY_PASSWORD=服务器 SSH 密码
DEPLOY_PATH=/opt/may-backend
```

## 服务器准备

安装 Docker：

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

退出 SSH 后重新登录，验证：

```bash
docker version
docker compose version
```

准备部署目录：

```bash
sudo mkdir -p /opt/may-backend
sudo chown -R $USER:$USER /opt/may-backend
cd /opt/may-backend
touch .env
mkdir -p logs
```

当前可按仓库中的 `.env.example` 内容创建服务器 `.env`。服务器上的 `.env` 不提交到 Git。

如需修改对外端口，可在服务器 `/opt/may-backend/.env` 写入：

```bash
APP_PORT=8000
```

## 自动部署

推送到 `main`：

```bash
git push origin main
```

GitHub Actions 会自动：

1. 构建 Docker 镜像。
2. 推送镜像到 `ghcr.io/<owner>/<repo>:<commit-sha>`。
3. 上传 `docker-compose.prod.yml` 到服务器。
4. 登录 GHCR。
5. 拉取新镜像。
6. 重启容器。
7. 打印容器日志，便于确认启动状态。

## 访问验证

部署完成后访问：

```text
http://<服务器 IP>:8000/api/v1/ping
```

期望响应：

```json
{"message":"pong"}
```

## 手动查看状态

登录服务器：

```bash
cd /opt/may-backend
IMAGE_NAME=ghcr.io/<owner>/<repo> IMAGE_TAG=<commit-sha> docker compose -f docker-compose.prod.yml ps
IMAGE_NAME=ghcr.io/<owner>/<repo> IMAGE_TAG=<commit-sha> docker compose -f docker-compose.prod.yml logs -f
```

也可以直接查看容器：

```bash
docker ps
docker logs -f may-backend
```

查看应用日志文件：

```bash
tail -f /opt/may-backend/logs/app.jsonl
```

## 手动更新

通常不需要手动更新。需要时可在服务器执行：

```bash
cd /opt/may-backend
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

手动执行时需要确保当前 shell 中存在 `IMAGE_NAME` 和 `IMAGE_TAG`，或在 `/opt/may-backend/.env` 中配置它们。

## 回滚

回滚到旧镜像时，在服务器指定旧 commit SHA：

```bash
cd /opt/may-backend
IMAGE_NAME=ghcr.io/<owner>/<repo> IMAGE_TAG=<old-commit-sha> docker compose -f docker-compose.prod.yml up -d
```
