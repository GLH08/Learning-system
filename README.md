# 📚 智能答题学习系统

通过答题系统学习、巩固知识，支持AI自动补全答案与解析，实现高效的学习闭环。

## ✨ 核心特性

- 📥 **智能导入** - 支持Word/Excel/TXT等格式，自动解析题目结构
- 🤖 **AI补全** - 接入OpenAI兼容API，自动生成答案与解析
- 📝 **智能组卷** - 按题型/数量/难度/知识点自由组合
- 📊 **学习分析** - 自动评分，错题收集，AI生成个性化分析报告
- 💾 **数据管理** - 题库导入导出，数据备份恢复

## 🚀 快速部署

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+

### 本地开发（一键部署）

```bash
cd Learning-system
docker compose up -d
```

访问：
- 前端: http://localhost:5173
- 后端: http://localhost:8000/docs

### 服务器部署（3步配置）

**重要：服务器部署必须修改环境变量！**

#### 步骤1: 复制配置模板
```bash
cp .env.example .env
```

#### 步骤2: 编辑配置文件
```bash
nano .env
```

修改以下配置：
```bash
# 1. 生成并设置安全密钥
# 运行: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=生成的密钥粘贴在这里

# 2. 修改为你的服务器IP或域名
CORS_ORIGINS=http://你的服务器IP:5173
VITE_API_BASE_URL=http://你的服务器IP:8000/api
```

**配置示例（假设服务器IP是 192.168.1.100）：**
```bash
SECRET_KEY=xK9mP2nQ5rT8wY1zA4bC7dE0fG3hJ6kL9mN2pQ5sT8vW
CORS_ORIGINS=http://192.168.1.100:5173
VITE_API_BASE_URL=http://192.168.1.100:8000/api
```

#### 步骤3: 启动服务
```bash
docker compose up -d
```

访问：http://你的服务器IP:5173

### 验证部署

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 测试后端健康
curl http://localhost:8000/health
# 预期输出: {"status":"healthy"}
```

## 🚢 远程部署 (GitHub Actions)

本项目配置了自动构建流程，代码推送到 `main` 分支后会自动构建 Docker 镜像并推送至 GitHub Container Registry (GHCR)。

### 常见部署方式

#### 方式 A: 远程服务器部署 (推荐 - 生产环境)
使用 GitHub Actions 自动构建好的镜像（GHCR），无需服务器构建代码。

1. **准备文件**: 将 `docker-compose.prod.yml` 和 `.env` 上传到服务器。
2. **启动服务**: `docker compose -f docker-compose.prod.yml up -d`
3. **更新版本**: `docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d`

#### 方式 B: 源码部署 (开发/测试环境)
适用于本地开发或需要修改源码的场景。

1. **启动**: `docker compose up -d` (使用默认的 docker-compose.yml 及其 Dockerfile)


### 首次使用

1. 访问前端地址
2. 系统检测到未初始化，显示密码设置页面
3. 输入管理员密码（至少6位）
4. 点击"初始化"按钮，自动登录进入系统

## 📖 功能说明

### 已实现功能（100%）

✅ **认证系统** - 初始化、登录、Token验证、密码修改  
✅ **题库管理** - CRUD、分类、标签、批量操作、导入导出  
✅ **AI功能** - 答案补全、解析生成、批量任务  
✅ **文档解析** - Word、Excel、TXT、JSON导入  
✅ **组卷答题** - 快速组卷、自定义组卷、错题专项、三种答题模式  
✅ **错题管理** - 收集、掌握、重做、试卷生成  
✅ **学习统计** - 概览、每日、分类、薄弱点分析  
✅ **AI报告** - 智能学习建议  
✅ **系统设置** - AI配置、数据备份恢复  

详细功能规划请查看 `plan.md`

## 🛠️ 技术栈

**后端**: Python + FastAPI + SQLAlchemy + SQLite  
**前端**: Vue 3 + TypeScript + Naive UI + ECharts  
**AI**: OpenAI API 集成  
**部署**: Docker + Docker Compose

## 🔧 常用命令

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 备份数据
cp -r ./data ./backup/backup_$(date +%Y%m%d_%H%M%S)
```

## ⚙️ 环境变量说明

| 变量 | 说明 | 本地开发 | 服务器部署 |
|------|------|----------|------------|
| `SECRET_KEY` | JWT加密密钥 | 默认值 | **必须修改** |
| `CORS_ORIGINS` | 允许的前端地址 | `http://localhost:5173` | **改为服务器IP** |
| `VITE_API_BASE_URL` | 后端API地址 | `http://localhost:8000/api` | **改为服务器IP** |

**配置格式：**
- 多个CORS地址用逗号分隔，不要有空格
- 必须包含协议（http:// 或 https://）
- 必须包含端口号（如果不是80/443）

## 🐛 常见问题

**Q: 后端启动失败，提示 Generic 错误？**  
A: 已修复，确保使用最新代码。

**Q: 前端无法连接后端？**  
A: 检查 CORS_ORIGINS 和 VITE_API_BASE_URL 配置是否正确。

**Q: 修改配置后不生效？**  
A: 需要重新构建：`docker compose down && docker compose up -d --build`

**Q: 端口被占用？**  
A: 修改 docker-compose.yml 中的端口映射。

**Q: 如何重置管理员密码？**  
A: 删除数据库文件 `./data/learning_system.db` 后重启服务。

更多问题请查看 [DEPLOYMENT.md](./DEPLOYMENT.md)

## 📁 项目结构

```
Learning-system/
├── backend/                # 后端（FastAPI）
│   ├── api/               # API路由
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic模型
│   ├── services/          # 业务逻辑
│   └── main.py            # 应用入口
├── frontend/              # 前端（Vue 3）
│   └── src/
│       ├── api/          # API封装
│       ├── views/        # 页面组件
│       └── stores/       # 状态管理
├── data/                  # 数据目录
├── backup/                # 备份目录
└── docker-compose.yml     # Docker配置
```

## 📄 许可证

MIT License


## 🚨 快速修复部署问题

如果遇到 "unable to open database file" 错误：

```bash
# 创建目录并设置权限
mkdir -p data backup
chmod 777 data backup

# 重新部署
docker compose down
docker compose up -d --build
```

或使用一键部署脚本：

```bash
chmod +x deploy.sh
./deploy.sh
```
