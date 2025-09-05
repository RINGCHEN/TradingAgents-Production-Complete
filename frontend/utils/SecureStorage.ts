// 安全存儲工具 - 提供加密的本地存儲功能
// 支援數據完整性檢查和錯誤恢復

export class SecureStorage {
  private static readonly STORAGE_PREFIX = 'ta_admin_';
  private static readonly ALGORITHM = 'AES-GCM';
  private static readonly KEY_LENGTH = 256;
  private static encryptionKey: CryptoKey | null = null;

  /**
   * 安全存儲數據
   */
  static async setItem(key: string, value: any): Promise<void> {
    try {
      const serialized = JSON.stringify(value);
      const encrypted = await this.encrypt(serialized);
      const storageKey = this.getStorageKey(key);
      
      localStorage.setItem(storageKey, encrypted);
      
      // 存儲校驗和以檢測數據完整性
      const checksum = await this.calculateChecksum(encrypted);
      localStorage.setItem(`${storageKey}_checksum`, checksum);
      
    } catch (error) {
      console.error('存儲數據失敗:', error);
      throw new Error('數據存儲失敗');
    }
  }

  /**
   * 安全讀取數據
   */
  static async getItem<T>(key: string): Promise<T | null> {
    try {
      const storageKey = this.getStorageKey(key);
      const encrypted = localStorage.getItem(storageKey);
      if (!encrypted) return null;

      // 驗證數據完整性
      const storedChecksum = localStorage.getItem(`${storageKey}_checksum`);
      if (storedChecksum) {
        const calculatedChecksum = await this.calculateChecksum(encrypted);
        if (storedChecksum !== calculatedChecksum) {
          console.warn('數據完整性檢查失敗，清除損壞的數據');
          this.removeItem(key);
          return null;
        }
      }

      const decrypted = await this.decrypt(encrypted);
      return JSON.parse(decrypted);
    } catch (error) {
      console.error('讀取數據失敗:', error);
      // 數據損壞，清除
      this.removeItem(key);
      return null;
    }
  }

  /**
   * 同步讀取數據（用於快速檢查）
   */
  static getItemSync<T>(key: string): T | null {
    try {
      const storageKey = this.getStorageKey(key);
      const encrypted = localStorage.getItem(storageKey);
      if (!encrypted) return null;

      // 簡化的同步解密（僅用於快速檢查）
      const decrypted = this.decryptSync(encrypted);
      return JSON.parse(decrypted);
    } catch (error) {
      console.warn('同步讀取數據失敗:', error);
      return null;
    }
  }

  /**
   * 移除存儲的數據
   */
  static async removeItem(key: string): Promise<void> {
    const storageKey = this.getStorageKey(key);
    localStorage.removeItem(storageKey);
    localStorage.removeItem(`${storageKey}_checksum`);
  }

  /**
   * 清除所有相關存儲
   */
  static async clearAll(): Promise<void> {
    const keys = Object.keys(localStorage);
    const prefixedKeys = keys.filter(key => key.startsWith(SecureStorage.STORAGE_PREFIX));
    
    prefixedKeys.forEach(key => {
      localStorage.removeItem(key);
    });
  }

