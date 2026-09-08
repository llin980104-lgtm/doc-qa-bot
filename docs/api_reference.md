# API 参考

## 基本信息

**Base URL**: `http://localhost:8000`
**API Prefix**: `/api/v1`
**Content-Type**: `application/json`

## 端点列表

### 1. 问答接口

#### 请求

```http
POST /api/v1/qa
Content-Type: application/json

{
  "query": "How to use the API?",
  "include_confidence": true,
  "include_sources": true,
  "force_llm": false
}
```

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| query | string | ✓ | 用户问题 |
| include_confidence | boolean | | 是否返回置信度（默认true） |
| include_sources | boolean | | 是否返回来源（默认true） |
| force_llm | boolean | | 强制使用LLM（默认false） |

#### 响应

```json
{
  "answer": "The API can be used by sending POST requests to /api/v1/qa with your question...",
  "layer": "small_model",
  "confidence": 0.87,
  "sources": ["docs/api_guide.md"],
  "processing_time_ms": 234,
  "llm_used": false,
  "metadata": {
    "retrieved_chunks": 3,
    "cache_hit": false
  }
}
```

#### 响应字段

| 字段 | 类型 | 描述 |
|------|------|------|
| answer | string | 生成的答案 |
| layer | string | 使用的层级（"rule", "small_model", "llm"） |
| confidence | float | 置信度评分 (0-1) |
| sources | array | 答案来源 |
| processing_time_ms | float | 处理耗时（毫秒） |
| llm_used | boolean | 是否使用了LLM |
| metadata | object | 额外元数据 |

#### 示例

```bash
curl -X POST http://localhost:8000/api/v1/qa \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Doc QA Bot?",
    "include_confidence": true
  }'
```

### 2. 添加文档接口

#### 请求

```http
POST /api/v1/documents
Content-Type: application/json

{
  "doc_id": "my-doc-1",
  "content": "This is the document content...",
  "source": "user-upload"
}
```

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| doc_id | string | ✓ | 文档唯一标识 |
| content | string | ✓ | 文档内容 |
| source | string | | 文档来源（默认"custom"） |

#### 响应

```json
{
  "status": "success",
  "message": "Document 'my-doc-1' added and indexed",
  "retriever_stats": {
    "indexed_documents": 42,
    "indexed_chunks": 256,
    "embedding_model": "distilbert-base-uncased",
    "embedding_dim": 768
  }
}
```

#### 示例

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "guide-1",
    "content": "Getting started guide...",
    "source": "documentation"
  }'
```

### 3. 反馈接口

#### 请求

```http
POST /api/v1/feedback
Content-Type: application/json

{
  "query": "How to use the API?",
  "answer": "The API can be used by...",
  "rating": 4,
  "comment": "Accurate but could be more detailed",
  "layer": "small_model"
}
```

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| query | string | ✓ | 原始问题 |
| answer | string | ✓ | 系统答案 |
| rating | integer | ✓ | 评分 (1-5) |
| comment | string | | 评论 |
| layer | string | | 答案来自哪一层 |

#### 响应

```json
{
  "status": "success",
  "message": "Feedback recorded"
}
```

#### 示例

```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to use the API?",
    "answer": "...",
    "rating": 5,
    "comment": "Very helpful"
  }'
```

### 4. 健康检查

#### 请求

```http
GET /api/v1/health
```

#### 响应

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

### 5. 系统统计

#### 请求

```http
GET /api/v1/stats
```

#### 响应

```json
{
  "general": {
    "rule_layer_hits": 1024,
    "small_model_hits": 5678,
    "llm_layer_hits": 234,
    "cache_hits": 2345,
    "total_queries": 9281
  },
  "rule_engine": {
    "total_faqs": 45,
    "total_rules": 12,
    "keywords_indexed": 156
  },
  "retriever": {
    "indexed_documents": 42,
    "indexed_chunks": 256,
    "embedding_model": "distilbert-base-uncased",
    "embedding_dim": 768
  },
  "llm": {
    "total_calls": 234,
    "total_cost": 1.25,
    "average_cost_per_call": 0.00534,
    "provider": "OpenAIProvider"
  },
  "cache": {
    "backend": "redis",
    "cache_size": 234,
    "used_memory": "125MB"
  }
}
```

## 错误处理

### 错误响应格式

```json
{
  "detail": "Error description"
}
```

### HTTP 状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 未找到答案 |
| 429 | 请求过于频繁（限流） |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

### 常见错误

#### 无效查询

```json
{
  "detail": "Query cannot be empty"
}
```

#### 未找到答案

```json
{
  "detail": "Could not find answer in knowledge base"
}
```

#### 服务不可用

```json
{
  "detail": "Retriever not initialized"
}
```

## 速率限制

默认限制：
- **100** 请求 / **60** 秒

响应头：
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1642252800
```

超限响应：
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

## 认证（可选）

如果启用 API 密钥认证：

```bash
curl -X POST http://localhost:8000/api/v1/qa \
  -H "Authorization: Bearer sk-xxxxx" \
  -d '{"query": "..."}'
```

## 批量请求

```bash
# 批量提交问题
for query in "How to?" "What is?" "Why?"; do
  curl -s -X POST http://localhost:8000/api/v1/qa \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$query\"}" &
done
wait
```

## 客户端示例

### Python

```python
import requests

def ask_question(query: str) -> dict:
    response = requests.post(
        "http://localhost:8000/api/v1/qa",
        json={"query": query}
    )
    return response.json()

result = ask_question("How to use the API?")
print(result["answer"])
print(f"Confidence: {result['confidence']}")
```

### JavaScript

```javascript
async function askQuestion(query) {
  const response = await fetch('http://localhost:8000/api/v1/qa', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query })
  });
  return response.json();
}

const result = await askQuestion('How to use the API?');
console.log(result.answer);
console.log(`Confidence: ${result.confidence}`);
```

### cURL

```bash
curl -X POST http://localhost:8000/api/v1/qa \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question here"}' | jq .
```
