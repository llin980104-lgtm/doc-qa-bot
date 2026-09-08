"""
MES 系统集成指南 - Doc QA Bot 定制化方案

本文档详细说明如何将 Doc QA Bot 集成到制造执行系统(MES)中
"""

# ============================================
# 1. MES 应用场景分析
# ============================================

## MES 中的典型问题类型

### 工艺流程相关
- "第一道工序是什么?"
- "产品A的加工时间是多少?"
- "质检标准怎么规定?"
- "设备BOM是什么?"

### 生产计划相关
- "今天的生产计划?"
- "订单ABC的交期?"
- "产能如何计算?"
- "优先级排序规则?"

### 质量管理相关
- "不良品如何处理?"
- "质检流程是?"
- "偏差如何上报?"
- "追溯代码生成规则?"

### 设备维护相关
- "设备保养周期?"
- "故障代码E001表示什么?"
- "换型时间?"
- "工具寿命?"

### 人员管理相关
- "工人权限是什么?"
- "绩效如何评算?"
- "岗位职责?"
- "培训要求?"

---

# ============================================
# 2. MES 数据源集成
# ============================================

## A. 数据导入方案

### 方案A: 从 MES 数据库直接读取

```python
# backend/modules/mes_integration.py
from sqlalchemy import create_engine
from typing import List, Dict

class MESDataConnector:
    """MES数据库连接器"""
    
    def __init__(self, mes_db_url: str):
        """
        mes_db_url: MES数据库连接字符串
        例: "mysql+pymysql://user:pass@localhost/mes_db"
        """
        self.engine = create_engine(mes_db_url)
    
    def get_process_docs(self) -> List[Dict]:
        """从工艺表获取文档"""
        query = """
        SELECT process_id, process_name, process_desc, 
               work_time, standard_time
        FROM t_process
        WHERE status = 'active'
        """
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [dict(row) for row in result.fetchall()]
    
    def get_equipment_docs(self) -> List[Dict]:
        """从设备表获取文档"""
        query = """
        SELECT equip_id, equip_name, model, 
               specifications, maintenance_cycle
        FROM t_equipment
        WHERE status = 'active'
        """
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [dict(row) for row in result.fetchall()]
    
    def get_quality_standards(self) -> List[Dict]:
        """从质检标准表获取文档"""
        query = """
        SELECT standard_id, product_code, 
               check_items, acceptance_criteria
        FROM t_quality_standard
        WHERE status = 'active'
        """
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [dict(row) for row in result.fetchall()]
    
    def get_production_orders(self, days: int = 7) -> List[Dict]:
        """获取最近N天的生产订单"""
        query = """
        SELECT order_id, product_code, quantity, 
               due_date, status, priority
        FROM t_production_order
        WHERE order_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
        ORDER BY due_date ASC
        """
        with self.engine.connect() as conn:
            result = conn.execute(query, (days,))
            return [dict(row) for row in result.fetchall()]
    
    def get_equipment_faults(self, days: int = 30) -> List[Dict]:
        """获取设备故障历史"""
        query = """
        SELECT fault_id, equip_id, fault_code, 
               fault_desc, solution, resolution_time
        FROM t_equipment_fault
        WHERE fault_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
        ORDER BY fault_date DESC
        """
        with self.engine.connect() as conn:
            result = conn.execute(query, (days,))
            return [dict(row) for row in result.fetchall()]
```

### 方案B: 从 MES API 获取

```python
# backend/modules/mes_api_client.py
import requests
from typing import List, Dict
import json

class MESAPIClient:
    """MES API 客户端"""
    
    def __init__(self, api_url: str, api_key: str):
        """
        api_url: MES API 基础URL
        api_key: API 认证密钥
        """
        self.api_url = api_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_process_list(self) -> List[Dict]:
        """获取工艺流程列表"""
        response = requests.get(
            f"{self.api_url}/api/processes",
            headers=self.headers,
            params={"status": "active"}
        )
        return response.json().get("data", [])
    
    def get_process_detail(self, process_id: str) -> Dict:
        """获取工艺详情"""
        response = requests.get(
            f"{self.api_url}/api/processes/{process_id}",
            headers=self.headers
        )
        return response.json().get("data", {})
    
    def get_current_orders(self) -> List[Dict]:
        """获取当前生产订单"""
        response = requests.get(
            f"{self.api_url}/api/orders/current",
            headers=self.headers
        )
        return response.json().get("data", [])
    
    def get_equipment_status(self, equip_id: str = None) -> Dict:
        """获取设备状态"""
        params = {"equip_id": equip_id} if equip_id else {}
        response = requests.get(
            f"{self.api_url}/api/equipment/status",
            headers=self.headers,
            params=params
        )
        return response.json().get("data", {})
```

