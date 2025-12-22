# FinBot - Railway 部署指南

## 架構說明

本專案需要部署兩個服務：
1. **Backend** - FastAPI 後端 API
2. **Frontend** - Vue 3 靜態網站

---

## 部署步驟

### 1. 準備 Git Repository

```bash
cd /Users/yaolo/Desktop/finbot
git add .
git commit -m "準備 Railway 部署"
git push origin main
```

### 2. 部署 Backend

1. 前往 [Railway](https://railway.app/) 並登入
2. 點擊 **New Project** → **Deploy from GitHub repo**
3. 選擇你的 finbot repository
4. Railway 會自動偵測到 `backend/` 目錄
5. 設定：
   - **Root Directory**: `backend`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. 部署完成後，複製 Backend URL（例如：`https://finbot-backend.up.railway.app`）

### 3. 部署 Frontend

1. 在 Railway 同一 Project 中，點擊 **New Service** → **GitHub Repo**
2. 選擇同一個 repository
3. 設定：
   - **Root Directory**: `.`（根目錄）
   - **Build Command**: `pnpm install && pnpm build`
   - **Start Command**: `npx serve dist -s -l $PORT`
4. 新增環境變數：
   ```
   VITE_API_URL=https://你的backend網址/api
   ```
   例如：`VITE_API_URL=https://finbot-backend.up.railway.app/api`

### 4. 設定 CORS（可選）

如果前端網址不是 `*`，需要在 Backend 設定環境變數：
```
FRONTEND_URL=https://你的frontend網址
```

---

## 環境變數總覽

### Backend
| 變數 | 說明 | 範例 |
|------|------|------|
| `FRONTEND_URL` | 前端網址（CORS） | `https://finbot.up.railway.app` |

### Frontend
| 變數 | 說明 | 範例 |
|------|------|------|
| `VITE_API_URL` | 後端 API 網址 | `https://finbot-backend.up.railway.app/api` |

---

## 注意事項

1. **SQLite 限制**：Railway 使用 ephemeral 儲存，重新部署會遺失資料。如需持久化，建議：
   - 使用 Railway 的 PostgreSQL 服務
   - 或使用 Railway Volume

2. **免費額度**：Railway 每月提供 $5 免費額度，小型專案通常足夠

3. **網域**：Railway 提供免費的 `*.up.railway.app` 網域，也支援自訂網域

---

## 本地測試生產版本

```bash
# 前端
pnpm build
npx serve dist -s -l 3000

# 後端
cd backend
uvicorn main:app --port 8000
```
