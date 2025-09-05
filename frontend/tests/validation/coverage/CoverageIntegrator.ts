/**
 * CoverageIntegrator - 覆蓋率監控整合系統
 * 整合多種覆蓋率工具和報告格式，提供統一的監控介面
 */

import { CoverageMonitor, CoverageMonitorConfig } from './CoverageMonitor'
import { 
  CoverageMetrics, 
  CoverageThreshold, 
  CoverageIntegration,
  CoverageReporter,
  CoverageNotifier,
  CoverageEvent,
  CoverageEventListener,
  CoverageGoal,
  CoverageCI
} from './types'
import { promises as fs } from 'fs'
import { join } from 'path'
import { EventEmitter } from 'events'

export interface CoverageIntegratorConfig {
  monitor: Partial<CoverageMonitorConfig>
  integrations: {
    vitest: boolean
    cypress: boolean
    jest: boolean
    istanbul: boolean
  }
  reporters: {
    html: boolean
    json: boolean
    lcov: boolean
    console: boolean
    slack?: {
      webhook: string
      channel: string
    }
    email?: {
      smtp: any
      recipients: string[]
    }
  }
  ci: {
    enabled: boolean
    failOnThreshold: boolean
    commentOnPR: boolean
    statusChecks: boolean
  }
  goals: CoverageGoal[]
  webhooks: string[]
}

export class CoverageIntegrator extends EventEmitter {
  private monitor: CoverageMonitor
  private config: CoverageIntegratorConfig
  private integrations: Map<string, CoverageIntegration> = new Map()
  private reporters: Map<string, CoverageReporter> = new Map()
  private notifiers: Map<string, CoverageNotifier> = new Map()
  private isInitialized = false

  constructor(config: Partial<CoverageIntegratorConfig> = {}) {
    super()
    
    this.config = {
      monitor: {},
      integrations: {
        vitest: true,
        cypress: true,
        jest: false,
        istanbul: true
      },
      reporters: {
        html: true,
        json: true,
        lcov: true,
        console: true
      },
      ci: {
        enabled: true,
        failOnThreshold: true,
        commentOnPR: true,
        statusChecks: true
      },
      goals: [],
      webhooks: [],
      ...config
    }

    this.monitor = new CoverageMonitor(this.config.monitor)
  }

  /**
   * 初始化覆蓋率整合系統
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return
    }

    console.log('🚀 Initializing coverage integrator...')

    // 初始化監控器
    await this.monitor.initialize()

    // 註冊整合工具
    await this.registerIntegrations()

    // 註冊報告器
    await this.registerReporters()

    // 註冊通知器
    await this.registerNotifiers()

    // 設置事件監聽
    this.setupEventListeners()

    this.isInitialized = true
    console.log('✅ Coverage integrator initialized')
  }

  /**
   * 執行完整的覆蓋率收集和分析
   */
  async runCoverageAnalysis(): Promise<CoverageMetrics> {
    if (!this.isInitialized) {
      await this.initialize()
    }

    console.log('📊 Starting coverage analysis...')
    
    this.emit('analysis:start')

    try {
      // 收集覆蓋率數據
      const metrics = await this.collectCoverage()
      
      // 分析和驗證
      const analysis = await this.analyzeCoverage(metrics)
      
      // 生成報告
      await this.generateReports(metrics)
      
      // 發送通知
      await this.sendNotifications(metrics, analysis)
      
      // CI 整合
      if (this.config.ci.enabled) {
        await this.handleCIIntegration(metrics)
      }

      this.emit('analysis:complete', metrics)
      
      console.log('✅ Coverage analysis completed')
      return metrics

    } catch (error) {
      this.emit('analysis:error', error)
      console.error('❌ Coverage analysis failed:', error)
      throw error
    }
  }