### 方案C: 定��同步 CSV/Excel

```python
# backend/modules/mes_data_sync.py
import pandas as pd
from pathlib import Path
from typing import List, Dict

class MESDataSync:
    """从CSV/Excel同步MES数据"""
    
    def __init__(self, data_dir: str = "data/mes"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def import_process_data(self, csv_file: str) -> List[Dict]:
        """导入工艺数据"""
        df = pd.read_csv(csv_file)
        # 数据清洗和转换
        data = []
        for _, row in df.iterrows():
            data.append({
                'process_id': row['工艺编号'],
                'process_name': row['工艺名称'],
                'description': row['工艺描述'],
                'work_time': row['标准工时'],
                'equipment': row['使用设备'],
                'material': row['使用材料'],
                'quality_check': row['质检要求']
            })
        return data
    
    def import_equipment_data(self, excel_file: str) -> List[Dict]:
        """导入设备数据"""
        df = pd.read_excel(excel_file, sheet_name='设备清单')
        data = []
        for _, row in df.iterrows():
            data.append({
                'equipment_id': row['设备编号'],
                'equipment_name': row['设备名称'],
                'model': row['型号'],
                'specifications': row['规格参数'],
                'maintenance_cycle': row['保养周期'],
                'last_maintenance': row['最后保养日期'],
                'fault_code_guide': row['故障代码说明']
            })
        return data
    
    def import_quality_standards(self, excel_file: str) -> List[Dict]:
        """导入质检标准"""
        df = pd.read_excel(excel_file, sheet_name='质检标准')
        data = []
        for _, row in df.iterrows():
            data.append({
                'product_code': row['产品代码'],
                'check_items': row['检查项目'].split(','),
                'acceptance_criteria': row['验收标准'],
                'inspection_method': row['检验方法'],
                'sampling_rate': row['取样率']
            })
        return data
```

---

# ============================================
# 3. 自定义规则库和 FAQ
# ============================================

## A. MES 专用 FAQ

```json
{
  "mes_faq_1": {
    "questions": [
      "生产流程是什么?",
      "产品如何生产?",
      "工艺流程?"
    ],
    "answer": "产品ABC的生产流程包括：\n1. 原料检验 (2小时)\n2. 前处理 (4小时)\n3. 主加工 (8小时)\n4. 质量检验 (2小时)\n5. 包装入库 (1小时)\n总工时：17小时",
    "keywords": ["生产流程", "工艺", "生产步骤"],
    "source": "MES-ProcessDocs",
    "category": "工艺管理",
    "product_code": "ABC-001",
    "update_time": "2024-01-15"
  },
  
  "mes_faq_2": {
    "questions": [
      "设备E001故障代码是什么?",
      "E001什么意思?",
      "设备出现E001错误"
    ],
    "answer": "设备E001故障代码含义：\n- 故障原因：主轴温度过高\n- 处理步骤：\n  1. 停止生产\n  2. 检查冷却液\n  3. 清理散热片\n  4. 冷却后重启\n- 若仍未解决，请联系维修部",
    "keywords": ["故障", "E001", "设备"],
    "source": "MES-EquipmentGuide",
    "category": "设备维护",
    "equipment_id": "E001",
    "severity": "high"
  },

  "mes_faq_3": {
    "questions": [
      "今天的生产计划是什么?",
      "今日订单?",
      "生产安排?"
    ],
    "answer": "今日生产计划（动态更新）：\n生产订单号 | 产品代码 | 数量 | 优先级 | 截止时间\nORD-2024-001 | ABC-001 | 1000 | 高 | 16:00\nORD-2024-002 | XYZ-002 | 500 | 中 | 18:00\nORD-2024-003 | PQR-003 | 200 | 低 | 明天\n\n点击订单号查看详细信息。",
    "keywords": ["生产计划", "订单", "生产安排"],
    "source": "MES-ProductionPlan",
    "category": "生产计划",
    "is_dynamic": true,
    "update_interval": 300  # 5分钟更新一次
  }
}
```

