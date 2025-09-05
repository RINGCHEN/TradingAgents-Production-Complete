/**
 * CoverageMonitor - 測試覆蓋率監控系統
 * 負責收集、分析和監控代碼覆蓋率數據
 */

import { CoverageData, CoverageThreshold, CoverageReport, CoverageAlert } from './types'
import { promises as fs } from 'fs'
import { join, dirname, relative } from 'path'
import { glob } from 'glob'

export interface CoverageMonitorConfig {
  thresholds: CoverageThreshold
  includePatterns: string[]
  excludePatterns: string[]
  outputDir: string
  historySize: number
  alertEnabled: boolean
  alertThresholds: {
    warning: number
    critical: number
  }
}

export class CoverageMonitor {
  private config: CoverageMonitorConfig
  private coverageHistory: CoverageReport[] = []
  private currentCoverage: CoverageData | null = null

  constructor(config: Partial<CoverageMonitorConfig> = {}) {
    this.config = {
      thresholds: {
        lines: 85,
        functions: 85,
        branches: 85,
        statements: 85
      },
      includePatterns: ['src/**/*.{ts,tsx}'],
      excludePatterns: [
        '**/*.test.{ts,tsx}',
        '**/*.spec.{ts,tsx}',
        '**/*.stories.{ts,tsx}',
        '**/node_modules/**',
        '**/dist/**',
        '**/coverage/**'
      ],
      outputDir: './coverage-reports',
      historySize: 30,
      alertEnabled: true,
      alertThresholds: {
        warning: 80,
        critical: 70
      },
      ...config
    }
  }

  /**
   * 初始化覆蓋率監控
   */
  async initialize(): Promise<void> {
    console.log('📊 Initializing coverage monitor...')
    
    // 確保輸出目錄存在
    await this.ensureOutputDirectory()
    
    // 載入歷史數據
    await this.loadCoverageHistory()
    
    console.log('✅ Coverage monitor initialized')
  }

  /**
   * 收集覆蓋率數據
   */
  async collectCoverage(coverageFiles: string[]): Promise<CoverageData> {
    console.log('📈 Collecting coverage data...')
    
    const aggregatedCoverage: CoverageData = {
      lines: 0,
      functions: 0,
      branches: 0,
      statements: 0,
      files: {}
    }

    let totalFiles = 0
    
    for (const coverageFile of coverageFiles) {
      try {
        const coverage = await this.parseCoverageFile(coverageFile)
        if (coverage) {
          this.mergeCoverage(aggregatedCoverage, coverage)
          totalFiles++
        }
      } catch (error) {
        console.warn(`Failed to parse coverage file ${coverageFile}:`, error)
      }
    }

    // 計算平均覆蓋率
    if (totalFiles > 0) {
      aggregatedCoverage.lines /= totalFiles
      aggregatedCoverage.functions /= totalFiles
      aggregatedCoverage.branches /= totalFiles
      aggregatedCoverage.statements /= totalFiles
    }

    // 過濾文件覆蓋率
    aggregatedCoverage.files = await this.filterFileCoverage(aggregatedCoverage.files || {})

    this.currentCoverage = aggregatedCoverage
    
    console.log(`📊 Coverage collected: ${aggregatedCoverage.lines.toFixed(1)}% lines`)
    
    return aggregatedCoverage
  }

  /**
   * 分析覆蓋率趨勢
   */
  analyzeTrends(): {
    trend: 'improving' | 'declining' | 'stable'
    changePercent: number
    recommendations: string[]
  } {
    if (this.coverageHistory.length < 2) {
      return {
        trend: 'stable',
        changePercent: 0,
        recommendations: ['需要更多歷史數據來分析趨勢']
      }
    }

    const latest = this.coverageHistory[this.coverageHistory.length - 1]
    const previous = this.coverageHistory[this.coverageHistory.length - 2]
    
    const changePercent = latest.coverage.lines - previous.coverage.lines
    
    let trend: 'improving' | 'declining' | 'stable'
    if (Math.abs(changePercent) < 0.5) {
      trend = 'stable'
    } else if (changePercent > 0) {
      trend = 'improving'
    } else {
      trend = 'declining'
    }

    const recommendations = this.generateRecommendations(latest.coverage, trend)

    return { trend, changePercent, recommendations }
  }