  /**
   * 收集覆蓋率數據
   */
  private async collectCoverage(): Promise<CoverageMetrics> {
    const coverageFiles: string[] = []
    
    // 從各個整合工具收集覆蓋率
    for (const [name, integration] of this.integrations) {
      if (await integration.isAvailable()) {
        console.log(`📈 Collecting coverage from ${name}...`)
        try {
          const metrics = await integration.collect()
          // 這裡需要合併多個來源的覆蓋率數據
          // 暫時返回第一個可用的
          return metrics
        } catch (error) {
          console.warn(`Failed to collect coverage from ${name}:`, error)
        }
      }
    }

    // 如果沒有整合工具可用，嘗試直接讀取覆蓋率文件
    const possiblePaths = [
      'coverage/coverage-final.json',
      'coverage/lcov.info',
      'coverage/clover.xml',
      'nyc_output/coverage-final.json'
    ]

    for (const path of possiblePaths) {
      try {
        await fs.access(path)
        coverageFiles.push(path)
      } catch {
        // 文件不存在，繼續檢查下一個
      }
    }

    if (coverageFiles.length === 0) {
      throw new Error('No coverage data found')
    }

    // 使用監控器收集覆蓋率
    const coverageData = await this.monitor.collectCoverage(coverageFiles)
    
    return {
      timestamp: new Date(),
      overall: coverageData,
      files: [], // TODO: 從 coverageData.files 轉換
      summary: {
        totalLines: 0,
        coveredLines: 0,
        totalFunctions: 0,
        coveredFunctions: 0,
        totalBranches: 0,
        coveredBranches: 0,
        totalStatements: 0,
        coveredStatements: 0
      }
    }
  }

  /**
   * 分析覆蓋率數據
   */
  private async analyzeCoverage(metrics: CoverageMetrics): Promise<any> {
    console.log('🔍 Analyzing coverage data...')
    
    // 檢查閾值
    const thresholdCheck = this.monitor.checkThresholds(metrics.overall)
    
    // 分析趨勢
    const trends = this.monitor.analyzeTrends()
    
    // 生成報告
    const report = await this.monitor.generateReport(metrics.overall)
    
    return {
      thresholdCheck,
      trends,
      report
    }
  }

  /**
   * 生成報告
   */
  private async generateReports(metrics: CoverageMetrics): Promise<void> {
    console.log('📄 Generating coverage reports...')
    
    const reportPromises: Promise<void>[] = []
    
    for (const [name, reporter] of this.reporters) {
      if (this.isReporterEnabled(name)) {
        reportPromises.push(
          reporter.generate(metrics).then(output => {
            console.log(`✅ Generated ${name} report: ${reporter.getOutputPath()}`)
          }).catch(error => {
            console.warn(`Failed to generate ${name} report:`, error)
          })
        )
      }
    }
    
    await Promise.allSettled(reportPromises)
  }

  /**
   * 發送通知
   */
  private async sendNotifications(metrics: CoverageMetrics, analysis: any): Promise<void> {
    if (analysis.thresholdCheck.failures.length === 0 && analysis.trends.trend !== 'declining') {
      return // 沒有需要通知的問題
    }

    console.log('📢 Sending coverage notifications...')
    
    const notificationPromises: Promise<void>[] = []
    
    for (const [name, notifier] of this.notifiers) {
      const alert = {
        type: analysis.thresholdCheck.failures.length > 0 ? 'critical' : 'warning' as const,
        message: this.formatNotificationMessage(metrics, analysis),
        timestamp: new Date(),
        coverage: metrics.overall.lines
      }
      
      notificationPromises.push(
        notifier.notify(alert).catch(error => {
          console.warn(`Failed to send ${name} notification:`, error)
        })
      )
    }
    
    await Promise.allSettled(notificationPromises)
  }