## B. MES 专用规则库

```json
{
  "rules": {
    "patterns": [
      {
        "pattern": "设备.*出现|报错|故障|异常",
        "handler": "get_equipment_fault_guide",
        "answer_template": "设备${equipment}出现${fault_code}故障\n故障原因：${reason}\n解决步骤：${steps}\n联系方式：${contact}",
        "source": "equipment",
        "confidence": 0.95
      },
      {
        "pattern": "产品.*生产|工艺|流程|步骤",
        "handler": "get_process_flow",
        "answer_template": "产品${product_code}的生产流程：\n${flow_steps}\n预计工时：${work_time}\n负责部门：${department}",
        "source": "process",
        "confidence": 0.90
      },
      {
        "pattern": "质检.*标准|要求|检验|检查",
        "handler": "get_quality_standards",
        "answer_template": "产品${product_code}的质检标准：\n检查项目：${check_items}\n验收标准：${criteria}\n检验方法：${method}",
        "source": "quality",
        "confidence": 0.92
      },
      {
        "pattern": "订单|计划|生产安排|产能",
        "handler": "get_production_plan",
        "answer_template": "订单${order_id}信息：\n产品：${product_code}\n数量：${quantity}\n优先级：${priority}\n截止时间：${due_date}\n当前进度：${progress}",
        "source": "production",
        "confidence": 0.88,
        "is_dynamic": true,
        "cache_ttl": 300
      }
    ]
  }
}
```

---

# ============================================
# 4. 实时数据查询集成
# ============================================

## A. 实时 Handler 示例

```python
# backend/modules/mes_handlers.py
from typing import Dict, Any
from modules.mes_api_client import MESAPIClient
from config import settings

class MESDataHandlers:
    """MES 实时数据处理器"""
    
    def __init__(self, mes_client: MESAPIClient):
        self.client = mes_client
    
    def get_production_plan(self, order_id: str = None) -> Dict:
        """获取生产计划"""
        orders = self.client.get_current_orders()
        
        if order_id:
            order = next((o for o in orders if o['id'] == order_id), None)
            if order:
                return self._format_order(order)
        
        # 返回今日计划
        return {
            "today_orders": [self._format_order(o) for o in orders],
            "total_count": len(orders),
            "high_priority": len([o for o in orders if o['priority'] == 'high'])
        }
    
    def get_equipment_status(self, equipment_id: str = None) -> Dict:
        """获取设备状态"""
        status = self.client.get_equipment_status(equipment_id)
        
        return {
            "equipment_id": status.get('id'),
            "equipment_name": status.get('name'),
            "current_status": status.get('status'),  # running/idle/fault
            "current_order": status.get('current_order'),
            "utilization_rate": status.get('utilization_rate'),
            "last_maintenance": status.get('last_maintenance'),
            "fault_history": status.get('recent_faults', [])[:5]  # 最近5条故障
        }
    
    def get_process_flow(self, product_code: str) -> Dict:
        """获取产品工艺流程"""
        process = self.client.get_process_detail(product_code)
        
        steps = []
        for i, step in enumerate(process.get('steps', []), 1):
            steps.append({
                "step_no": i,
                "process_name": step['name'],
                "equipment": step.get('equipment'),
                "standard_time": step.get('work_time'),
                "quality_check": step.get('quality_check'),
                "material": step.get('material')
            })
        
        return {
            "product_code": product_code,
            "product_name": process.get('name'),
            "steps": steps,
            "total_time": process.get('total_time'),
            "department": process.get('department')
        }
    
    def get_quality_standards(self, product_code: str) -> Dict:
        """获取质检标准"""
        standards = self.client.get_quality_standards(product_code)
        
        return {
            "product_code": product_code,
            "check_items": standards.get('check_items', []),
            "acceptance_criteria": standards.get('criteria'),
            "inspection_method": standards.get('method'),
            "sampling_rate": standards.get('sampling_rate'),
            "document_url": standards.get('document_url')
        }
    
    def get_fault_guide(self, equipment_id: str, fault_code: str) -> Dict:
        """获取设备故障处理指南"""
        # 从 MES 数据库查询故障指南
        fault_guides = {
            "E001": {
                "name": "主轴温度过高",
                "cause": "冷却液不足或散热片堵塞",
                "steps": [
                    "停止生产",
                    "检查冷却液液位",
                    "清理散热片",
                    "冷却后重启"
                ],
                "contact": "维修部: 0571-8888-8888"
            },
            "E002": {
                "name": "压力异常",
                "cause": "液压泵故障或油路堵塞",
                "steps": [
                    "检查油位",
                    "清理油路过滤器",
                    "启动检测程序",
                    "必要时更换液压泵"
                ],
                "contact": "维修部: 0571-8888-8888"
            }
        }
        
        guide = fault_guides.get(fault_code)
        if not guide:
            return {"error": f"未找到故障代码{fault_code}的处理指南"}
        
        return {
            "equipment_id": equipment_id,
            "fault_code": fault_code,
            "fault_name": guide['name'],
            "cause": guide['cause'],
            "resolution_steps": guide['steps'],
            "contact_info": guide['contact'],
            "estimated_time": "2小时"
        }
    
    @staticmethod
    def _format_order(order: Dict) -> Dict:
        """格式化订单信息"""
        return {
            "order_id": order.get('id'),
            "product_code": order.get('product_code'),
            "product_name": order.get('product_name'),
            "quantity": order.get('quantity'),
            "priority": order.get('priority'),
            "status": order.get('status'),
            "progress": order.get('progress', 0),
            "due_date": order.get('due_date'),
            "assigned_equipment": order.get('assigned_equipment')
        }
```

