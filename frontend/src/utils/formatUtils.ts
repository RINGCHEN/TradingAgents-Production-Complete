/**
 * 安全格式化工具函數
 * 防止 undefined/null 值導致的 toLocaleString 錯誤
 */

/**
 * 安全格式化數字
 */
export function safeFormatNumber(value: number | undefined | null, defaultValue: string = '--'): string {
  if (value === undefined || value === null || isNaN(value)) {
    return defaultValue;
  }
  return value.toLocaleString();
}

/**
 * 安全格式化價格
 */
export function safeFormatPrice(price: number | undefined | null, currency: string = 'NT$', defaultValue: string = '--'): string {
  if (price === undefined || price === null || isNaN(price)) {
    return `${currency} ${defaultValue}`;
  }
  return `${currency} ${price.toLocaleString()}`;
}

/**
 * 安全格式化日期
 */
export function safeFormatDate(date: string | Date | undefined | null, defaultValue: string = '--'): string {
  if (!date) {
    return defaultValue;
  }
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    if (isNaN(dateObj.getTime())) {
      return defaultValue;
    }
    return dateObj.toLocaleString('zh-TW');
  } catch (error) {
    console.warn('Date formatting error:', error);
    return defaultValue;
  }
}

/**
 * 安全格式化百分比
 */
export function safeFormatPercent(value: number | undefined | null, decimals: number = 1, defaultValue: string = '--'): string {
  if (value === undefined || value === null || isNaN(value)) {
    return `${defaultValue}%`;
  }
  return `${value.toFixed(decimals)}%`;
}

/**
 * 安全格式化計數器（如瀏覽次數、讚數等）
 */
export function safeFormatCount(count: number | undefined | null, defaultValue: string = '0'): string {
  if (count === undefined || count === null || isNaN(count)) {
    return defaultValue;
  }
  return count.toLocaleString();
}