  /**
   * 檢查覆蓋率閾值
   */
  checkThresholds(coverage: CoverageData): {
    passed: boolean
    failures: string[]
    warnings: string[]
  } {
    const failures: string[] = []
    const warnings: string[] = []

    // 檢查全局閾值
    if (coverage.lines < this.config.thresholds.lines) {
      failures.push(`Lines coverage ${coverage.lines.toFixed(1)}% below threshold ${this.config.thresholds.lines}%`)
    }
    if (coverage.functions < this.config.thresholds.functions) {
      failures.push(`Functions coverage ${coverage.functions.toFixed(1)}% below threshold ${this.config.thresholds.functions}%`)
    }
    if (coverage.branches < this.config.thresholds.branches) {
      failures.push(`Branches coverage ${coverage.branches.toFixed(1)}% below threshold ${this.config.thresholds.branches}%`)
    }
    if (coverage.statements < this.config.thresholds.statements) {
      failures.push(`Statements coverage ${coverage.statements.toFixed(1)}% below threshold ${this.config.thresholds.statements}%`)
    }

    // 檢查警告閾值
    if (coverage.lines < this.config.alertThresholds.warning && coverage.lines >= this.config.alertThresholds.critical) {
      warnings.push(`Lines coverage ${coverage.lines.toFixed(1)}% is below warning threshold`)
    }

    // 檢查文件級別覆蓋率
    if (coverage.files) {
      Object.entries(coverage.files).forEach(([file, fileCoverage]) => {
        if (typeof fileCoverage === 'object' && fileCoverage.lines < this.config.thresholds.lines * 0.8) { // 文件閾值稍低
          warnings.push(`File ${file} has low coverage: ${fileCoverage.lines.toFixed(1)}%`)
        }
      })
    }

    return {
      passed: failures.length === 0,
      failures,
      warnings
    }
  }

  /**
   * 生成覆蓋率報告
   */
  async generateReport(coverage: CoverageData): Promise<CoverageReport> {
    const timestamp = new Date()
    const thresholdCheck = this.checkThresholds(coverage)
    const trends = this.analyzeTrends()
    
    const report: CoverageReport = {
      timestamp,
      coverage,
      thresholds: this.config.thresholds,
      passed: thresholdCheck.passed,
      failures: thresholdCheck.failures,
      warnings: thresholdCheck.warnings,
      trends,
      uncoveredFiles: await this.findUncoveredFiles(coverage),
      recommendations: trends.recommendations
    }

    // 添加到歷史記錄
    this.coverageHistory.push(report)
    
    // 限制歷史記錄大小
    if (this.coverageHistory.length > this.config.historySize) {
      this.coverageHistory = this.coverageHistory.slice(-this.config.historySize)
    }

    // 保存報告
    await this.saveCoverageReport(report)
    await this.saveCoverageHistory()

    // 生成告警
    if (this.config.alertEnabled) {
      await this.generateAlerts(report)
    }

    return report
  }

  /**
   * 獲取覆蓋率歷史
   */
  getCoverageHistory(): CoverageReport[] {
    return [...this.coverageHistory]
  }

  /**
   * 獲取當前覆蓋率
   */
  getCurrentCoverage(): CoverageData | null {
    return this.currentCoverage
  }

  /**
   * 找出未覆蓋的文件
   */
  private async findUncoveredFiles(coverage: CoverageData): Promise<string[]> {
    const allFiles = await this.getAllSourceFiles()
    const coveredFiles = Object.keys(coverage.files || {})
    
    return allFiles.filter(file => !coveredFiles.includes(file))
  }

  /**
   * 獲取所有源文件
   */
  private async getAllSourceFiles(): Promise<string[]> {
    const files: string[] = []
    
    for (const pattern of this.config.includePatterns) {
      const matchedFiles = await glob(pattern, {
        ignore: this.config.excludePatterns
      })
      files.push(...matchedFiles)
    }
    
    return [...new Set(files)] // 去重
  }