  /**
   * 處理 CI 整合
   */
  private async handleCIIntegration(metrics: CoverageMetrics): Promise<void> {
    console.log('🔧 Handling CI integration...')
    
    // 這裡可以實現 GitHub Actions、GitLab CI 等整合
    // 例如設置狀態檢查、添加 PR 評論等
    
    if (process.env.CI) {
      console.log('Running in CI environment')
      
      // 設置退出碼
      const thresholds: CoverageThreshold = {
        lines: 85,
        functions: 85,
        branches: 85,
        statements: 85
      }
      
      const shouldFail = this.shouldFailBuild(metrics, thresholds)
      
      if (shouldFail && this.config.ci.failOnThreshold) {
        console.error('❌ Coverage thresholds not met, failing build')
        process.exit(1)
      }
    }
  }

  /**
   * 註冊整合工具
   */
  private async registerIntegrations(): Promise<void> {
    // Vitest 整合
    if (this.config.integrations.vitest) {
      this.integrations.set('vitest', new VitestIntegration())
    }
    
    // Cypress 整合
    if (this.config.integrations.cypress) {
      this.integrations.set('cypress', new CypressIntegration())
    }
    
    // Jest 整合
    if (this.config.integrations.jest) {
      this.integrations.set('jest', new JestIntegration())
    }
    
    // Istanbul 整合
    if (this.config.integrations.istanbul) {
      this.integrations.set('istanbul', new IstanbulIntegration())
    }
  }

  /**
   * 註冊報告器
   */
  private async registerReporters(): Promise<void> {
    if (this.config.reporters.html) {
      this.reporters.set('html', new HtmlReporter())
    }
    
    if (this.config.reporters.json) {
      this.reporters.set('json', new JsonReporter())
    }
    
    if (this.config.reporters.lcov) {
      this.reporters.set('lcov', new LcovReporter())
    }
    
    if (this.config.reporters.console) {
      this.reporters.set('console', new ConsoleReporter())
    }
  }

  /**
   * 註冊通知器
   */
  private async registerNotifiers(): Promise<void> {
    if (this.config.reporters.slack) {
      this.notifiers.set('slack', new SlackNotifier(this.config.reporters.slack))
    }
    
    if (this.config.reporters.email) {
      this.notifiers.set('email', new EmailNotifier(this.config.reporters.email))
    }
  }

  /**
   * 設置事件監聽
   */
  private setupEventListeners(): void {
    this.on('analysis:start', () => {
      console.log('🎯 Coverage analysis started')
    })
    
    this.on('analysis:complete', (metrics: CoverageMetrics) => {
      console.log(`📊 Coverage: ${metrics.overall.lines.toFixed(1)}% lines`)
    })
    
    this.on('analysis:error', (error: Error) => {
      console.error('💥 Coverage analysis error:', error.message)
    })
  }

  /**
   * 檢查報告器是否啟用
   */
  private isReporterEnabled(name: string): boolean {
    return (this.config.reporters as any)[name] === true
  }

  /**
   * 格式化通知消息
   */
  private formatNotificationMessage(metrics: CoverageMetrics, analysis: any): string {
    const lines = [
      `📊 Coverage Report - ${new Date().toLocaleDateString()}`,
      `Lines: ${metrics.overall.lines.toFixed(1)}%`,
      `Functions: ${metrics.overall.functions.toFixed(1)}%`,
      `Branches: ${metrics.overall.branches.toFixed(1)}%`,
      `Statements: ${metrics.overall.statements.toFixed(1)}%`
    ]
    
    if (analysis.thresholdCheck.failures.length > 0) {
      lines.push('', '❌ Threshold Failures:')
      lines.push(...analysis.thresholdCheck.failures)
    }
    
    if (analysis.thresholdCheck.warnings.length > 0) {
      lines.push('', '⚠️ Warnings:')
      lines.push(...analysis.thresholdCheck.warnings)
    }
    
    if (analysis.trends.trend === 'declining') {
      lines.push('', `📉 Coverage declined by ${Math.abs(analysis.trends.changePercent).toFixed(1)}%`)
    }
    
    return lines.join('\n')
  }

