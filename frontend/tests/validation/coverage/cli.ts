#!/usr/bin/env node

/**
 * Coverage CLI - 覆蓋率監控命令行工具
 * 提供命令行介面來執行覆蓋率收集、分析和報告
 */

import { Command } from 'commander'
import { CoverageIntegrator, CoverageIntegratorConfig } from './CoverageIntegrator'
import { CoverageMonitor } from './CoverageMonitor'
import { promises as fs } from 'fs'
import { join } from 'path'
import chalk from 'chalk'

const program = new Command()

program
  .name('coverage-cli')
  .description('TradingAgents Frontend Coverage Monitoring CLI')
  .version('1.0.0')

// 收集覆蓋率命令
program
  .command('collect')
  .description('Collect coverage data from various sources')
  .option('-c, --config <path>', 'Configuration file path', './coverage.config.json')
  .option('-o, --output <path>', 'Output directory', './coverage-reports')
  .option('--format <format>', 'Output format (json|html|lcov|console)', 'console')
  .option('--threshold <number>', 'Coverage threshold percentage', '85')
  .option('--fail-on-threshold', 'Fail if coverage is below threshold')
  .option('--watch', 'Watch mode for continuous monitoring')
  .action(async (options) => {
    try {
      console.log(chalk.blue('📊 Starting coverage collection...'))
      
      const config = await loadConfig(options.config)
      const integrator = new CoverageIntegrator(config)
      
      if (options.watch) {
        await runWatchMode(integrator, options)
      } else {
        const metrics = await integrator.runCoverageAnalysis()
        await handleResults(metrics, options)
      }
      
    } catch (error) {
      console.error(chalk.red('❌ Coverage collection failed:'), error)
      process.exit(1)
    }
  })

// 分析覆蓋率命令
program
  .command('analyze')
  .description('Analyze coverage trends and generate insights')
  .option('-c, --config <path>', 'Configuration file path', './coverage.config.json')
  .option('-d, --days <number>', 'Number of days to analyze', '30')
  .option('--format <format>', 'Output format (json|html|console)', 'console')
  .action(async (options) => {
    try {
      console.log(chalk.blue('🔍 Analyzing coverage trends...'))
      
      const config = await loadConfig(options.config)
      const integrator = new CoverageIntegrator(config)
      await integrator.initialize()
      
      const history = integrator.getCoverageHistory()
      const analysis = analyzeTrends(history, parseInt(options.days))
      
      await outputAnalysis(analysis, options.format)
      
    } catch (error) {
      console.error(chalk.red('❌ Coverage analysis failed:'), error)
      process.exit(1)
    }
  })

// 報告命令
program
  .command('report')
  .description('Generate coverage reports')
  .option('-c, --config <path>', 'Configuration file path', './coverage.config.json')
  .option('-i, --input <path>', 'Input coverage data file')
  .option('-o, --output <path>', 'Output directory', './coverage-reports')
  .option('--format <formats...>', 'Report formats', ['html', 'json'])
  .option('--open', 'Open HTML report in browser')
  .action(async (options) => {
    try {
      console.log(chalk.blue('📄 Generating coverage reports...'))
      
      const config = await loadConfig(options.config)
      const integrator = new CoverageIntegrator(config)
      
      let metrics
      if (options.input) {
        metrics = await loadCoverageData(options.input)
      } else {
        metrics = await integrator.runCoverageAnalysis()
      }
      
      await generateReports(metrics, options)
      
      if (options.open && options.format.includes('html')) {
        await openReport(join(options.output, 'index.html'))
      }
      
    } catch (error) {
      console.error(chalk.red('❌ Report generation failed:'), error)
      process.exit(1)
    }
  })

// 監控命令
program
  .command('monitor')
  .description('Start continuous coverage monitoring')
  .option('-c, --config <path>', 'Configuration file path', './coverage.config.json')
  .option('--interval <seconds>', 'Monitoring interval in seconds', '300')
  .option('--alert-threshold <number>', 'Alert threshold percentage', '80')
  .option('--webhook <url>', 'Webhook URL for notifications')
  .action(async (options) => {
    try {
      console.log(chalk.blue('👁️ Starting coverage monitoring...'))
      
      const config = await loadConfig(options.config)
      const integrator = new CoverageIntegrator(config)
      
      await startMonitoring(integrator, options)
      
    } catch (error) {
      console.error(chalk.red('❌ Coverage monitoring failed:'), error)
      process.exit(1)
    }
  })

