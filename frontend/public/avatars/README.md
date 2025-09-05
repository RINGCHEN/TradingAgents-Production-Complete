# 分析師頭像資源

此目錄包含對話模組中使用的分析師頭像圖片。

## 頭像規格

- **格式**: PNG (推薦) 或 JPG
- **尺寸**: 64x64 像素 (推薦)
- **背景**: 透明背景 (PNG) 或白色背景
- **風格**: 簡潔、專業的圖標風格

## 頭像文件命名

頭像文件應該按照以下格式命名：

```
{analyst_id}.png
```

例如：
- `market_analyst.png` - 市場分析師
- `fundamentals_analyst.png` - 基本面分析師
- `news_analyst.png` - 新聞分析師
- `social_media_analyst.png` - 社群媒體分析師
- `risk_analyst.png` - 風險分析師

## 預設頭像

如果特定分析師的頭像不存在，系統會使用 `default_avatar.png` 作為預設頭像。

## CDN 支援

在生產環境中，這些頭像可以部署到 CDN 以提高載入速度：

```
https://cdn.tradingagents.com/avatars/{analyst_id}.png
```

## 頭像設計指南

### 市場分析師 (market_analyst)
- 圖標：📈 或 📊
- 顏色：藍色系 (#1890ff)
- 風格：技術圖表相關

### 基本面分析師 (fundamentals_analyst)
- 圖標：📋 或 💼
- 顏色：綠色系 (#52c41a)
- 風格：財報、數據相關

### 新聞分析師 (news_analyst)
- 圖標：📰 或 📺
- 顏色：橙色系 (#fa8c16)
- 風格：新聞、媒體相關

### 社群媒體分析師 (social_media_analyst)
- 圖標：💬 或 🌐
- 顏色：紫色系 (#722ed1)
- 風格：社交網路相關

### 風險分析師 (risk_analyst)
- 圖標：⚠️ 或 🛡️
- 顏色：紅色系 (#f5222d)
- 風格：安全、警示相關

## 使用範例

在 React 元件中使用頭像：

```tsx
<img 
  src={`/avatars/${analystId}.png`}
  alt={`${analystName} 頭像`}
  className="analyst-avatar"
  onError={(e) => {
    e.currentTarget.src = '/avatars/default_avatar.png';
  }}
/>
```

## 版權說明

所有頭像圖片應該是：
1. 原創設計
2. 使用免費圖標庫 (如 Feather Icons, Heroicons)
3. 購買的商業授權圖片

請確保所有使用的圖片都有適當的使用權限。