## B. 集成到规则引擎

```python
# 在 app.py 中的 startup_event 中添加
@app.on_event("startup")
async def startup_event():
    global rule_engine, mes_handlers
    
    # ... 原有代码 ...
    
    # 初始化 MES 集成
    if settings.MES_ENABLE:
        mes_client = MESAPIClient(
            api_url=settings.MES_API_URL,
            api_key=settings.MES_API_KEY
        )
        mes_handlers = MESDataHandlers(mes_client)
        logger.info("MES integration initialized")
```

---

# ============================================
# 5. 环境变量配置
# ============================================

## .env 中的 MES 配置

```bash
# ===== MES 集成 =====
MES_ENABLE=true
MES_INTEGRATION_TYPE=api  # api / database / csv

# MES API 配置
MES_API_URL=http://mes.example.com:8080
MES_API_KEY=your-mes-api-key
MES_API_TIMEOUT=30

# MES 数据库配置（可选）
MES_DB_TYPE=mysql  # mysql / postgresql / sqlserver
MES_DB_HOST=localhost
MES_DB_PORT=3306
MES_DB_NAME=mes_database
MES_DB_USER=mes_user
MES_DB_PASSWORD=mes_password

# MES 数据同步
MES_DATA_SYNC_INTERVAL=600  # 10分钟同步一次
MES_DATA_CACHE_TTL=3600     # 1小时缓存

# MES 特定功能
MES_ENABLE_REAL_TIME_ORDERS=true    # 实时订单更新
MES_ENABLE_EQUIPMENT_MONITORING=true # 设备监控
MES_ENABLE_FAULT_PREDICTION=false    # 故障预测（可选）
```

---

# ============================================
# 6. 会话上下文管理
# ============================================

## 用户工作环境注入

```python
# backend/modules/mes_context.py
from typing import Optional, Dict, Any
from pydantic import BaseModel

class MESUserContext(BaseModel):
    """MES 用户会话上下文"""
    user_id: str
    username: str
    department: str           # 部门
    role: str                # 角色：operator/supervisor/manager/engineer
    current_equipment: Optional[str]  # 当前操作的设备
    current_order: Optional[str]      # 当前生产订单
    shift: str               # 班次：morning/afternoon/night
    permissions: list        # 权限列表

class ContextAwareQARequest(BaseModel):
    """上下文感知的问答请求"""
    query: str
    user_context: MESUserContext
    include_confidence: bool = True
    include_sources: bool = True
    force_llm: bool = False

# 在 app.py 中使用
@app.post(f"{settings.API_PREFIX}/qa")
async def answer_question_with_context(request: ContextAwareQARequest):
    """支持 MES 用户上下文的问答接口"""
    
    # 根据用户上下文增强查询
    enhanced_query = f"""
    用户：{request.user_context.username} ({request.user_context.role})
    部门：{request.user_context.department}
    当前设备：{request.user_context.current_equipment or 'N/A'}
    当前订单：{request.user_context.current_order or 'N/A'}
    班次：{request.user_context.shift}
    
    原始问题：{request.query}
    """
    
    # 如果是设备相关问题，自动注入当前设备信息
    if request.user_context.current_equipment and any(
        keyword in request.query 
        for keyword in ['设备', '故障', '维护', '状态']
    ):
        equipment_status = mes_handlers.get_equipment_status(
            request.user_context.current_equipment
        )
        enhanced_query += f"\n\n设备当前状态：{equipment_status}"
    
    # 如果是订单相关问题，自动注入当前订单信息
    if request.user_context.current_order and any(
        keyword in request.query 
        for keyword in ['订单', '进度', '计划', '交期']
    ):
        plan = mes_handlers.get_production_plan(
            request.user_context.current_order
        )
        enhanced_query += f"\n\n订单信息：{plan}"
    
    # 执行增强后的查询
    return await answer_question(
        QARequest(query=enhanced_query)
    )
```

