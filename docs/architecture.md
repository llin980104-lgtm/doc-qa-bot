# 系统架构设计

## 概述

Doc QA Bot 是一个混合模式的文档问答系统，采用三层架构：
- **Layer 1: 规则引擎** - 精确匹配
- **Layer 2: 小模型** - 向量化检索
- **Layer 3: 大模型** - LLM增强

## 架构图

```
┌─────────────────────────────────────┐
│         User Query                  │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Layer 1: Rule Engine               │
│  - Exact FAQ Matching               │
│  - Keyword Matching                 │
│  - Pattern Matching (Regex)         │
│  Latency: <10ms                     │
│  Accuracy: 100%                     │
└──────────────┬──────────────────────┘
               ↓ (if no match)
┌─────────────────────────────────────┐
│  Layer 2: Semantic Retrieval        │
│  - Document Embedding               │
│  - Similarity Search                │
│  - Confidence Scoring               │
│  Latency: <500ms                    │
│  Accuracy: 85-90%                   │
└──────────────┬──────────────────────┘
               ↓ (if confidence < threshold)
┌─────────────────────────────────────┐
│  Layer 3: LLM Enhancement           │
│  - Context-Aware Generation         │
│  - Deep Reasoning                   │
│  - Quality Improvement              │
│  Latency: 1-3s                      │
│  Accuracy: 95%+                     │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│      Response with Confidence       │
│      and Sources                    │
└─────────────────────────────────────┘
```

## 三层设计详解

### Layer 1: 规则引擎

**目的**: 快速处理确定性问题

**实现方式**:
1. **Exact Match**: 精确匹配FAQ问题
2. **Keyword Match**: 关键词匹配FAQ
3. **Pattern Match**: 正则表达式模式匹配

**配置**:
```python
RULE_CONFIDENCE_THRESHOLD = 0.95  # 规则置信度阈值
RULE_DB_PATH = "data/rules.json"  # 规则数据库路径
FAQ_DB_PATH = "data/faqs.json"    # FAQ数据库路径
```

**性能指标**:
- **延迟**: <10ms（毫秒级）
- **准确率**: 100%（精确匹配）
- **覆盖率**: 10-15%（仅处理热门问题）

### Layer 2: 小模型（向量检索）

**目的**: 处理大多数常见问题

**实现方式**:
1. **Document Chunking**: 将文档分成小块
2. **Embedding**: 使用 DistilBERT 或 Sentence Transformers 生成向量
3. **Semantic Search**: 计算查询与文档的相似度
4. **Top-K Retrieval**: 返回最相关的 K 个文档

**模型选择**:
- `distilbert-base-uncased` - 轻量级，速度快
- `sentence-transformers/all-MiniLM-L6-v2` - 更轻量
- `sentence-transformers/all-mpnet-base-v2` - 更准确

**配置**:
```python
EMBEDDING_MODEL_NAME = "distilbert-base-uncased"
RETRIEVAL_TOP_K = 5           # 返回前5个相关文档
SIMILARITY_THRESHOLD = 0.6    # 相似度阈值
CHUNK_SIZE = 512              # 文档块大小
CHUNK_OVERLAP = 50            # 块之间的重叠
```

**性能指标**:
- **延迟**: 300-500ms
- **准确率**: 85-90%
- **覆盖率**: 70-80%（处理大部分问题）

### Layer 3: 大模型增强

**目的**: 处理复杂问题和生成高质量答案

**触发条件**:
- 小模型置信度 < `LLM_TRIGGER_THRESHOLD`（默认0.65）
- 用户明确要求 `force_llm=true`
- 小模型无法检索到相关文档

**实现方式**:
1. **Context Retrieval**: 获取小模型检索的文档作为上下文
2. **Prompt Engineering**: 构造包含上下文的提示词
3. **LLM Generation**: 调用 LLM 生成答案
4. **Quality Scoring**: 评估答案质量