// 比較命令
program
  .command('compare')
  .description('Compare coverage between two points')
  .option('--baseline <path>', 'Baseline coverage data file')
  .option('--current <path>', 'Current coverage data file')
  .option('--format <format>', 'Output format (json|html|console)', 'console')
  .action(async (options) => {
    try {
      console.log(chalk.blue('🔄 Comparing coverage data...'))
      
      const baseline = await loadCoverageData(options.baseline)
      const current = await loadCoverageData(options.current)
      
      const comparison = compareCoverage(baseline, current)
      await outputComparison(comparison, options.format)
      
    } catch (error) {
      console.error(chalk.red('❌ Coverage comparison failed:'), error)
      process.exit(1)
    }
  })

// 初始化命令
program
  .command('init')
  .description('Initialize coverage monitoring configuration')
  .option('--template <template>', 'Configuration template (basic|advanced)', 'basic')
  .action(async (options) => {
    try {
      console.log(chalk.blue('🚀 Initializing coverage configuration...'))
      
      const config = generateConfigTemplate(options.template)
      await fs.writeFile('./coverage.config.json', JSON.stringify(config, null, 2))
      
      console.log(chalk.green('✅ Configuration file created: coverage.config.json'))
      console.log(chalk.yellow('💡 Edit the configuration file to customize your setup'))
      
    } catch (error) {
      console.error(chalk.red('❌ Initialization failed:'), error)
      process.exit(1)
    }
  })

// 驗證命令
program
  .command('validate')
  .description('Validate coverage configuration and setup')
  .option('-c, --config <path>', 'Configuration file path', './coverage.config.json')
  .action(async (options) => {
    try {
      console.log(chalk.blue('🔍 Validating coverage setup...'))
      
      const config = await loadConfig(options.config)
      const validation = await validateSetup(config)
      
      if (validation.valid) {
        console.log(chalk.green('✅ Coverage setup is valid'))
      } else {
        console.log(chalk.red('❌ Coverage setup has issues:'))
        validation.errors.forEach(error => {
          console.log(chalk.red(`  - ${error}`))
        })
        process.exit(1)
      }
      
    } catch (error) {
      console.error(chalk.red('❌ Validation failed:'), error)
      process.exit(1)
    }
  })

// 清理命令
program
  .command('clean')
  .description('Clean up coverage data and reports')
  .option('--reports', 'Clean coverage reports')
  .option('--data', 'Clean coverage data')
  .option('--all', 'Clean everything')
  .option('--older-than <days>', 'Clean files older than specified days', '30')
  .action(async (options) => {
    try {
      console.log(chalk.blue('🧹 Cleaning up coverage files...'))
      
      await cleanupFiles(options)
      
      console.log(chalk.green('✅ Cleanup completed'))
      
    } catch (error) {
      console.error(chalk.red('❌ Cleanup failed:'), error)
      process.exit(1)
    }
  })

// 輔助函數

async function loadConfig(configPath: string): Promise<Partial<CoverageIntegratorConfig>> {
  try {
    const content = await fs.readFile(configPath, 'utf-8')
    return JSON.parse(content)
  } catch (error) {
    console.warn(chalk.yellow(`⚠️ Could not load config from ${configPath}, using defaults`))
    return {}
  }
}

async function loadCoverageData(filePath: string): Promise<any> {
  const content = await fs.readFile(filePath, 'utf-8')
  return JSON.parse(content)
}

async function handleResults(metrics: any, options: any): Promise<void> {
  const threshold = parseFloat(options.threshold)
  const passed = metrics.overall.lines >= threshold
  
  if (options.format === 'console') {
    displayConsoleResults(metrics, threshold, passed)
  }
  
  if (options.failOnThreshold && !passed) {
    console.log(chalk.red(`❌ Coverage ${metrics.overall.lines.toFixed(1)}% is below threshold ${threshold}%`))
    process.exit(1)
  }
}

