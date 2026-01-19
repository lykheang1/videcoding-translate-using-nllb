# Docker Setup Guide

This project uses Docker Compose to run both the backend and frontend services.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)

## Quick Start

1. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

2. **Run in detached mode (background):**
   ```bash
   docker-compose up -d --build
   ```

3. **View logs:**
   ```bash
   # All services
   docker-compose logs -f
   
   # Backend only
   docker-compose logs -f backend
   
   # Frontend only
   docker-compose logs -f frontend
   ```

4. **Stop services:**
   ```bash
   docker-compose down
   ```

5. **Stop and remove volumes (clears model cache):**
   ```bash
   docker-compose down -v
   ```

## Services

### Backend (FastAPI)
- **Port:** 8000 (host) -> 8000 (container)
- **URL:** http://localhost:8000
- **Health Check:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs

### Frontend (Next.js)
- **Port:** 3000 (host) -> 3000 (container)
- **URL:** http://localhost:3000

## First Run

On the first run, the backend will download the NLLB-200 model (~1.2GB). This may take several minutes depending on your internet connection. The model will be cached in `./backend/models` directory.

## Environment Variables

You can customize the setup by creating a `.env` file in the root directory:

```env
# Backend
BACKEND_PORT=8000

# Frontend
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Volume Mounts

- `./backend/models` - Hugging Face model cache (persisted across restarts)

## Troubleshooting

### Port Already in Use

If ports 8000 or 4000 are already in use, modify the port mappings in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8002:8000"  # Change host port (backend)
  frontend:
    ports:
      - "3001:3000"  # Change host port (frontend)
```

### Model Download Issues

If the model download fails:
1. Check internet connection
2. Check available disk space (needs ~2GB)
3. View backend logs: `docker-compose logs backend`

### Frontend Can't Connect to Backend

If you see connection errors:
1. Ensure backend is healthy: `docker-compose ps`
2. Check backend logs: `docker-compose logs backend`
3. Verify network: `docker network inspect translate-meta_translate-network`

### Rebuild After Code Changes

After modifying code, rebuild the affected service:

```bash
# Rebuild backend
docker-compose build backend

# Rebuild frontend
docker-compose build frontend

# Rebuild everything
docker-compose build
```

## Development Mode

For development, you may want to use volume mounts for live code reloading. Create a `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  backend:
    volumes:
      - ./backend:/app
      - ./backend/models:/root/.cache/huggingface
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  frontend:
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    command: npm run dev
```

Run with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Production Deployment

For production:
1. Update environment variables
2. Use a reverse proxy (nginx/traefik) in front of services
3. Enable HTTPS/SSL
4. Set proper resource limits in `docker-compose.yml`
5. Use Docker secrets for sensitive data

Example resource limits:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```
