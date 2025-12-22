"""
FinBot Backend - FastAPI 應用入口
記帳聊天機器人後端服務
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from models.database import create_tables
from routers import chat, transactions, budgets, analytics, import_export


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    create_tables()
    yield


app = FastAPI(
    title="FinBot API",
    description="智慧記帳聊天機器人 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 設定
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

# 生產環境允許的來源
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

# Railway 部署時允許所有來源（或指定前端網址）
if os.getenv("RAILWAY_ENVIRONMENT"):
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(chat.router, prefix="/api/chat", tags=["聊天"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["交易"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["預算"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["分析"])
app.include_router(import_export.router, prefix="/api/io", tags=["匯入匯出"])


@app.get("/")
async def root():
    """API 根端點"""
    return {
        "name": "FinBot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy"}