**配置**:
```python
LLM_ENABLE = True
LLM_PROVIDER = "openai"       # 或 "local"
LLM_MODEL = "gpt-3.5-turbo"
LLM_TRIGGER_THRESHOLD = 0.65  # 触发LLM的置信度阈值
LLM_TEMPERATURE = 0.3         # 采样温度（越低越确定）
LLM_MAX_TOKENS = 1000         # 最大输出token数
```

**性能指标**:
- **延迟**: 1-3秒
- **准确率**: 95%+
- **成本**: 每次调用 ~$0.005（GPT-3.5-turbo）
- **使用率**: 仅 5-10% 的查询需要LLM

## 置信度评分

系统使用置信度分数来决定是否路由到下一层：

```python
confidence_score = weighted_average(
    rule_match_score * 1.0,
    similarity_score * 0.8,
    source_reliability * 0.2
)

if confidence_score > RULE_CONFIDENCE_THRESHOLD:
    return rule_answer
elif confidence_score > SIMILARITY_THRESHOLD:
    return small_model_answer
elif confidence_score < LLM_TRIGGER_THRESHOLD:
    return llm_answer
else:
    return "No answer found"
```

## 缓存策略

为了优化性能，系统使用多层缓存：

### 1. 查询缓存（Query Cache）
- **后端**: Redis 或 内存
- **TTL**: 1小时（可配置）
- **命中率**: 30-50%（热门问题）

### 2. Embedding 缓存
- 缓存已编码的文档向量
- **TTL**: 7天
- **大小**: 50GB+ （根据文档量）

### 3. LLM 结果缓存
- 缓存昂贵的 LLM 调用
- **TTL**: 7天
- **成本节省**: 50%+

## 并发处理

系统使用 FastAPI 的异步特性处理并发请求：

```python
@app.post("/api/v1/qa")
async def answer_question(request: QARequest):
    # 异步处理多个查询
    # 使用连接池管理数据库/缓存连接
    # 限流防止过载
    pass
```

**性能目标**:
- **吞吐量**: 1000+ QPS（Queries Per Second）
- **P95延迟**: <1秒（包含LLM）
- **P99延迟**: <3秒

## 数据流

### 文档索引流程

```
上传文档
   ↓
预处理（清洗、分块）
   ↓
Embedding 向量化
   ↓
构建索引（Faiss / 数据库）
   ↓
缓存预热
   ↓
就绪服务
```

### 查询流程

```
用户查询
   ↓
缓存查询 ──→ 命中 → 返回结果
   ↓ 未命中
Rule Engine 匹配 ──→ 命中 → 缓存 → 返回
   ↓ 未命中
Small Model 检索 ──→ 得到结果
   ↓
置信度评分
   ├─ 高 (>0.7) → 缓存 → 返回
   └─ 低 (<0.7) → LLM 增强 → 缓存 → 返回
```

## 扩展性

### 水平扩展

1. **多实例部署**: 使用 Kubernetes 部署多个 API 实例
2. **负载均衡**: Nginx / ALB 分发请求
3. **共享缓存**: Redis 集群管理缓存
4. **分布式索引**: Elasticsearch / Milvus 存储向量

### 垂直扩展

1. **增加 GPU**: 加速 Embedding 计算
2. **优化模型**: 使用更小/更快的模型
3. **预计算**: 离线生成热点问题的答案

## 监控和告警

```python
# 关键指标
metrics = {
    'layer1_hits': 计数器,
    'layer2_hits': 计数器,
    'layer3_hits': 计数器,
    'cache_hit_rate': 仪表,
    'response_latency': 直方图,
    'llm_cost': 计数器,
    'error_rate': 仪表
}
```

## 成本优化

| 优化方法 | 效果 | 实现难度 |
|---------|------|----------|
| 缓存命中 | 减少50% LLM调用 | 简单 |
| 小模型覆盖率 | 减少80% LLM调用 | 中等 |
| 批量Embedding | 减少30% 延迟 | 简单 |
| 本地LLM | 消除API成本 | 复杂 |
| 知识蒸馏 | 更小/更快的模型 | 复杂 |
