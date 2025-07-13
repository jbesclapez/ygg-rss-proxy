# Docker Build Guide for YGG-RSS-Proxy

This guide covers the automated Docker build system for the YGG-RSS-Proxy project, including setup, usage, and troubleshooting.

## 📦 Automated Build System

The project uses GitHub Actions to automatically build and publish multi-architecture Docker images to GitHub Container Registry (GHCR).

### Available Images

- **Latest Release**: `ghcr.io/jbesclapez/ygg-rss-proxy:latest`
- **Master Branch**: `ghcr.io/jbesclapez/ygg-rss-proxy:master`
- **Develop Branch**: `ghcr.io/jbesclapez/ygg-rss-proxy:develop`
- **Tagged Releases**: `ghcr.io/jbesclapez/ygg-rss-proxy:v1.0.0` (example)

### Supported Architectures

- **AMD64** (x86_64) - Intel/AMD processors
- **ARM64** (aarch64) - ARM processors (Apple Silicon, Raspberry Pi 4+, etc.)

## 🚀 Quick Start

### Using Pre-built Images

1. **Clone the repository**:
   ```bash
   git clone https://github.com/jbesclapez/ygg-rss-proxy.git
   cd ygg-rss-proxy
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your YGG credentials and settings
   ```

3. **Start the services**:
   ```bash
   docker-compose up -d
   ```

The docker-compose.yml is configured to use the latest pre-built image from GHCR.

### Building Locally (Development)

If you need to build the image locally for development:

```bash
# Build the image
docker build -t ygg-rss-proxy:local .

# Update docker-compose.yml to use local image
# Change: image: ghcr.io/jbesclapez/ygg-rss-proxy:latest
# To:     image: ygg-rss-proxy:local

# Start services
docker-compose up -d
```

## 🔄 Build Triggers

### Automatic Builds

The CI/CD system automatically builds and publishes images when:

1. **Push to Master**: Creates `latest` and `master` tags
2. **Push to Develop**: Creates `develop` tag
3. **Release Published**: Creates `latest` and version-specific tags

### Manual Builds

You can trigger manual builds by:
- Creating a new release on GitHub
- Pushing commits to `master` or `develop` branches
- Using GitHub Actions "Re-run jobs" feature

## 📋 Build Process

### GitHub Actions Workflow

The build process includes:

1. **Multi-platform Setup**: QEMU and Docker Buildx for cross-compilation
2. **Authentication**: Automatic login to GitHub Container Registry
3. **Build & Push**: Creates images for AMD64 and ARM64 architectures
4. **Caching**: Uses GitHub Actions cache for faster builds

### Build Steps

```yaml
# Simplified workflow overview
1. Checkout code
2. Set up QEMU (for ARM64 emulation)
3. Set up Docker Buildx (for multi-platform builds)
4. Login to GHCR using GITHUB_TOKEN
5. Build and push multi-architecture images
6. Cache layers for faster subsequent builds
```

## 🐳 Image Details

### Base Image
- **Base**: `python:3.11.9-slim-bullseye`
- **Package Manager**: Poetry
- **Port**: 8080 (configurable via `GUNICORN_PORT`)

### Image Layers
1. Python base image
2. Poetry installation
3. Dependencies installation
4. Application code
5. Configuration and entrypoint

### Environment Variables

The Docker image supports all environment variables from `.env.example`:

```bash
# Core Configuration
YGG_USER=your_username
YGG_PASS=your_password
FLARESOLVERR_HOST=flaresolverr
RSS_HOST=ygg-rss-proxy

# Optional Configuration
LOG_LEVEL=INFO
GUNICORN_PORT=8080
GUNICORN_WORKERS=1
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Image Pull Failures

**Error**: `Error response from daemon: pull access denied`

**Solution**:
```bash
# The image may not be public yet. Log in to GHCR:
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Or build locally:
docker build -t ygg-rss-proxy:local .
```

#### 2. Architecture Mismatch

**Error**: `exec format error` or `no matching manifest`

**Solution**:
```bash
# Pull specific architecture
docker pull --platform linux/amd64 ghcr.io/jbesclapez/ygg-rss-proxy:latest

# Or let Docker auto-detect
docker pull ghcr.io/jbesclapez/ygg-rss-proxy:latest
```

#### 3. Build Cache Issues

**Error**: Build fails with dependency errors

**Solution**:
```bash
# Clear Docker build cache
docker builder prune -a

# Or build without cache
docker build --no-cache -t ygg-rss-proxy:local .
```

#### 4. Environment Configuration

**Error**: Container starts but functionality doesn't work

**Solution**:
```bash
# Check environment variables
docker-compose exec ygg-rss-proxy env | grep -E "(YGG|FLARE|RSS)"

# Check logs
docker-compose logs ygg-rss-proxy
docker-compose logs flaresolverr
```

### Debug Mode

Enable debug logging:

```bash
# In .env file
LOG_LEVEL=DEBUG

# Restart services
docker-compose down
docker-compose up -d

# View detailed logs
docker-compose logs -f ygg-rss-proxy
```

## 🔒 Security Considerations

### Authentication

- Uses `GITHUB_TOKEN` for secure authentication
- No personal access tokens required
- Automatic token management by GitHub Actions

### Image Security

- Based on official Python slim images
- Regular dependency updates via Dependabot
- No unnecessary packages or tools included

### Environment Variables

- Never commit sensitive data to repository
- Use `.env` file for local development
- Use Docker secrets for production deployments

## 📊 Monitoring Build Status

### GitHub Actions

Check build status at:
- Repository → Actions tab
- Latest workflow runs
- Build logs and artifacts

### Image Registry

View published images at:
- `https://github.com/jbesclapez/ygg-rss-proxy/pkgs/container/ygg-rss-proxy`

## 🔄 Update Process

### For Users

1. **Pull latest image**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

2. **Check for updates**:
   ```bash
   # Compare local and remote image
   docker images ghcr.io/jbesclapez/ygg-rss-proxy
   ```

### For Developers

1. **Commit changes to develop branch**
2. **Test with develop image**
3. **Merge to master for stable release**
4. **Create GitHub release for versioned image**

## 📝 Advanced Configuration

### Custom Image Tags

```yaml
# docker-compose.override.yml
version: "3.8"
services:
  ygg-rss-proxy:
    image: ghcr.io/jbesclapez/ygg-rss-proxy:develop  # Use develop branch
```

### Health Checks

```yaml
# Add to docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Resource Limits

```yaml
# Add to docker-compose.yml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

## 🆘 Getting Help

1. **Check GitHub Issues**: Known problems and solutions
2. **Review Logs**: Container and application logs
3. **Community Support**: GitHub Discussions
4. **Documentation**: README.md and inline code comments

---

**Last Updated**: $(date)
**Repository**: https://github.com/jbesclapez/ygg-rss-proxy
**Registry**: https://ghcr.io/jbesclapez/ygg-rss-proxy 