  /**
   * 解析覆蓋率文件
   */
  private async parseCoverageFile(filePath: string): Promise<CoverageData | null> {
    try {
      const content = await fs.readFile(filePath, 'utf-8')
      
      // 支援多種覆蓋率格式
      if (filePath.endsWith('.json')) {
        return this.parseJsonCoverage(content)
      } else if (filePath.endsWith('.lcov')) {
        return this.parseLcovCoverage(content)
      } else if (filePath.includes('clover')) {
        return this.parseCloverCoverage(content)
      }
      
      return null
    } catch (error) {
      console.warn(`Failed to read coverage file ${filePath}:`, error)
      return null
    }
  }

  /**
   * 解析 JSON 格式覆蓋率
   */
  private parseJsonCoverage(content: string): CoverageData | null {
    try {
      const data = JSON.parse(content)
      
      // Istanbul/NYC 格式
      if (data.total) {
        return {
          lines: data.total.lines.pct,
          functions: data.total.functions.pct,
          branches: data.total.branches.pct,
          statements: data.total.statements.pct,
          files: Object.keys(data)
            .filter(key => key !== 'total')
            .reduce((acc, key) => {
              acc[key] = {
                lines: data[key].lines.pct,
                functions: data[key].functions.pct,
                branches: data[key].branches.pct,
                statements: data[key].statements.pct
              }
              return acc
            }, {} as any)
        }
      }
      
      // V8 格式
      if (data.result) {
        return this.parseV8Coverage(data.result)
      }
      
      return null
    } catch (error) {
      console.warn('Failed to parse JSON coverage:', error)
      return null
    }
  }

  /**
   * 解析 LCOV 格式覆蓋率
   */
  private parseLcovCoverage(content: string): CoverageData | null {
    try {
      const lines = content.split('\n')
      const files: Record<string, any> = {}
      let currentFile = ''
      
      let totalLines = 0, coveredLines = 0
      let totalFunctions = 0, coveredFunctions = 0
      let totalBranches = 0, coveredBranches = 0
      
      let currentFound = 0
      
      for (const line of lines) {
        if (line.startsWith('SF:')) {
          currentFile = line.substring(3)
          files[currentFile] = { lines: 0, functions: 0, branches: 0, statements: 0 }
        } else if (line.startsWith('LF:')) {
          currentFound = parseInt(line.substring(3))
          totalLines += currentFound
        } else if (line.startsWith('LH:')) {
          const hit = parseInt(line.substring(3))
          coveredLines += hit
          if (currentFile) {
            files[currentFile].lines = currentFound > 0 ? (hit / currentFound) * 100 : 0
          }
        } else if (line.startsWith('FNF:')) {
          currentFound = parseInt(line.substring(4))
          totalFunctions += currentFound
        } else if (line.startsWith('FNH:')) {
          const hit = parseInt(line.substring(4))
          coveredFunctions += hit
          if (currentFile) {
            files[currentFile].functions = currentFound > 0 ? (hit / currentFound) * 100 : 0
          }
        } else if (line.startsWith('BRF:')) {
          currentFound = parseInt(line.substring(4))
          totalBranches += currentFound
        } else if (line.startsWith('BRH:')) {
          const hit = parseInt(line.substring(4))
          coveredBranches += hit
          if (currentFile) {
            files[currentFile].branches = currentFound > 0 ? (hit / currentFound) * 100 : 0
          }
        }
      }
      
      return {
        lines: totalLines > 0 ? (coveredLines / totalLines) * 100 : 0,
        functions: totalFunctions > 0 ? (coveredFunctions / totalFunctions) * 100 : 0,
        branches: totalBranches > 0 ? (coveredBranches / totalBranches) * 100 : 0,
        statements: totalLines > 0 ? (coveredLines / totalLines) * 100 : 0, // LCOV 中 statements 通常等於 lines
        files
      }
    } catch (error) {
      console.warn('Failed to parse LCOV coverage:', error)
      return null
    }
  }

  /**
   * 解析 Clover 格式覆蓋率
   */
  private parseCloverCoverage(content: string): CoverageData | null {
    // TODO: 實現 Clover XML 格式解析
    console.warn('Clover coverage format not yet implemented')
    return null
  }

