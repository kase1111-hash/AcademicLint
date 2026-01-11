# Self-Hosting Guide

This guide explains how to deploy AcademicLint's REST API server for institutional use.

## Docker Deployment

### Quick Start

```bash
docker run -p 8080:8080 academiclint/server:latest
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  academiclint:
    image: academiclint/server:latest
    ports:
      - "8080:8080"
    environment:
      - ACADEMICLINT_LEVEL=standard
      - ACADEMICLINT_WORKERS=4
    volumes:
      - academiclint-models:/root/.cache/academiclint
    restart: unless-stopped

volumes:
  academiclint-models:
```

Start with:

```bash
docker-compose up -d
```

## Kubernetes Deployment

### Deployment Manifest

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: academiclint
  labels:
    app: academiclint
spec:
  replicas: 3
  selector:
    matchLabels:
      app: academiclint
  template:
    metadata:
      labels:
        app: academiclint
    spec:
      containers:
      - name: academiclint
        image: academiclint/server:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /v1/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /v1/health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: model-cache
          mountPath: /root/.cache/academiclint
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: academiclint-models

---
apiVersion: v1
kind: Service
metadata:
  name: academiclint
spec:
  selector:
    app: academiclint
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: academiclint-models
spec:
  accessModes:
    - ReadOnlyMany
  resources:
    requests:
      storage: 5Gi
```

Deploy with:

```bash
kubectl apply -f deployment.yaml
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACADEMICLINT_LEVEL` | Default strictness | standard |
| `ACADEMICLINT_WORKERS` | Number of workers | 1 |
| `ACADEMICLINT_HOST` | Bind host | 0.0.0.0 |
| `ACADEMICLINT_PORT` | Bind port | 8080 |
| `ACADEMICLINT_CACHE_DIR` | Model cache directory | ~/.cache/academiclint |

### Resource Requirements

- **Memory**: 2-4GB per worker (NLP models are memory-intensive)
- **CPU**: 0.5-2 cores per worker
- **Storage**: ~2GB for models

## Security

### Authentication

For production, add authentication via a reverse proxy:

```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name academiclint.example.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        auth_basic "AcademicLint API";
        auth_basic_user_file /etc/nginx/.htpasswd;

        proxy_pass http://academiclint:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Rate Limiting

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

server {
    location /v1/check {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://academiclint:8080;
    }
}
```

## Monitoring

### Health Check

```bash
curl http://localhost:8080/v1/health
```

### Prometheus Metrics

Add a metrics endpoint using a sidecar:

```yaml
- name: metrics
  image: nginx/nginx-prometheus-exporter
  args:
    - -nginx.scrape-uri=http://localhost:8080/metrics
  ports:
    - containerPort: 9113
```

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: academiclint
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: academiclint
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```
