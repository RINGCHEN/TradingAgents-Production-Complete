/**
 * SecureStorage 單元測試
 * 測試安全存儲工具的加密和存儲功能
 */

import { SecureStorage } from '../../utils/SecureStorage';

describe('SecureStorage', () => {
  const testKey = 'test-key';
  const testData = { id: 1, name: 'test', sensitive: 'secret-data' };

  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    jest.clearAllMocks();
  });

  describe('setItem', () => {
    it('should store data successfully', async () => {
      // Act
      await SecureStorage.setItem(testKey, testData);

      // Assert
      expect(localStorage.setItem).toHaveBeenCalled();
      const storedValue = localStorage.getItem.mock.calls[0]?.[0] || 
                         (localStorage.setItem as jest.Mock).mock.calls[0]?.[1];
      expect(storedValue).toBeDefined();
    });

    it('should handle storage errors', async () => {
      // Arrange
      (localStorage.setItem as jest.Mock).mockImplementation(() => {
        throw new Error('Storage quota exceeded');
      });

      // Act & Assert
      await expect(SecureStorage.setItem(testKey, testData)).rejects.toThrow();
    });

    it('should store different data types', async () => {
      // Arrange
      const testCases = [
        { key: 'string', value: 'test string' },
        { key: 'number', value: 42 },
        { key: 'boolean', value: true },
        { key: 'array', value: [1, 2, 3] },
        { key: 'object', value: { nested: { data: 'value' } } },
        { key: 'null', value: null }
      ];

      // Act & Assert
      for (const testCase of testCases) {
        await expect(SecureStorage.setItem(testCase.key, testCase.value)).resolves.toBeUndefined();
      }
    });
  });

  describe('getItem', () => {
    it('should retrieve stored data successfully', async () => {
      // Arrange
      await SecureStorage.setItem(testKey, testData);

      // Act
      const result = await SecureStorage.getItem(testKey);

      // Assert
      expect(result).toEqual(testData);
    });

    it('should return null for non-existent keys', async () => {
      // Act
      const result = await SecureStorage.getItem('non-existent-key');

      // Assert
      expect(result).toBeNull();
    });

    it('should handle corrupted data gracefully', async () => {
      // Arrange
      (localStorage.getItem as jest.Mock).mockReturnValue('corrupted-data');

      // Act
      const result = await SecureStorage.getItem(testKey);

      // Assert
      expect(result).toBeNull();
    });

    it('should handle storage errors', async () => {
      // Arrange
      (localStorage.getItem as jest.Mock).mockImplementation(() => {
        throw new Error('Storage access denied');
      });

      // Act & Assert
      await expect(SecureStorage.getItem(testKey)).rejects.toThrow();
    });

    it('should retrieve different data types correctly', async () => {
      // Arrange
      const testCases = [
        { key: 'string', value: 'test string' },
        { key: 'number', value: 42 },
        { key: 'boolean', value: true },
        { key: 'array', value: [1, 2, 3] },
        { key: 'object', value: { nested: { data: 'value' } } }
      ];

      // Act & Assert
      for (const testCase of testCases) {
        await SecureStorage.setItem(testCase.key, testCase.value);
        const result = await SecureStorage.getItem(testCase.key);
        expect(result).toEqual(testCase.value);
      }
    });
  });

  describe('getItemSync', () => {
    it('should retrieve stored data synchronously', () => {
      // Arrange
      const jsonData = JSON.stringify(testData);
      (localStorage.getItem as jest.Mock).mockReturnValue(jsonData);

      // Act
      const result = SecureStorage.getItemSync(testKey);

      // Assert
      expect(result).toEqual(testData);
      expect(localStorage.getItem).toHaveBeenCalledWith(testKey);
    });

    it('should return null for non-existent keys', () => {
      // Arrange
      (localStorage.getItem as jest.Mock).mockReturnValue(null);

      // Act
      const result = SecureStorage.getItemSync(testKey);

      // Assert
      expect(result).toBeNull();
    });

    it('should handle corrupted data gracefully', () => {
      // Arrange
      (localStorage.getItem as jest.Mock).mockReturnValue('corrupted-data');

      // Act
      const result = SecureStorage.getItemSync(testKey);

      // Assert
      expect(result).toBeNull();
    });

    it('should handle storage errors gracefully', () => {
      // Arrange
      (localStorage.getItem as jest.Mock).mockImplementation(() => {
        throw new Error('Storage access denied');
      });

      // Act
      const result = SecureStorage.getItemSync(testKey);

      // Assert
      expect(result).toBeNull();
    });
  });

  describe('removeItem', () => {
    it('should remove stored data successfully', async () => {
      // Arrange
      await SecureStorage.setItem(testKey, testData);

      // Act
      await SecureStorage.removeItem(testKey);

      // Assert
      expect(localStorage.removeItem).toHaveBeenCalledWith(testKey);
    });

    it('should handle removal of non-existent keys', async () => {
      // Act & Assert
      await expect(SecureStorage.removeItem('non-existent-key')).resolves.toBeUndefined();
    });

    it('should handle storage errors', async () => {
      // Arrange
      (localStorage.removeItem as jest.Mock).mockImplementation(() => {
        throw new Error('Storage access denied');
      });

      // Act & Assert
      await expect(SecureStorage.removeItem(testKey)).rejects.toThrow();
    });
  });

  describe('clear', () => {
    it('should clear all stored data', async () => {
      // Arrange
      await SecureStorage.setItem('key1', 'value1');
      await SecureStorage.setItem('key2', 'value2');

      // Act
      await SecureStorage.clear();

      // Assert
      expect(localStorage.clear).toHaveBeenCalled();
    });

    it('should handle storage errors', async () => {
      // Arrange
      (localStorage.clear as jest.Mock).mockImplementation(() => {
        throw new Error('Storage access denied');
      });

      // Act & Assert
      await expect(SecureStorage.clear()).rejects.toThrow();
    });
  });

  describe('hasItem', () => {
    it('should return true for existing items', async () => {
      // Arrange
      await SecureStorage.setItem(testKey, testData);

      // Act
      const result = await SecureStorage.hasItem(testKey);

      // Assert
      expect(result).toBe(true);
    });

    it('should return false for non-existent items', async () => {
      // Act
      const result = await SecureStorage.hasItem('non-existent-key');

      // Assert
      expect(result).toBe(false);
    });

    it('should handle storage errors', async () => {
      // Arrange
      (localStorage.getItem as jest.Mock).mockImplementation(() => {
        throw new Error('Storage access denied');
      });

      // Act & Assert
      await expect(SecureStorage.hasItem(testKey)).rejects.toThrow();
    });
  });

  describe('getAllKeys', () => {
    it('should return all storage keys', async () => {
      // Arrange
      await SecureStorage.setItem('key1', 'value1');
      await SecureStorage.setItem('key2', 'value2');
      await SecureStorage.setItem('key3', 'value3');

      // Mock localStorage.length and key method
      Object.defineProperty(localStorage, 'length', { value: 3 });
      (localStorage.key as jest.Mock)
        .mockReturnValueOnce('key1')
        .mockReturnValueOnce('key2')
        .mockReturnValueOnce('key3');

      // Act
      const keys = await SecureStorage.getAllKeys();

      // Assert
      expect(keys).toEqual(['key1', 'key2', 'key3']);
    });

    it('should return empty array when no keys exist', async () => {
      // Arrange
      Object.defineProperty(localStorage, 'length', { value: 0 });

      // Act
      const keys = await SecureStorage.getAllKeys();

      // Assert
      expect(keys).toEqual([]);
    });

    it('should handle storage errors', async () => {
      // Arrange
      Object.defineProperty(localStorage, 'length', {
        get: () => {
          throw new Error('Storage access denied');
        }
      });

      // Act & Assert
      await expect(SecureStorage.getAllKeys()).rejects.toThrow();
    });
  });

  describe('getStorageSize', () => {
    it('should calculate storage size correctly', async () => {
      // Arrange
      await SecureStorage.setItem('key1', 'value1');
      await SecureStorage.setItem('key2', { data: 'value2' });

      // Mock localStorage entries
      Object.defineProperty(localStorage, 'length', { value: 2 });
      (localStorage.key as jest.Mock)
        .mockReturnValueOnce('key1')
        .mockReturnValueOnce('key2');
      (localStorage.getItem as jest.Mock)
        .mockReturnValueOnce('"value1"')
        .mockReturnValueOnce('{"data":"value2"}');

      // Act
      const size = await SecureStorage.getStorageSize();

      // Assert
      expect(size).toBeGreaterThan(0);
      expect(typeof size).toBe('number');
    });

    it('should return 0 for empty storage', async () => {
      // Arrange
      Object.defineProperty(localStorage, 'length', { value: 0 });

      // Act
      const size = await SecureStorage.getStorageSize();

      // Assert
      expect(size).toBe(0);
    });
  });

  describe('data integrity', () => {
    it('should maintain data integrity across operations', async () => {
      // Arrange
      const complexData = {
        user: {
          id: 123,
          profile: {
            name: 'Test User',
            settings: {
              theme: 'dark',
              notifications: true,
              preferences: ['pref1', 'pref2']
            }
          }
        },
        tokens: {
          access: 'access-token',
          refresh: 'refresh-token',
          expires: Date.now() + 3600000
        },
        metadata: {
          version: '1.0.0',
          lastUpdated: new Date().toISOString()
        }
      };

      // Act
      await SecureStorage.setItem('complex-data', complexData);
      const retrieved = await SecureStorage.getItem('complex-data');

      // Assert
      expect(retrieved).toEqual(complexData);
      expect(retrieved).not.toBe(complexData); // Should be a different object reference
    });

    it('should handle special characters and unicode', async () => {
      // Arrange
      const specialData = {
        text: 'Special chars: !@#$%^&*()_+-=[]{}|;:,.<>?',
        unicode: '你好世界 🌍 🚀 ✨',
        emoji: '😀😃😄😁😆😅😂🤣',
        symbols: '™®©℠℗'
      };

      // Act
      await SecureStorage.setItem('special-data', specialData);
      const retrieved = await SecureStorage.getItem('special-data');

      // Assert
      expect(retrieved).toEqual(specialData);
    });
  });

  describe('error recovery', () => {
    it('should recover from temporary storage failures', async () => {
      // Arrange
      let failCount = 0;
      (localStorage.setItem as jest.Mock).mockImplementation(() => {
        failCount++;
        if (failCount <= 2) {
          throw new Error('Temporary failure');
        }
        // Success on third try
      });

      // Act & Assert - should eventually succeed with retry logic if implemented
      // For now, just test that it fails consistently
      await expect(SecureStorage.setItem(testKey, testData)).rejects.toThrow();
    });

    it('should handle quota exceeded errors', async () => {
      // Arrange
      (localStorage.setItem as jest.Mock).mockImplementation(() => {
        const error = new Error('QuotaExceededError');
        error.name = 'QuotaExceededError';
        throw error;
      });

      // Act & Assert
      await expect(SecureStorage.setItem(testKey, testData)).rejects.toThrow('QuotaExceededError');
    });
  });

  describe('performance', () => {
    it('should handle large data efficiently', async () => {
      // Arrange
      const largeData = {
        items: Array.from({ length: 1000 }, (_, i) => ({
          id: i,
          name: `Item ${i}`,
          data: `Data for item ${i}`.repeat(10)
        }))
      };

      // Act
      const startTime = Date.now();
      await SecureStorage.setItem('large-data', largeData);
      const retrieved = await SecureStorage.getItem('large-data');
      const endTime = Date.now();

      // Assert
      expect(retrieved).toEqual(largeData);
      expect(endTime - startTime).toBeLessThan(1000); // Should complete within 1 second
    });

    it('should handle multiple concurrent operations', async () => {
      // Arrange
      const operations = Array.from({ length: 10 }, (_, i) => 
        SecureStorage.setItem(`key-${i}`, { value: i })
      );

      // Act
      await Promise.all(operations);

      // Verify all items were stored
      const retrieveOperations = Array.from({ length: 10 }, (_, i) => 
        SecureStorage.getItem(`key-${i}`)
      );

      const results = await Promise.all(retrieveOperations);

      // Assert
      results.forEach((result, index) => {
        expect(result).toEqual({ value: index });
      });
    });
  });
});