---

# ============================================
# 7. 权限和审计
# ============================================

## A. 角色权限控制

```python
# backend/modules/mes_permissions.py
from enum import Enum
from typing import List, Set

class MESRole(str, Enum):
    """MES 角色定义"""
    OPERATOR = "operator"        # 操作员：查看自己的工作
    SUPERVISOR = "supervisor"    # 主管：查看班组内容
    MANAGER = "manager"          # 经理：查看部门内容
    ENGINEER = "engineer"        # 工程师：查看全厂内容
    ADMIN = "admin"              # 管理员：全部权限

class MESPermissions:
    """MES 权限矩阵"""
    
    PERMISSIONS = {
        MESRole.OPERATOR: {
            "view_own_orders": True,
            "view_own_equipment": True,
            "view_process_docs": True,
            "view_quality_standards": True,
            "view_faults": False,  # 不能查看全厂故障
            "export_data": False,
            "modify_plans": False
        },
        MESRole.SUPERVISOR: {
            "view_own_orders": True,
            "view_team_orders": True,
            "view_own_equipment": True,
            "view_team_equipment": True,
            "view_process_docs": True,
            "view_quality_standards": True,
            "view_faults": True,  # 可以查看班组故障
            "export_data": True,
            "modify_plans": False
        },
        MESRole.MANAGER: {
            "view_own_orders": True,
            "view_dept_orders": True,
            "view_own_equipment": True,
            "view_dept_equipment": True,
            "view_process_docs": True,
            "view_quality_standards": True,
            "view_faults": True,
            "export_data": True,
            "modify_plans": True   # 可以修改部门计划
        },
        MESRole.ENGINEER: {
            "view_own_orders": True,
            "view_all_orders": True,
            "view_own_equipment": True,
            "view_all_equipment": True,
            "view_process_docs": True,
            "view_quality_standards": True,
            "view_faults": True,
            "export_data": True,
            "modify_plans": True
        },
        MESRole.ADMIN: {
            "view_own_orders": True,
            "view_all_orders": True,
            "view_own_equipment": True,
            "view_all_equipment": True,
            "view_process_docs": True,
            "view_quality_standards": True,
            "view_faults": True,
            "export_data": True,
            "modify_plans": True,
            "manage_users": True,
            "manage_system": True
        }
    }
    
    @staticmethod
    def has_permission(role: MESRole, permission: str) -> bool:
        """检查角色是否有权限"""
        return MESPermissions.PERMISSIONS.get(role, {}).get(permission, False)
    
    @staticmethod
    def filter_by_permission(
        data: List[Dict],
        role: MESRole,
        permission: str
    ) -> List[Dict]:
        """根据权限过滤数据"""
        if not MESPermissions.has_permission(role, permission):
            return []
        return data

# 在中间件中添加权限检查
@app.middleware("http")
async def check_mes_permissions(request: Request, call_next):
    """检查 MES 权限"""
    user_role = request.headers.get("X-User-Role")
    endpoint = request.url.path
    
    # 权限检查逻辑
    if not MESPermissions.has_permission(
        MESRole(user_role),
        get_permission_for_endpoint(endpoint)
    ):
        return JSONResponse(
            status_code=403,
            content={"detail": "Insufficient permissions"}
        )
    
    return await call_next(request)
```

## B. 审计日志