  /**
   * 判斷是否應該讓構建失敗
   */
  private shouldFailBuild(metrics: CoverageMetrics, thresholds: CoverageThreshold): boolean {
    return (
      metrics.overall.lines < thresholds.lines ||
      metrics.overall.functions < thresholds.functions ||
      metrics.overall.branches < thresholds.branches ||
      metrics.overall.statements < thresholds.statements
    )
  }

  /**
   * 獲取覆蓋率歷史
   */
  getCoverageHistory(): any[] {
    return this.monitor.getCoverageHistory()
  }

  /**
   * 獲取當前覆蓋率
   */
  getCurrentCoverage(): any {
    return this.monitor.getCurrentCoverage()
  }
}

// 整合工具實現
class VitestIntegration implements CoverageIntegration {
  name = 'vitest'

  async isAvailable(): Promise<boolean> {
    try {
      await fs.access('vitest.config.ts')
      return true
    } catch {
      return false
    }
  }

  async collect(): Promise<CoverageMetrics> {
    // 實現 Vitest 覆蓋率收集
    throw new Error('Vitest integration not implemented')
  }

  configure(config: any): void {
    // 配置 Vitest 整合
  }
}

class CypressIntegration implements CoverageIntegration {
  name = 'cypress'

  async isAvailable(): Promise<boolean> {
    try {
      await fs.access('cypress.config.ts')
      return true
    } catch {
      return false
    }
  }

  async collect(): Promise<CoverageMetrics> {
    // 實現 Cypress 覆蓋率收集
    throw new Error('Cypress integration not implemented')
  }

  configure(config: any): void {
    // 配置 Cypress 整合
  }
}

class JestIntegration implements CoverageIntegration {
  name = 'jest'

  async isAvailable(): Promise<boolean> {
    try {
      await fs.access('jest.config.js')
      return true
    } catch {
      return false
    }
  }

  async collect(): Promise<CoverageMetrics> {
    // 實現 Jest 覆蓋率收集
    throw new Error('Jest integration not implemented')
  }

  configure(config: any): void {
    // 配置 Jest 整合
  }
}

class IstanbulIntegration implements CoverageIntegration {
  name = 'istanbul'

  async isAvailable(): Promise<boolean> {
    try {
      await fs.access('coverage/coverage-final.json')
      return true
    } catch {
      return false
    }
  }

  async collect(): Promise<CoverageMetrics> {
    // 實現 Istanbul 覆蓋率收集
    const coverageFile = 'coverage/coverage-final.json'
    const content = await fs.readFile(coverageFile, 'utf-8')
    const data = JSON.parse(content)
    
    // 轉換 Istanbul 格式到標準格式
    return this.convertIstanbulFormat(data)
  }

  configure(config: any): void {
    // 配置 Istanbul 整合
  }

  private convertIstanbulFormat(data: any): CoverageMetrics {
    // 實現 Istanbul 格式轉換
    return {
      timestamp: new Date(),
      overall: {
        lines: 0,
        functions: 0,
        branches: 0,
        statements: 0,
        files: {}
      },
      files: [],
      summary: {
        totalLines: 0,
        coveredLines: 0,
        totalFunctions: 0,
        coveredFunctions: 0,
        totalBranches: 0,
        coveredBranches: 0,
        totalStatements: 0,
        coveredStatements: 0
      }
    }
  }
}

// 報告器實現
class HtmlReporter implements CoverageReporter {
  name = 'html'

  async generate(metrics: CoverageMetrics): Promise<string> {
    const html = this.generateHtmlReport(metrics)
    const outputPath = this.getOutputPath()
    await fs.writeFile(outputPath, html, 'utf-8')
    return outputPath
  }

  getOutputPath(): string {
    return join('coverage-reports', 'index.html')
  }