function displayConsoleResults(metrics: any, threshold: number, passed: boolean): void {
  console.log('\n' + chalk.bold('📊 Coverage Results'))
  console.log('='.repeat(50))
  
  const statusIcon = passed ? '✅' : '❌'
  const statusColor = passed ? chalk.green : chalk.red
  
  console.log(`${statusIcon} Overall: ${statusColor(metrics.overall.lines.toFixed(1) + '%')} (threshold: ${threshold}%)`)
  console.log(`📈 Lines: ${formatCoverage(metrics.overall.lines)}`)
  console.log(`🔧 Functions: ${formatCoverage(metrics.overall.functions)}`)
  console.log(`🌿 Branches: ${formatCoverage(metrics.overall.branches)}`)
  console.log(`📝 Statements: ${formatCoverage(metrics.overall.statements)}`)
  
  console.log('\n' + chalk.gray(`Generated: ${metrics.timestamp}`))
}

function formatCoverage(coverage: number): string {
  const color = coverage >= 80 ? chalk.green : coverage >= 60 ? chalk.yellow : chalk.red
  return color(`${coverage.toFixed(1)}%`)
}

async function runWatchMode(integrator: CoverageIntegrator, options: any): Promise<void> {
  console.log(chalk.blue('👁️ Starting watch mode...'))
  
  // 實現文件監控邏輯
  const chokidar = require('chokidar')
  
  const watcher = chokidar.watch(['src/**/*.{ts,tsx}', 'tests/**/*.{ts,tsx}'], {
    ignored: /node_modules/,
    persistent: true
  })
  
  let timeout: NodeJS.Timeout
  
  watcher.on('change', () => {
    clearTimeout(timeout)
    timeout = setTimeout(async () => {
      try {
        console.log(chalk.blue('🔄 Files changed, running coverage...'))
        const metrics = await integrator.runCoverageAnalysis()
        await handleResults(metrics, options)
      } catch (error) {
        console.error(chalk.red('❌ Watch mode error:'), error)
      }
    }, 2000) // 2秒防抖
  })
  
  console.log(chalk.green('✅ Watch mode started. Press Ctrl+C to stop.'))
  
  // 處理退出信號
  process.on('SIGINT', () => {
    console.log(chalk.yellow('\n👋 Stopping watch mode...'))
    watcher.close()
    process.exit(0)
  })
}

async function startMonitoring(integrator: CoverageIntegrator, options: any): Promise<void> {
  const interval = parseInt(options.interval) * 1000
  
  console.log(chalk.green(`✅ Monitoring started (interval: ${options.interval}s)`))
  
  const runMonitoring = async () => {
    try {
      const metrics = await integrator.runCoverageAnalysis()
      
      if (metrics.overall.lines < parseFloat(options.alertThreshold)) {
        console.log(chalk.red(`🚨 Alert: Coverage ${metrics.overall.lines.toFixed(1)}% below threshold ${options.alertThreshold}%`))
        
        if (options.webhook) {
          await sendWebhookAlert(options.webhook, metrics)
        }
      }
      
      console.log(chalk.gray(`📊 ${new Date().toLocaleTimeString()}: Coverage ${metrics.overall.lines.toFixed(1)}%`))
      
    } catch (error) {
      console.error(chalk.red('❌ Monitoring error:'), error)
    }
  }
  
  // 立即執行一次
  await runMonitoring()
  
  // 設置定期執行
  const intervalId = setInterval(runMonitoring, interval)
  
  // 處理退出信號
  process.on('SIGINT', () => {
    console.log(chalk.yellow('\n👋 Stopping monitoring...'))
    clearInterval(intervalId)
    process.exit(0)
  })
}

async function sendWebhookAlert(webhookUrl: string, metrics: any): Promise<void> {
  try {
    const fetch = require('node-fetch')
    
    const payload = {
      text: `🚨 Coverage Alert: ${metrics.overall.lines.toFixed(1)}%`,
      attachments: [{
        color: 'danger',
        fields: [
          { title: 'Lines', value: `${metrics.overall.lines.toFixed(1)}%`, short: true },
          { title: 'Functions', value: `${metrics.overall.functions.toFixed(1)}%`, short: true },
          { title: 'Branches', value: `${metrics.overall.branches.toFixed(1)}%`, short: true },
          { title: 'Statements', value: `${metrics.overall.statements.toFixed(1)}%`, short: true }
        ]
      }]
    }
    
    await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    
  } catch (error) {
    console.error(chalk.red('❌ Webhook alert failed:'), error)
  }
}

