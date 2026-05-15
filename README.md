# A股量化交易选股系统

[![license](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![fastapi](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![react](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev/)
[![qlib](https://img.shields.io/badge/powered%20by-qlib-00A86B)](https://github.com/microsoft/qlib)
[![build](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/chokingkit/mianAquant)
[![version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/chokingkit/mianAquant)

基于 [qlib](https://github.com/microsoft/qlib) 框架进行二次开发，构建适配 A 股市场的量化交易选股系统。

## 📋 项目简介

本项目旨在为 A 股市场提供一个开源的量化研究和回测平台，支持：

- **A 股市场化适配**：完整支持 A 股交易规则、股票代码规范和市场特性
- **灵活的数据源架构**：通过抽象层设计实现数据源（Tushare/AKShare）的无缝切换
- **友好的用户界面**：基于 React + MUI 的 Web UI，降低量化投资门槛

## ✨ 核心功能

### P0 功能（已完成）

- ✅ A 股股票代码适配（sh.600000 / sz.000001 格式）
- ✅ 数据源抽象层设计（统一接口 + 工厂模式）
- ✅ Tushare 和 AKShare 数据源适配器
- ✅ A 股交易日历集成
- ✅ qlib 数据格式转换
- ✅ 基础回测框架（支持 T+1、涨跌停限制）

### P1 功能（开发中）

- 🔄 Web UI 界面（策略配置 + 回测可视化）
- 🔄 策略库（预置常用选股策略）
- 🔄 风险管理模块（仓位控制、止损止盈）
- 🔄 数据缓存机制

### P2 功能（规划中）

- 📋 实盘交易接口
- 📋 因子研究工具
- 📋 多账户管理
- 📋 告警通知（邮件/微信/钉钉）

## 🏗️ 技术架构

```
┌─────────────────────────────────────────┐
│       业务逻辑层 (Strategy Engine)       │
├─────────────────────────────────────────┤
│     数据服务层 (Data Service Layer)      │
│  - 统一数据接口定义                      │
│  - 数据缓存管理                         │
│  - 数据质量校验                         │
├─────────────────────────────────────────┤
│   数据源适配层 (Data Adapter Layer)      │
│  - TushareAdapter                       │
│  - AKShareAdapter                       │
├─────────────────────────────────────────┤
│     数据源 API (Data Source API)         │
│  - Tushare API                          │
│  - AKShare API                          │
└─────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术选型 |
|------|----------|
| **后端框架** | FastAPI (Python 3.10+) |
| **量化框架** | qlib (微软开源) |
| **数据处理** | Pandas, NumPy |
| **前端框架** | React + TypeScript + Vite |
| **UI 组件库** | MUI (Material-UI) + Tailwind CSS |
| **数据库** | SQLite (开发) / PostgreSQL (生产) |
| **缓存** | Redis |
| **任务队列** | Celery (异步任务) |
| **数据源** | Tushare, AKShare |

## 🚀 快速开始

### 方式一：本地开发启动

#### 1. 后端启动

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -e .

# 启动后端服务（自动重载模式）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**验证成功**：访问 http://localhost:8000/docs 查看 Swagger API 文档。

#### 2. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖（首次运行需要 5-10 分钟）
npm install

# 启动前端开发服务器
npm run dev
```

**验证成功**：访问 http://localhost:3000 查看前端界面。

---

### 方式二：Docker 启动（推荐）

```bash
# 在项目根目录执行
docker-compose -f docker/docker-compose.yml up -d
```

启动的服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |
| 后端 API | 8000 | FastAPI 服务 |
| 前端界面 | 3000 | React 应用 |

---

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **API 文档** | http://localhost:8000/docs | Swagger UI，可在线调试 |
| **系统信息** | http://localhost:8000/ | 根路径 |
| **健康检查** | http://localhost:8000/health | 返回 `{"status":"ok"}` |
| **前端界面** | http://localhost:3000 | React 前端应用 |

---

## 📖 使用指南

### 1. 配置数据源

在 `backend/app/config.py` 中配置数据源：

```python
# 使用 Tushare（需要 Token）
data_provider: str = "tushare"
tushare_token: str = "YOUR_TUSHARE_TOKEN"

# 或使用 AKShare（免费，无需 Token）
data_provider: str = "akshare"
```

### 2. 运行策略回测

通过 Web UI：

1. 进入"策略管理"页面
2. 创建或选择策略（如 MA 均线策略）
3. 配置回测参数（股票池、时间范围、基准）
4. 点击"开始回测"
5. 查看回测报告（收益曲线、回撤、Sharpe 比率等）

通过 API：

```bash
# 创建策略
curl -X POST http://localhost:8000/api/v1/strategies/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试MA策略",
    "strategy_type": "ma_cross",
    "parameters": {"short_window": 5, "long_window": 20},
    "is_active": true
  }'

# 获取股票列表
curl http://localhost:8000/api/v1/stocks/
```

---

## 📂 项目结构

```
quant-system/
├── backend/                # 后端服务（FastAPI）
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── data/         # 数据源层
│   │   │   └── providers/  # 数据适配器
│   │   ├── models/       # 数据库模型
│   │   ├── strategies/   # 策略引擎
│   │   ├── risk/         # 风险管理
│   │   └── services/     # 业务逻辑
│   └── tests/
├── frontend/             # 前端应用（React + Vite）
│   ├── src/
│   │   ├── components/   # UI 组件
│   │   ├── pages/        # 页面
│   │   ├── services/     # API 服务
│   │   └── store/        # Redux 状态管理
│   └── public/
├── docker/               # Docker 配置
├── docs/                 # 文档
│   ├── PRD-quant-system.md         # 产品需求文档
│   ├── Architecture-quant-system.md # 系统架构设计
│   └── *.mermaid       # 架构图（Mermaid 格式）
├── qlib-source/          # qlib 框架源码（可选）
└── scripts/              # 脚本工具
```

---

## 🧪 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

---

## 📊 成功指标

- ✅ **功能完整性**：P0 需求完成率 100%，P1 需求完成率 ≥ 80%
- ✅ **性能**：5 年日线数据回测时间 < 1 分钟
- ✅ **可用性**：用户完成首次回测的操作步骤 ≤ 5 步
- ✅ **数据准确性**：与官方数据源对比，数据准确率 ≥ 99.9%
- ✅ **系统稳定性**：7×24 小时运行，可用性 ≥ 99%

---

## 🤝 贡献指南

欢迎贡献！请阅读以下指南：

1. **Fork 本仓库**
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **打开 Pull Request**

---

## 📝 文档

- [产品需求文档 (PRD)](docs/PRD-quant-system.md)
- [系统架构设计](docs/Architecture-quant-system.md)
- [API 文档](http://localhost:8000/docs)（本地启动后访问）

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢

- [qlib](https://github.com/microsoft/qlib) - 微软开源量化框架
- [Tushare](https://tushare.pro/) - 金融数据接口
- [AKShare](https://akshare.akfamily.xyz/) - 免费金融数据接口
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [React](https://react.dev/) - 前端 UI 框架

---

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/yourusername/quant-system/issues)

---

**⭐ 如果这个项目对你有帮助，请给它一个 Star！**
#   m i a n A q u a n t 
 
 