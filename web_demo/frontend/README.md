# 实验室安全小助手 · 前端

React + TypeScript + Vite + Tailwind 构建的实验室安全咨询前端。

## 开发

```bash
npm install
npm run dev          # 启动 Vite，端口 5173
```

开发模式下 `/api` 与 `/health` 通过 Vite proxy 转发到 `127.0.0.1:8088`（FastAPI 后端）。
若后端端口不同，修改 `vite.config.ts` 的 `proxy.target`。

## 构建

```bash
npm run build        # 产出 dist/
npm run preview      # 本地预览 dist/
```

## 生产部署

两种方式：

1. **FastAPI 托管**（推荐）：在后端 `app.mount('/', StaticFiles(directory='dist', html=True))`。
2. **独立 Nginx**：将 `dist/` 部署到 Nginx，反代 `/api` 与 `/health` 到 FastAPI。

## 目录

```
src/
├── components/        # 全部 UI 组件
├── hooks/useApi.ts    # 接口封装
├── types/api.ts       # 与后端模型对齐的 TS 接口
├── App.tsx            # 应用入口
├── main.tsx           # ReactDOM 挂载
└── index.css          # Tailwind + 主题变量
```

## 设计要点

- **决策类型**有 7 种，每种通过左侧边框颜色 + 标签 + 背景做视觉区分
- **引用面板**默认折叠，点击展开；引用卡片显示来源、片段、匹配分（10 分制可视化）
- **快捷问题**点击后填充到输入框并自动聚焦，伴随 150ms 闪烁动画
- **响应式**：≥1024 三栏，768–1023 双栏，<768 单栏
- **所有 API 调用使用相对路径**，不写死 host
- **Markdown** 通过 `marked` + `DOMPurify` 渲染，防 XSS