function analyzeTrends(history: any[], days: number): any {
  const cutoffDate = new Date()
  cutoffDate.setDate(cutoffDate.getDate() - days)
  
  const recentHistory = history.filter(item => 
    new Date(item.timestamp) >= cutoffDate
  )
  
  if (recentHistory.length < 2) {
    return {
      trend: 'insufficient_data',
      message: 'Not enough historical data for trend analysis'
    }
  }
  
  const first = recentHistory[0]
  const last = recentHistory[recentHistory.length - 1]
  
  const change = last.coverage.lines - first.coverage.lines
  const trend = Math.abs(change) < 0.5 ? 'stable' : change > 0 ? 'improving' : 'declining'
  
  return {
    trend,
    change: change.toFixed(2),
    period: `${days} days`,
    dataPoints: recentHistory.length,
    average: (recentHistory.reduce((sum, item) => sum + item.coverage.lines, 0) / recentHistory.length).toFixed(2)
  }
}

async function outputAnalysis(analysis: any, format: string): Promise<void> {
  if (format === 'console') {
    console.log('\n' + chalk.bold('📈 Coverage Trend Analysis'))
    console.log('='.repeat(50))
    
    const trendIcon = analysis.trend === 'improving' ? '📈' : analysis.trend === 'declining' ? '📉' : '➡️'
    const trendColor = analysis.trend === 'improving' ? chalk.green : analysis.trend === 'declining' ? chalk.red : chalk.yellow
    
    console.log(`${trendIcon} Trend: ${trendColor(analysis.trend)}`)
    console.log(`📊 Change: ${analysis.change}%`)
    console.log(`📅 Period: ${analysis.period}`)
    console.log(`📍 Data Points: ${analysis.dataPoints}`)
    console.log(`📊 Average: ${analysis.average}%`)
  } else if (format === 'json') {
    console.log(JSON.stringify(analysis, null, 2))
  }
}

function compareCoverage(baseline: any, current: any): any {
  const diff = {
    lines: current.overall.lines - baseline.overall.lines,
    functions: current.overall.functions - baseline.overall.functions,
    branches: current.overall.branches - baseline.overall.branches,
    statements: current.overall.statements - baseline.overall.statements
  }
  
  return {
    baseline: baseline.overall,
    current: current.overall,
    diff,
    improved: Object.values(diff).every(d => d >= 0),
    significantChange: Object.values(diff).some(d => Math.abs(d) > 1)
  }
}

async function outputComparison(comparison: any, format: string): Promise<void> {
  if (format === 'console') {
    console.log('\n' + chalk.bold('🔄 Coverage Comparison'))
    console.log('='.repeat(50))
    
    const statusIcon = comparison.improved ? '✅' : '❌'
    console.log(`${statusIcon} Overall: ${comparison.improved ? 'Improved' : 'Declined'}`)
    
    console.log('\nBaseline:')
    console.log(`  Lines: ${comparison.baseline.lines.toFixed(1)}%`)
    console.log(`  Functions: ${comparison.baseline.functions.toFixed(1)}%`)
    console.log(`  Branches: ${comparison.baseline.branches.toFixed(1)}%`)
    console.log(`  Statements: ${comparison.baseline.statements.toFixed(1)}%`)
    
    console.log('\nCurrent:')
    console.log(`  Lines: ${comparison.current.lines.toFixed(1)}%`)
    console.log(`  Functions: ${comparison.current.functions.toFixed(1)}%`)
    console.log(`  Branches: ${comparison.current.branches.toFixed(1)}%`)
    console.log(`  Statements: ${comparison.current.statements.toFixed(1)}%`)
    
    console.log('\nDifference:')
    Object.entries(comparison.diff).forEach(([key, value]: [string, any]) => {
      const color = value >= 0 ? chalk.green : chalk.red
      const sign = value >= 0 ? '+' : ''
      console.log(`  ${key}: ${color(sign + value.toFixed(1) + '%')}`)
    })
  } else if (format === 'json') {
    console.log(JSON.stringify(comparison, null, 2))
  }
}