```python
# backend/modules/mes_audit.py
import json
from datetime import datetime
from typing import Any

class MESAuditLogger:
    """MES 审计日志"""
    
    @staticmethod
    def log_query(
        user_id: str,
        query: str,
        result: Any,
        response_time: float,
        layer_used: str
    ):
        """记录查询请求"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": "query",
            "query": query,
            "layer_used": layer_used,
            "response_time_ms": response_time,
            "result_length": len(str(result)),
            "status": "success"
        }
        
        # 保存到审计日志文件或数据库
        save_audit_log(audit_entry)
        logger.info(f"Query audit: {audit_entry}")
    
    @staticmethod
    def log_data_modification(
        user_id: str,
        action: str,  # create/update/delete
        table: str,
        record_id: str,
        changes: dict
    ):
        """记录数据修改"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "table": table,
            "record_id": record_id,
            "changes": changes,
            "status": "success"
        }
        
        save_audit_log(audit_entry)
        logger.warning(f"Data modification audit: {audit_entry}")
    
    @staticmethod
    def log_error(
        user_id: str,
        query: str,
        error: str,
        error_type: str
    ):
        """记录错误"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "query": query,
            "error": error,
            "error_type": error_type,
            "status": "error"
        }
        
        save_audit_log(audit_entry)
        logger.error(f"Error audit: {audit_entry}")
```

---

# ============================================
# 8. 完整集成示例
# ============================================

## MES 专用 FastAPI 应用

```python
# backend/mes_app.py
from fastapi import FastAPI, Depends, Header
from typing import Optional
from modules.mes_integration import MESDataConnector
from modules.mes_handlers import MESDataHandlers
from modules.mes_permissions import MESPermissions, MESRole
from modules.mes_audit import MESAuditLogger

# 创建 MES 专用应用
mes_app = FastAPI(
    title="Doc QA Bot for MES",
    version="1.0.0",
    description="制造执行系统专用问答机器人"
)

# 初始化 MES 数据连接
mes_connector = MESDataConnector(settings.MES_DB_URL)
mes_handlers = MESDataHandlers(mes_connector)

# 定义当前用户依赖
async def get_current_user(
    x_user_id: str = Header(...),
    x_user_role: str = Header(...)
) -> MESUserContext:
    """从请求头获取用户信息"""
    return MESUserContext(
        user_id=x_user_id,
        username=x_user_id,  # 实际应从数据库查询
        department="Production",
        role=x_user_role,
        current_equipment=None,
        current_order=None,
        shift="morning"
    )

# MES 专用问答端点
@mes_app.post("/api/v1/mes/qa")
async def mes_answer_question(
    request: ContextAwareQARequest,
    current_user: MESUserContext = Depends(get_current_user)
):
    """MES 问答接口"""
    
    start_time = time.time()
    
    try:
        # 权限检查
        if not MESPermissions.has_permission(
            MESRole(current_user.role),
            "view_process_docs"
        ):
            return {"error": "权限不足"}
        
        # 执行查询
        response = await answer_question(request)
        
        # 审计日志
        MESAuditLogger.log_query(
            user_id=current_user.user_id,
            query=request.query,
            result=response,
            response_time=(time.time() - start_time) * 1000,
            layer_used=response.layer
        )
        
        return response
    
    except Exception as e:
        MESAuditLogger.log_error(
            user_id=current_user.user_id,
            query=request.query,
            error=str(e),
            error_type=type(e).__name__
        )
        raise

# MES 数据接口
@mes_app.get("/api/v1/mes/production/plan")
async def get_production_plan(
    current_user: MESUserContext = Depends(get_current_user)
):
    """获取生产计划"""
    return mes_handlers.get_production_plan()

@mes_app.get("/api/v1/mes/equipment/{equipment_id}/status")
async def get_equipment_status(
    equipment_id: str,
    current_user: MESUserContext = Depends(get_current_user)
):
    """获取设备状态"""
    return mes_handlers.get_equipment_status(equipment_id)

@mes_app.get("/api/v1/mes/process/{product_code}")
async def get_process_flow(
    product_code: str,
    current_user: MESUserContext = Depends(get_current_user)
):
    """获取工艺流程"""
    return mes_handlers.get_process_flow(product_code)

@mes_app.get("/api/v1/mes/quality/{product_code}")
async def get_quality_standards(
    product_code: str,
    current_user: MESUserContext = Depends(get_current_user)
):
    """获取质检标准"""
    return mes_handlers.get_quality_standards(product_code)

@mes_app.get("/api/v1/mes/equipment/{equipment_id}/fault/{fault_code}")
async def get_fault_guide(
    equipment_id: str,
    fault_code: str,
    current_user: MESUserContext = Depends(get_current_user)
):
    """获取故障处理指南"""
    return mes_handlers.get_fault_guide(equipment_id, fault_code)
```