  /**
   * 解析 V8 覆蓋率
   */
  private parseV8Coverage(result: any[]): CoverageData {
    let totalLines = 0, coveredLines = 0
    let totalFunctions = 0, coveredFunctions = 0
    let totalBranches = 0, coveredBranches = 0
    
    const files: Record<string, any> = {}
    
    for (const file of result) {
      const filePath = relative(process.cwd(), file.url.replace('file://', ''))
      
      let fileLines = 0, fileCoveredLines = 0
      let fileFunctions = 0, fileCoveredFunctions = 0
      let fileBranches = 0, fileCoveredBranches = 0
      
      // 處理函數覆蓋率
      for (const func of file.functions || []) {
        fileFunctions++
        totalFunctions++
        if (func.ranges.some((range: any) => range.count > 0)) {
          fileCoveredFunctions++
          coveredFunctions++
        }
      }
      
      // 處理行覆蓋率
      for (const range of file.ranges || []) {
        const lineCount = range.end.line - range.start.line + 1
        fileLines += lineCount
        totalLines += lineCount
        
        if (range.count > 0) {
          fileCoveredLines += lineCount
          coveredLines += lineCount
        }
      }
      
      files[filePath] = {
        lines: fileLines > 0 ? (fileCoveredLines / fileLines) * 100 : 0,
        functions: fileFunctions > 0 ? (fileCoveredFunctions / fileFunctions) * 100 : 0,
        branches: fileBranches > 0 ? (fileCoveredBranches / fileBranches) * 100 : 0,
        statements: fileLines > 0 ? (fileCoveredLines / fileLines) * 100 : 0
      }
    }
    
    return {
      lines: totalLines > 0 ? (coveredLines / totalLines) * 100 : 0,
      functions: totalFunctions > 0 ? (coveredFunctions / totalFunctions) * 100 : 0,
      branches: totalBranches > 0 ? (coveredBranches / totalBranches) * 100 : 0,
      statements: totalLines > 0 ? (coveredLines / totalLines) * 100 : 0,
      files
    }
  }

  /**
   * 合併覆蓋率數據
   */
  private mergeCoverage(target: CoverageData, source: CoverageData): void {
    target.lines += source.lines
    target.functions += source.functions
    target.branches += source.branches
    target.statements += source.statements
    
    if (source.files) {
      target.files = { ...target.files, ...source.files }
    }
  }

  /**
   * 過濾文件覆蓋率
   */
  private async filterFileCoverage(files: Record<string, any>): Promise<Record<string, any>> {
    const filtered: Record<string, any> = {}
    
    for (const [filePath, coverage] of Object.entries(files)) {
      // 檢查是否符合包含模式
      const included = this.config.includePatterns.some(pattern => 
        this.matchPattern(filePath, pattern)
      )
      
      // 檢查是否符合排除模式
      const excluded = this.config.excludePatterns.some(pattern => 
        this.matchPattern(filePath, pattern)
      )
      
      if (included && !excluded) {
        filtered[filePath] = coverage
      }
    }
    
    return filtered
  }

  /**
   * 模式匹配
   */
  private matchPattern(filePath: string, pattern: string): boolean {
    // 簡單的 glob 模式匹配
    const regex = pattern
      .replace(/\*\*/g, '.*')
      .replace(/\*/g, '[^/]*')
      .replace(/\?/g, '.')
    
    return new RegExp(`^${regex}$`).test(filePath)
  }

  /**
   * 生成建議
   */
  private generateRecommendations(coverage: CoverageData, trend: string): string[] {
    const recommendations: string[] = []
    
    if (coverage.lines < this.config.thresholds.lines) {
      recommendations.push(`增加單元測試以提高行覆蓋率至 ${this.config.thresholds.lines}%`)
    }
    
    if (coverage.functions < this.config.thresholds.functions) {
      recommendations.push(`為未測試的函數添加測試用例`)
    }
    
    if (coverage.branches < this.config.thresholds.branches) {
      recommendations.push(`添加測試以覆蓋更多分支條件`)
    }
    
    if (trend === 'declining') {
      recommendations.push('覆蓋率呈下降趨勢，建議檢查最近的代碼變更')
    }
    
    // 檢查文件級別建議
    if (coverage.files) {
      const lowCoverageFiles = Object.entries(coverage.files)
        .filter(([, fileCoverage]) => typeof fileCoverage === 'object' && fileCoverage.lines < 50)
        .slice(0, 5) // 只顯示前5個
      
      if (lowCoverageFiles.length > 0) {
        recommendations.push(`優先為以下文件添加測試: ${lowCoverageFiles.map(([file]) => file).join(', ')}`)
      }
    }
    
    return recommendations
  }