  private generateHtmlReport(metrics: CoverageMetrics): string {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>Coverage Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 3px; }
        .high { color: green; }
        .medium { color: orange; }
        .low { color: red; }
    </style>
</head>
<body>
    <h1>Coverage Report</h1>
    <div class="summary">
        <div class="metric">
            <strong>Lines:</strong> 
            <span class="${this.getCoverageClass(metrics.overall.lines)}">${metrics.overall.lines.toFixed(1)}%</span>
        </div>
        <div class="metric">
            <strong>Functions:</strong> 
            <span class="${this.getCoverageClass(metrics.overall.functions)}">${metrics.overall.functions.toFixed(1)}%</span>
        </div>
        <div class="metric">
            <strong>Branches:</strong> 
            <span class="${this.getCoverageClass(metrics.overall.branches)}">${metrics.overall.branches.toFixed(1)}%</span>
        </div>
        <div class="metric">
            <strong>Statements:</strong> 
            <span class="${this.getCoverageClass(metrics.overall.statements)}">${metrics.overall.statements.toFixed(1)}%</span>
        </div>
    </div>
    <p><em>Generated on ${metrics.timestamp.toLocaleString()}</em></p>
</body>
</html>
    `
  }

  private getCoverageClass(coverage: number): string {
    if (coverage >= 80) return 'high'
    if (coverage >= 60) return 'medium'
    return 'low'
  }
}

class JsonReporter implements CoverageReporter {
  name = 'json'

  async generate(metrics: CoverageMetrics): Promise<string> {
    const outputPath = this.getOutputPath()
    await fs.writeFile(outputPath, JSON.stringify(metrics, null, 2), 'utf-8')
    return outputPath
  }

  getOutputPath(): string {
    return join('coverage-reports', 'coverage.json')
  }
}

class LcovReporter implements CoverageReporter {
  name = 'lcov'

  async generate(metrics: CoverageMetrics): Promise<string> {
    const lcov = this.generateLcovFormat(metrics)
    const outputPath = this.getOutputPath()
    await fs.writeFile(outputPath, lcov, 'utf-8')
    return outputPath
  }

  getOutputPath(): string {
    return join('coverage-reports', 'lcov.info')
  }

  private generateLcovFormat(metrics: CoverageMetrics): string {
    // 實現 LCOV 格式生成
    return `TN:
SF:${process.cwd()}
FNF:${metrics.summary.totalFunctions}
FNH:${metrics.summary.coveredFunctions}
LF:${metrics.summary.totalLines}
LH:${metrics.summary.coveredLines}
BRF:${metrics.summary.totalBranches}
BRH:${metrics.summary.coveredBranches}
end_of_record
`
  }
}

class ConsoleReporter implements CoverageReporter {
  name = 'console'

  async generate(metrics: CoverageMetrics): Promise<string> {
    const report = this.generateConsoleReport(metrics)
    console.log(report)
    return 'console'
  }

  getOutputPath(): string {
    return 'console'
  }

  private generateConsoleReport(metrics: CoverageMetrics): string {
    return `
📊 Coverage Summary
==================
Lines:      ${metrics.overall.lines.toFixed(1)}%
Functions:  ${metrics.overall.functions.toFixed(1)}%
Branches:   ${metrics.overall.branches.toFixed(1)}%
Statements: ${metrics.overall.statements.toFixed(1)}%

Generated: ${metrics.timestamp.toLocaleString()}
`
  }
}

// 通知器實現
class SlackNotifier implements CoverageNotifier {
  constructor(private config: { webhook: string; channel: string }) {}

  async notify(alert: any): Promise<void> {
    // 實現 Slack 通知
    console.log(`Would send Slack notification to ${this.config.channel}:`, alert.message)
  }

  configure(config: any): void {
    this.config = { ...this.config, ...config }
  }
}

class EmailNotifier implements CoverageNotifier {
  constructor(private config: { smtp: any; recipients: string[] }) {}

  async notify(alert: any): Promise<void> {
    // 實現郵件通知
    console.log(`Would send email to ${this.config.recipients.join(', ')}:`, alert.message)
  }

  configure(config: any): void {
    this.config = { ...this.config, ...config }
  }
}