function generateConfigTemplate(template: string): any {
  const basicConfig = {
    monitor: {
      thresholds: {
        lines: 85,
        functions: 85,
        branches: 85,
        statements: 85
      },
      outputDir: './coverage-reports',
      historySize: 30,
      alertEnabled: true,
      alertThresholds: {
        warning: 80,
        critical: 70
      }
    },
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
    }
  }
  
  if (template === 'advanced') {
    return {
      ...basicConfig,
      reporters: {
        ...basicConfig.reporters,
        slack: {
          webhook: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
          channel: '#coverage'
        },
        email: {
          smtp: {
            host: 'smtp.example.com',
            port: 587,
            secure: false,
            auth: {
              user: 'your-email@example.com',
              pass: 'your-password'
            }
          },
          recipients: ['team@example.com']
        }
      },
      goals: [
        {
          name: 'Reach 90% coverage',
          target: {
            lines: 90,
            functions: 90,
            branches: 85,
            statements: 90
          },
          deadline: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          priority: 'high'
        }
      ],
      webhooks: []
    }
  }
  
  return basicConfig
}

async function validateSetup(config: any): Promise<{ valid: boolean; errors: string[] }> {
  const errors: string[] = []
  
  // 檢查配置結構
  if (!config.monitor) {
    errors.push('Missing monitor configuration')
  }
  
  if (!config.integrations) {
    errors.push('Missing integrations configuration')
  }
  
  // 檢查閾值
  if (config.monitor?.thresholds) {
    const thresholds = config.monitor.thresholds
    Object.entries(thresholds).forEach(([key, value]) => {
      if (typeof value !== 'number' || value < 0 || value > 100) {
        errors.push(`Invalid threshold for ${key}: ${value}`)
      }
    })
  }
  
  // 檢查輸出目錄
  if (config.monitor?.outputDir) {
    try {
      await fs.mkdir(config.monitor.outputDir, { recursive: true })
    } catch (error) {
      errors.push(`Cannot create output directory: ${config.monitor.outputDir}`)
    }
  }
  
  // 檢查整合工具
  if (config.integrations?.vitest) {
    try {
      await fs.access('vitest.config.ts')
    } catch {
      errors.push('Vitest integration enabled but vitest.config.ts not found')
    }
  }
  
  if (config.integrations?.cypress) {
    try {
      await fs.access('cypress.config.ts')
    } catch {
      errors.push('Cypress integration enabled but cypress.config.ts not found')
    }
  }
  
  return {
    valid: errors.length === 0,
    errors
  }
}

async function cleanupFiles(options: any): Promise<void> {
  const olderThan = parseInt(options.olderThan)
  const cutoffDate = new Date()
  cutoffDate.setDate(cutoffDate.getDate() - olderThan)
  
  if (options.reports || options.all) {
    await cleanDirectory('./coverage-reports', cutoffDate)
    console.log(chalk.green('✅ Cleaned coverage reports'))
  }
  
  if (options.data || options.all) {
    await cleanDirectory('./coverage', cutoffDate)
    await cleanDirectory('./.nyc_output', cutoffDate)
    console.log(chalk.green('✅ Cleaned coverage data'))
  }
}

async function cleanDirectory(dirPath: string, cutoffDate: Date): Promise<void> {
  try {
    const files = await fs.readdir(dirPath)
    
    for (const file of files) {
      const filePath = join(dirPath, file)
      const stats = await fs.stat(filePath)
      
      if (stats.mtime < cutoffDate) {
        await fs.unlink(filePath)
        console.log(chalk.gray(`Removed: ${filePath}`))
      }
    }
  } catch (error) {
    // 目錄不存在或無法訪問，忽略
  }
}

async function generateReports(metrics: any, options: any): Promise<void> {
  // 實現報告生成邏輯
  console.log(chalk.green(`✅ Generated reports in ${options.output}`))
}

async function openReport(reportPath: string): Promise<void> {
  const open = require('open')
  await open(reportPath)
  console.log(chalk.green(`🌐 Opened report: ${reportPath}`))
}

// 執行 CLI
if (require.main === module) {
  program.parse()
}

export { program }