  /**
   * 生成告警
   */
  private async generateAlerts(report: CoverageReport): Promise<void> {
    const alerts: CoverageAlert[] = []
    
    // 檢查關鍵閾值
    if (report.coverage.lines < this.config.alertThresholds.critical) {
      alerts.push({
        type: 'critical',
        message: `代碼覆蓋率 ${report.coverage.lines.toFixed(1)}% 低於關鍵閾值 ${this.config.alertThresholds.critical}%`,
        timestamp: report.timestamp,
        coverage: report.coverage.lines
      })
    } else if (report.coverage.lines < this.config.alertThresholds.warning) {
      alerts.push({
        type: 'warning',
        message: `代碼覆蓋率 ${report.coverage.lines.toFixed(1)}% 低於警告閾值 ${this.config.alertThresholds.warning}%`,
        timestamp: report.timestamp,
        coverage: report.coverage.lines
      })
    }
    
    // 檢查趨勢告警
    if (report.trends.trend === 'declining' && Math.abs(report.trends.changePercent) > 5) {
      alerts.push({
        type: 'warning',
        message: `代碼覆蓋率下降 ${Math.abs(report.trends.changePercent).toFixed(1)}%`,
        timestamp: report.timestamp,
        coverage: report.coverage.lines
      })
    }
    
    // 保存告警
    if (alerts.length > 0) {
      await this.saveAlerts(alerts)
      console.warn(`⚠️ Generated ${alerts.length} coverage alerts`)
    }
  }

  /**
   * 保存覆蓋率報告
   */
  private async saveCoverageReport(report: CoverageReport): Promise<void> {
    const filename = `coverage-${report.timestamp.toISOString().split('T')[0]}.json`
    const filepath = join(this.config.outputDir, filename)
    
    await fs.writeFile(filepath, JSON.stringify(report, null, 2), 'utf-8')
  }

  /**
   * 保存覆蓋率歷史
   */
  private async saveCoverageHistory(): Promise<void> {
    const filepath = join(this.config.outputDir, 'coverage-history.json')
    await fs.writeFile(filepath, JSON.stringify(this.coverageHistory, null, 2), 'utf-8')
  }

  /**
   * 載入覆蓋率歷史
   */
  private async loadCoverageHistory(): Promise<void> {
    try {
      const filepath = join(this.config.outputDir, 'coverage-history.json')
      const content = await fs.readFile(filepath, 'utf-8')
      this.coverageHistory = JSON.parse(content)
    } catch (error) {
      // 文件不存在或解析失敗，使用空歷史
      this.coverageHistory = []
    }
  }

  /**
   * 保存告警
   */
  private async saveAlerts(alerts: CoverageAlert[]): Promise<void> {
    const filepath = join(this.config.outputDir, 'coverage-alerts.json')
    
    let existingAlerts: CoverageAlert[] = []
    try {
      const content = await fs.readFile(filepath, 'utf-8')
      existingAlerts = JSON.parse(content)
    } catch {
      // 文件不存在，使用空數組
    }
    
    const allAlerts = [...existingAlerts, ...alerts]
    
    // 只保留最近的告警
    const recentAlerts = allAlerts
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, 100)
    
    await fs.writeFile(filepath, JSON.stringify(recentAlerts, null, 2), 'utf-8')
  }

  /**
   * 確保輸出目錄存在
   */
  private async ensureOutputDirectory(): Promise<void> {
    try {
      await fs.mkdir(this.config.outputDir, { recursive: true })
    } catch (error) {
      console.error(`Failed to create output directory: ${error}`)
      throw error
    }
  }
}