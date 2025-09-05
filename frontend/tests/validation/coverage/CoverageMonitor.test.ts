/**
 * CoverageMonitor 測試套件
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { CoverageMonitor } from './CoverageMonitor'
import { promises as fs } from 'fs'
import { join } from 'path'

// Mock 文件系統操作
vi.mock('fs', () => ({
  promises: {
    mkdir: vi.fn(),
    readFile: vi.fn(),
    writeFile: vi.fn(),
    access: vi.fn()
  }
}))

// Mock glob
vi.mock('glob', () => ({
  glob: vi.fn()
}))

describe('CoverageMonitor', () => {
  let monitor: CoverageMonitor
  const mockOutputDir = './test-coverage-reports'

  beforeEach(() => {
    monitor = new CoverageMonitor({
      thresholds: {
        lines: 85,
        functions: 85,
        branches: 80,
        statements: 85
      },
      outputDir: mockOutputDir,
      historySize: 10,
      alertEnabled: true,
      alertThresholds: {
        warning: 80,
        critical: 70
      }
    })

    // 清除所有 mock
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('初始化', () => {
    it('應該成功初始化監控器', async () => {
      const mkdirSpy = vi.mocked(fs.mkdir).mockResolvedValue(undefined)
      const readFileSpy = vi.mocked(fs.readFile).mockRejectedValue(new Error('File not found'))

      await monitor.initialize()

      expect(mkdirSpy).toHaveBeenCalledWith(mockOutputDir, { recursive: true })
    })

    it('應該載入現有的覆蓋率歷史', async () => {
      const mockHistory = [
        {
          timestamp: new Date(),
          coverage: { lines: 80, functions: 75, branches: 70, statements: 80 },
          passed: false
        }
      ]

      vi.mocked(fs.mkdir).mockResolvedValue(undefined)
      vi.mocked(fs.readFile).mockResolvedValue(JSON.stringify(mockHistory))

      await monitor.initialize()

      const history = monitor.getCoverageHistory()
      expect(history).toHaveLength(1)
      expect(history[0].coverage.lines).toBe(80)
    })
  })

  describe('覆蓋率收集', () => {
    beforeEach(async () => {
      vi.mocked(fs.mkdir).mockResolvedValue(undefined)
      vi.mocked(fs.readFile).mockRejectedValue(new Error('File not found'))
      await monitor.initialize()
    })

    it('應該成功收集 JSON 格式覆蓋率', async () => {
      const mockCoverageData = {
        total: {
          lines: { pct: 85.5 },
          functions: { pct: 90.0 },
          branches: { pct: 75.0 },
          statements: { pct: 87.2 }
        }
      }

      vi.mocked(fs.readFile).mockResolvedValue(JSON.stringify(mockCoverageData))

      const coverage = await monitor.collectCoverage(['coverage/coverage-final.json'])

      expect(coverage.lines).toBe(85.5)
      expect(coverage.functions).toBe(90.0)
      expect(coverage.branches).toBe(75.0)
      expect(coverage.statements).toBe(87.2)
    })

    it('應該處理 LCOV 格式覆蓋率', async () => {
      const mockLcovData = `
TN:
SF:/path/to/file.ts
FNF:10
FNH:8
LF:100
LH:85
BRF:20
BRH:15
end_of_record
      `.trim()

      vi.mocked(fs.readFile).mockResolvedValue(mockLcovData)

      const coverage = await monitor.collectCoverage(['coverage/lcov.info'])

      expect(coverage.lines).toBe(85)
      expect(coverage.functions).toBe(80)
      expect(coverage.branches).toBe(75)
    })

    it('應該處理多個覆蓋率文件', async () => {
      const mockData1 = {
        total: {
          lines: { pct: 80 },
          functions: { pct: 85 },
          branches: { pct: 70 },
          statements: { pct: 82 }
        }
      }

      const mockData2 = {
        total: {
          lines: { pct: 90 },
          functions: { pct: 95 },
          branches: { pct: 80 },
          statements: { pct: 92 }
        }
      }

      vi.mocked(fs.readFile)
        .mockResolvedValueOnce(JSON.stringify(mockData1))
        .mockResolvedValueOnce(JSON.stringify(mockData2))

      const coverage = await monitor.collectCoverage([
        'coverage1/coverage-final.json',
        'coverage2/coverage-final.json'
      ])

      // 應該是平均值
      expect(coverage.lines).toBe(85)
      expect(coverage.functions).toBe(90)
      expect(coverage.branches).toBe(75)
      expect(coverage.statements).toBe(87)
    })

    it('應該處理無效的覆蓋率文件', async () => {
      vi.mocked(fs.readFile).mockRejectedValue(new Error('File not found'))

      await expect(monitor.collectCoverage(['invalid-file.json']))
        .rejects.toThrow('No coverage data found')
    })
  })

  describe('閾值檢查', () => {
    beforeEach(async () => {
      vi.mocked(fs.mkdir).mockResolvedValue(undefined)
      vi.mocked(fs.readFile).mockRejectedValue(new Error('File not found'))
      await monitor.initialize()
    })

    it('應該通過閾值檢查', () => {
      const coverage = {
        lines: 90,
        functions: 88,
        branches: 85,
        statements: 92,
        files: {}
      }

      const result = monitor.checkThresholds(coverage)

      expect(result.passed).toBe(true)
      expect(result.failures).toHaveLength(0)
    })

    it('應該檢測閾值失敗', () => {
      const coverage = {
        lines: 70,  // 低於 85%
        functions: 80, // 低於 85%
        branches: 75,  // 低於 80%
        statements: 75, // 低於 85%
        files: {}
      }

      const result = monitor.checkThresholds(coverage)

      expect(result.passed).toBe(false)
      expect(result.failures).toHaveLength(4)
      expect(result.failures[0]).toContain('Lines coverage 70.0% below threshold 85%')
    })

    it('應該生成警告', () => {
      const coverage = {
        lines: 75,  // 在警告閾值以下
        functions: 85,
        branches: 80,
        statements: 85,
        files: {
          'src/test.ts': { lines: 50, functions: 60, branches: 40, statements: 55 }
        }
      }

      const result = monitor.checkThresholds(coverage)

      expect(result.warnings.length).toBeGreaterThan(0)
      expect(result.warnings.some(w => w.includes('below warning threshold'))).toBe(true)
    })
  })

  describe('趨勢分析', () => {
    it('應該檢測改善趨勢', () => {
      // 模擬歷史數據
      const history = [
        {
          timestamp: new Date('2025-01-01'),
          coverage: { lines: 80, functions: 75, branches: 70, statements: 80 },
          passed: false
        },
        {
          timestamp: new Date('2025-01-02'),
          coverage: { lines: 85, functions: 80, branches: 75, statements: 85 },
          passed: true
        }
      ]

      // 使用反射設置私有屬性
      ;(monitor as any).coverageHistory = history

      const trends = monitor.analyzeTrends()

      expect(trends.trend).toBe('improving')
      expect(trends.changePercent).toBe(5)
      expect(trends.recommendations).toContain('覆蓋率呈上升趨勢，繼續保持')
    })

    it('應該檢測下降趨勢', () => {
      const history = [
        {
          timestamp: new Date('2025-01-01'),
          coverage: { lines: 90, functions: 85, branches: 80, statements: 90 },
          passed: true
        },
        {
          timestamp: new Date('2025-01-02'),
          coverage: { lines: 80, functions: 75, branches: 70, statements: 80 },
          passed: false
        }
      ]

      ;(monitor as any).coverageHistory = history

      const trends = monitor.analyzeTrends()

      expect(trends.trend).toBe('declining')
      expect(trends.changePercent).toBe(-10)
      expect(trends.recommendations).toContain('覆蓋率呈下降趨勢，建議檢查最近的代碼變更')
    })

    it('應該檢測穩定趨勢', () => {
      const history = [
        {
          timestamp: new Date('2025-01-01'),
          coverage: { lines: 85, functions: 80, branches: 75, statements: 85 },
          passed: true
        },
        {
          timestamp: new Date('2025-01-02'),
          coverage: { lines: 85.2, functions: 80.1, branches: 75.3, statements: 85.1 },
          passed: true
        }
      ]

      ;(monitor as any).coverageHistory = history

      const trends = monitor.analyzeTrends()

      expect(trends.trend).toBe('stable')
      expect(Math.abs(trends.changePercent)).toBeLessThan(0.5)
    })

    it('應該處理數據不足的情況', () => {
      ;(monitor as any).coverageHistory = []

      const trends = monitor.analyzeTrends()

      expect(trends.trend).toBe('stable')
      expect(trends.changePercent).toBe(0)
      expect(trends.recommendations).toContain('需要更多歷史數據來分析趨勢')
    })
  })

  describe('報告生成', () => {
    beforeEach(async () => {
      vi.mocked(fs.mkdir).mockResolvedValue(undefined)
      vi.mocked(fs.readFile).mockRejectedValue(new Error('File not found'))
      vi.mocked(fs.writeFile).mockResolvedValue(undefined)
      await monitor.initialize()
    })

    it('應該生成完整報告', async () => {
      const coverage = {
        lines: 85,
        functions: 80,
        branches: 75,
        statements: 87,
        files: {}
      }

      const report = await monitor.generateReport(coverage)

      expect(report.timestamp).toBeInstanceOf(Date)
      expect(report.coverage).toEqual(coverage)
      expect(report.passed).toBe(true)
      expect(report.trends).toBeDefined()
      expect(report.recommendations).toBeDefined()
    })

    it('應該保存報告到文件', async () => {
      const coverage = {
        lines: 85,
        functions: 80,
        branches: 75,
        statements: 87,
        files: {}
      }

      await monitor.generateReport(coverage)

      expect(vi.mocked(fs.writeFile)).toHaveBeenCalledWith(
        expect.stringContaining('coverage-'),
        expect.stringContaining('"coverage"'),
        'utf-8'
      )
    })

    it('應該限制歷史記錄大小', async () => {
      // 設置小的歷史大小
      const smallMonitor = new CoverageMonitor({
        historySize: 2,
        outputDir: mockOutputDir
      })

      vi.mocked(fs.mkdir).mockResolvedValue(undefined)
      vi.mocked(fs.readFile).mockRejectedValue(new Error('File not found'))
      await smallMonitor.initialize()

      const coverage = {
        lines: 85,
        functions: 80,
        branches: 75,
        statements: 87,
        files: {}
      }

      // 生成 3 個報告
      await smallMonitor.generateReport(coverage)
      await smallMonitor.generateReport(coverage)
      await smallMonitor.generateReport(coverage)

      const history = smallMonitor.getCoverageHistory()
      expect(history).toHaveLength(2) // 應該只保留最近的 2 個
    })
  })

  describe('告警生成', () => {
    beforeEach(async () => {
      vi.mocked(fs.mkdir).mockResolvedValue(undefined)
      vi.mocked(fs.readFile).mockRejectedValue(new Error('File not found'))
      vi.mocked(fs.writeFile).mockResolvedValue(undefined)
      await monitor.initialize()
    })

    it('應該生成嚴重告警', async () => {
      const coverage = {
        lines: 65, // 低於嚴重閾值 70%
        functions: 80,
        branches: 75,
        statements: 87,
        files: {}
      }

      await monitor.generateReport(coverage)

      // 檢查是否調用了保存告警的方法
      expect(vi.mocked(fs.writeFile)).toHaveBeenCalledWith(
        expect.stringContaining('coverage-alerts.json'),
        expect.stringContaining('critical'),
        'utf-8'
      )
    })

    it('應該生成警告告警', async () => {
      const coverage = {
        lines: 75, // 在警告閾值以下但高於嚴重閾值
        functions: 80,
        branches: 75,
        statements: 87,
        files: {}
      }

      await monitor.generateReport(coverage)

      expect(vi.mocked(fs.writeFile)).toHaveBeenCalledWith(
        expect.stringContaining('coverage-alerts.json'),
        expect.stringContaining('warning'),
        'utf-8'
      )
    })

    it('不應該為高覆蓋率生成告警', async () => {
      const coverage = {
        lines: 90, // 高於所有閾值
        functions: 88,
        branches: 85,
        statements: 92,
        files: {}
      }

      await monitor.generateReport(coverage)

      // 檢查沒有調用保存告警
      const writeFileCalls = vi.mocked(fs.writeFile).mock.calls
      const alertCalls = writeFileCalls.filter(call => 
        call[0].toString().includes('coverage-alerts.json')
      )
      expect(alertCalls).toHaveLength(0)
    })
  })

  describe('文件過濾', () => {
    beforeEach(async () => {
      vi.mocked(fs.mkdir).mockResolvedValue(undefined)
      vi.mocked(fs.readFile).mockRejectedValue(new Error('File not found'))
      await monitor.initialize()
    })

    it('應該正確過濾包含和排除的文件', () => {
      const testMonitor = new CoverageMonitor({
        includePatterns: ['src/**/*.ts'],
        excludePatterns: ['**/*.test.ts']
      })

      // 測試模式匹配邏輯
      const matchPattern = (testMonitor as any).matchPattern.bind(testMonitor)

      expect(matchPattern('src/utils/helper.ts', 'src/**/*.ts')).toBe(true)
      expect(matchPattern('src/utils/helper.test.ts', '**/*.test.ts')).toBe(true)
      expect(matchPattern('lib/utils/helper.ts', 'src/**/*.ts')).toBe(false)
    })
  })

  describe('錯誤處理', () => {
    it('應該處理文件讀取錯誤', async () => {
      vi.mocked(fs.mkdir).mockResolvedValue(undefined)
      vi.mocked(fs.readFile).mockRejectedValue(new Error('Permission denied'))

      await monitor.initialize()

      // 應該不拋出錯誤，而是使用空歷史
      const history = monitor.getCoverageHistory()
      expect(history).toHaveLength(0)
    })

    it('應該處理無效的 JSON 數據', async () => {
      vi.mocked(fs.mkdir).mockResolvedValue(undefined)
      vi.mocked(fs.readFile)
        .mockRejectedValueOnce(new Error('File not found')) // 初始化時
        .mockResolvedValueOnce('invalid json') // 收集覆蓋率時

      await monitor.initialize()

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      await expect(monitor.collectCoverage(['invalid.json']))
        .rejects.toThrow('No coverage data found')

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to parse coverage file'),
        expect.any(Error)
      )

      consoleSpy.mockRestore()
    })

    it('應該處理目錄創建失敗', async () => {
      vi.mocked(fs.mkdir).mockRejectedValue(new Error('Permission denied'))

      await expect(monitor.initialize()).rejects.toThrow('Permission denied')
    })
  })

  describe('性能測試', () => {
    it('應該在合理時間內處理大量文件', async () => {
      vi.mocked(fs.mkdir).mockResolvedValue(undefined)
      vi.mocked(fs.readFile).mockRejectedValue(new Error('File not found'))
      await monitor.initialize()

      const mockCoverageData = {
        total: {
          lines: { pct: 85 },
          functions: { pct: 80 },
          branches: { pct: 75 },
          statements: { pct: 87 }
        }
      }

      // 模擬大量文件
      const files = Array.from({ length: 100 }, (_, i) => `coverage${i}.json`)
      vi.mocked(fs.readFile).mockResolvedValue(JSON.stringify(mockCoverageData))

      const startTime = Date.now()
      await monitor.collectCoverage(files)
      const endTime = Date.now()

      // 應該在 1 秒內完成
      expect(endTime - startTime).toBeLessThan(1000)
    })
  })
})