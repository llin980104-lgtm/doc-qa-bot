# 部署指南

## 前置要求

- Python 3.8+
- Docker & Docker Compose（可选）
- GPU（可选，用于加速embedding）
- Redis（可选，用于缓存）
- OpenAI API Key（可选，用于LLM）

## 本地部署

### 1. 克隆仓库

```bash
git clone https://github.com/llin980104-lgtm/doc-qa-bot.git
cd doc-qa-bot
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制模板
cp ../.env.example ../.env

# 编辑 .env 文件
vim ../.env
```

必须配置的环境变量：
- `OPENAI_API_KEY`: 如果使用 OpenAI
- `REDIS_URL`: 如果使用 Redis 缓存
- `EMBEDDING_DEVICE`: "cpu" 或 "cuda"

### 5. 启动服务

```bash
python app.py
```

访问 API:
- 主页: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/v1/health

## Docker 部署

### 1. 构建镜像

```bash
cd docker
docker build -t doc-qa-bot:latest .
```

### 2. 运行容器

```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-xxx \
  -v $(pwd)/data:/app/data \
  --name doc-qa-bot \
  doc-qa-bot:latest
```

### 3. 查看日志

```bash
docker logs -f doc-qa-bot
```

## Docker Compose 部署（推荐）

### 1. 配置环境

```bash
cp .env.example .env
vim .env
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 检查服务状态

```bash
docker-compose ps

# 输出示例
NAME       COMMAND                  STATE           PORTS
api        python app.py            Up (healthy)    0.0.0.0:8000->8000/tcp
redis      redis-server --append... Up              0.0.0.0:6379->6379/tcp
```

### 4. 停止服务

```bash
docker-compose down
```

## Kubernetes 部署

### 1. 创建命名空间

```bash
kubectl create namespace doc-qa
```

### 2. 创建配置和密钥

```bash
kubectl create configmap doc-qa-config \
  --from-file=.env \
  -n doc-qa

kubectl create secret generic doc-qa-secrets \
  --from-literal=openai-api-key=sk-xxx \
  -n doc-qa
```

### 3. 应用 Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: doc-qa-api
  namespace: doc-qa
spec:
  replicas: 3
  selector:
    matchLabels:
      app: doc-qa-api
  template:
    metadata:
      labels:
        app: doc-qa-api
    spec:
      containers:
      - name: api
        image: doc-qa-bot:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: doc-qa-secrets
              key: openai-api-key
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

```bash
kubectl apply -f k8s/deployment.yaml
```

### 4. 创建 Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: doc-qa-api
  namespace: doc-qa
spec:
  selector:
    app: doc-qa-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

```bash
kubectl apply -f k8s/service.yaml
kubectl get svc doc-qa-api -n doc-qa
```

## 性能优化

### 1. 启用 GPU 加速

```bash
# .env
EMBEDDING_DEVICE=cuda
```

```bash
# Docker
docker run --gpus all -d doc-qa-bot:latest
```

### 2. 预热缓存

```python
# scripts/warmup_cache.py
from backend.modules.embedding_model import EmbeddingModel
from backend.modules.retrieval import SemanticRetriever

retriever = SemanticRetriever()
retriever.index_documents()  # 预计算所有向量
```

```bash
python scripts/warmup_cache.py
```

### 3. 使用更小的模型

```bash
# .env
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

### 4. 启用 Redis 集群

```bash
# .env
CACHE_BACKEND=redis
REDIS_URL=redis://redis-cluster:6379/0
```

## 监控和日志

### 1. Prometheus 指标

```bash
# 访问指标
curl http://localhost:8000/metrics
```

### 2. 日志收集

```bash
# Docker 日志
docker logs -f doc-qa-bot

# Kubernetes 日志
kubectl logs -f deploy/doc-qa-api -n doc-qa

# 日志文件（如果配置）
tail -f logs/doc-qa.log
```

### 3. Grafana 仪表板

```bash
# 启动 Grafana
docker run -d -p 3000:3000 grafana/grafana

# 访问 http://localhost:3000
# 默认用户/密码: admin/admin
```

## 常见问题

### Q: 如何更新文档？

```bash
# 添加新文档
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "my-doc",
    "content": "Document content here",
    "source": "user-upload"
  }'
```

### Q: 如何重新索引所有文档？

```python
# scripts/reindex.py
from backend.modules.retrieval import SemanticRetriever

retriever = SemanticRetriever()
retriever.index_documents(rebuild=True)
```

### Q: 如何清空缓存？

```bash
# Redis
redis-cli FLUSHDB

# API 端点
curl -X POST http://localhost:8000/api/v1/cache/clear
```

## 性能基准

在标准配置下的性能指标：

| 操作 | P50 | P95 | P99 |
|------|-----|-----|-----|
| 规则匹配 | 5ms | 10ms | 15ms |
| 小模型检索 | 200ms | 350ms | 500ms |
| LLM生成 | 1.5s | 2.5s | 3.5s |
| 缓存命中 | 1ms | 2ms | 5ms |

## 安全建议

1. **使用 HTTPS**
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:8000;
       }
   }
   ```

2. **API 认证**
   ```python
   # 添加 API Key 认证
   API_KEYS = ["key1", "key2"]
   ```

3. **速率限制**
   ```python
   # .env
   RATE_LIMIT_ENABLE=true
   RATE_LIMIT_REQUESTS=100
   RATE_LIMIT_WINDOW=60
   ```

4. **CORS 配置**
   ```python
   # 限制允许的来源
   CORS_ORIGINS=["https://example.com"]
   ```