  /**
   * 檢查存儲是否可用
   */
  static isStorageAvailable(): boolean {
    try {
      const testKey = '__storage_test__';
      localStorage.setItem(testKey, 'test');
      localStorage.removeItem(testKey);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * 獲取存儲使用情況
   */
  static getStorageInfo(): { used: number; available: number; percentage: number } {
    let used = 0;
    let available = 5 * 1024 * 1024; // 假設5MB可用空間

    try {
      // 計算已使用空間
      for (let key in localStorage) {
        if (localStorage.hasOwnProperty(key)) {
          used += localStorage[key].length + key.length;
        }
      }
    } catch (error) {
      console.warn('無法計算存儲使用情況:', error);
    }

    return {
      used,
      available,
      percentage: (used / available) * 100
    };
  }

  /**
   * 初始化加密密鑰
   */
  private static async initializeKey(): Promise<void> {
    if (this.encryptionKey) return;

    try {
      // 從sessionStorage獲取密鑰材料，如果不存在則生成新的
      let keyMaterial = sessionStorage.getItem('key_material');
      if (!keyMaterial) {
        const randomBytes = crypto.getRandomValues(new Uint8Array(32));
        keyMaterial = Array.from(randomBytes, byte => byte.toString(16).padStart(2, '0')).join('');
        sessionStorage.setItem('key_material', keyMaterial);
      }

      // 導入密鑰
      const keyData = new Uint8Array(keyMaterial.match(/.{1,2}/g)!.map(byte => parseInt(byte, 16)));
      this.encryptionKey = await crypto.subtle.importKey(
        'raw',
        keyData,
        { name: this.ALGORITHM },
        false,
        ['encrypt', 'decrypt']
      );
    } catch (error) {
      console.error('密鑰初始化失敗:', error);
      throw new Error('加密初始化失敗');
    }
  }

  /**
   * 加密數據
   */
  private static async encrypt(text: string): Promise<string> {
    try {
      await this.initializeKey();
      if (!this.encryptionKey) throw new Error('加密密鑰未初始化');

      const encoder = new TextEncoder();
      const data = encoder.encode(text);
      
      // 生成隨機IV
      const iv = crypto.getRandomValues(new Uint8Array(12));
      
      // 加密數據
      const encrypted = await crypto.subtle.encrypt(
        { name: this.ALGORITHM, iv },
        this.encryptionKey,
        data
      );

      // 組合IV和加密數據
      const combined = new Uint8Array(iv.length + encrypted.byteLength);
      combined.set(iv);
      combined.set(new Uint8Array(encrypted), iv.length);

      // 轉換為Base64
      return btoa(String.fromCharCode(...combined));
    } catch (error) {
      console.error('加密失敗:', error);
      // 降級到簡單的Base64編碼
      return btoa(unescape(encodeURIComponent(text)));
    }
  }

  /**
   * 解密數據
   */
  private static async decrypt(encrypted: string): Promise<string> {
    try {
      await this.initializeKey();
      if (!this.encryptionKey) throw new Error('加密密鑰未初始化');

      // 從Base64解碼
      const combined = new Uint8Array(
        atob(encrypted).split('').map(char => char.charCodeAt(0))
      );

      // 分離IV和加密數據
      const iv = combined.slice(0, 12);
      const encryptedData = combined.slice(12);

      // 解密數據
      const decrypted = await crypto.subtle.decrypt(
        { name: this.ALGORITHM, iv },
        this.encryptionKey,
        encryptedData
      );

      const decoder = new TextDecoder();
      return decoder.decode(decrypted);
    } catch (error) {
      console.error('解密失敗:', error);
      try {
        // 降級到簡單的Base64解碼
        const decoded = atob(encrypted);
        return decodeURIComponent(escape(decoded));
      } catch (fallbackError) {
        throw new Error('解密失敗');
      }
    }
  }

  /**
   * 同步解密（簡化版本）
   */
  private static decryptSync(encrypted: string): string {
    try {
      const mixed = atob(encrypted);
      const parts = mixed.split('.');
      if (parts.length !== 2) {
        throw new Error('加密格式錯誤');
      }
      
      const encoded = parts[1];
      const decoded = atob(encoded);
      return decodeURIComponent(escape(decoded));
    } catch (error) {
      throw new Error('同步解密失敗');
    }
  }

  /**
   * 計算校驗和 - 使用Web Crypto API的SHA-256
   */
  private static async calculateChecksum(data: string): Promise<string> {
    try {
      const encoder = new TextEncoder();
      const dataBuffer = encoder.encode(data);
      const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    } catch (error) {
      // 降級到簡單的校驗和計算
      let hash = 0;
      for (let i = 0; i < data.length; i++) {
        const char = data.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // 轉換為32位整數
      }
      return hash.toString(36);
    }
  }

  /**
   * 清除加密密鑰（登出時調用）
   */
  static clearEncryptionKey(): void {
    this.encryptionKey = null;
    sessionStorage.removeItem('key_material');
  }

  /**
   * 獲取存儲鍵名
   */
  private static getStorageKey(key: string): string {
    return `${SecureStorage.STORAGE_PREFIX}${key}`;
  }
}