---

# ============================================
# 9. 前端集成示例
# ============================================

## MES 中的聊天机器人界面

```html
<!-- mes_qa_widget.html -->
<!DOCTYPE html>
<html>
<head>
    <title>MES 智能助手</title>
    <style>
        .qa-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 400px;
            height: 600px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        .qa-messages {
            height: 500px;
            overflow-y: auto;
            padding: 10px;
        }
        .qa-input {
            display: flex;
            padding: 10px;
            border-top: 1px solid #ddd;
        }
        .message {
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .user-message {
            background: #e3f2fd;
            text-align: right;
        }
        .bot-message {
            background: #f5f5f5;
        }
    </style>
</head>
<body>
    <div class="qa-widget">
        <div class="qa-messages" id="messages"></div>
        <div class="qa-input">
            <input 
                type="text" 
                id="queryInput" 
                placeholder="请输入问题..."
                style="flex: 1; padding: 8px;"
            />
            <button onclick="sendQuery()" style="padding: 8px 15px;">发送</button>
        </div>
    </div>

    <script>
        // 从 MES session 获取用户信息
        const userId = localStorage.getItem('mes_user_id');
        const userRole = localStorage.getItem('mes_user_role');

        async function sendQuery() {
            const query = document.getElementById('queryInput').value;
            if (!query) return;

            // 显示用户消息
            addMessage(query, 'user');
            document.getElementById('queryInput').value = '';

            try {
                // 调用 Doc QA Bot API
                const response = await fetch('http://localhost:8000/api/v1/mes/qa', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-User-Id': userId,
                        'X-User-Role': userRole
                    },
                    body: JSON.stringify({
                        query: query,
                        user_context: {
                            user_id: userId,
                            role: userRole,
                            department: localStorage.getItem('mes_department'),
                            current_equipment: localStorage.getItem('mes_current_equipment')
                        }
                    })
                });

                const data = await response.json();
                
                // 格式化并显示答案
                let message = data.answer;
                if (data.confidence) {
                    message += `\n\n[置信度: ${(data.confidence * 100).toFixed(0)}%] [来源: ${data.layer}]`;
                }
                if (data.sources && data.sources.length > 0) {
                    message += `\n参考资料: ${data.sources.join(', ')}`;
                }
                
                addMessage(message, 'bot');
            } catch (error) {
                addMessage(`错误: ${error.message}`, 'bot');
            }
        }

        function addMessage(text, type) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            messageDiv.textContent = text;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        // 快捷按钮
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && document.getElementById('queryInput') === document.activeElement) {
                sendQuery();
            }
        });
    </script>
</body>
</html>
```

---

# ============================================
# 10. 部署和配置检查表
# ============================================

## ✅ MES 集成检查清单

```
配置阶段:
□ MES 数据库连接配置
□ MES API 密钥申请
□ 用户认证集成
□ 权限系统配置
□ 审计日志设置

数据阶段:
□ 工艺文档导入
□ 设备信息导入
□ 质检标准导入
□ 故障代码导入
□ 组织架构导入

开发阶段:
□ 数据连接模块测试
□ 实时数据查询测试
□ 权限检查测试
□ 审计日志验证
□ API 集成测试

部署阶段:
□ 测试环境部署
□ MES 集成测试
□ 性能测试
□ 安全审计
□ 用户培训

运维阶段:
□ 监控告警配置
□ 备份策略
□ 日志收集
□ 版本更新计划
```

---

# 总结

**将 Doc QA Bot 集成到 MES 的关键步骤：**

1. **数据连接** → 选择合适的 MES 数据源（API/数据库/CSV）
2. **规则定制** → 创建 MES 专用的 FAQ 和规则库
3. **实时处理** → 实现动态数据查询和上下文注入
4. **用户集成** → 支持会话上下文和用户信息传递
5. **权限控制** → 基于角色的访问控制
6. **审计追踪** → 完整的操作日志记录
7. **前端嵌入** → 集成到 MES UI 中

**预期效果：**
- ⚡ 降低 50%+ 的培训时间
- 📈 提升 30%+ 的工作效率
- 🎯 减少 40%+ 的问题响应时间
- 📊 完整的操作追溯和合规

---
"""
