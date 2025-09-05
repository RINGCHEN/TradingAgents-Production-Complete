/**
 * Coverage Types - 覆蓋率相關類型定義
 */

export interface CoverageThreshold {
  lines: number
  functions: number
  branches: number
  statements: number
}

export interface CoverageData {
  lines: number
  functions: number
  branches: number
  statements: number
  files?: Record<string, {
    lines: number
    functions: number
    branches: number
    statements: number
  }>
}

export interface CoverageReport {
  timestamp: Date
  coverage: CoverageData
  thresholds: CoverageThreshold
  passed: boolean
  failures: string[]
  warnings: string[]
  trends: {
    trend: 'improving' | 'declining' | 'stable'
    changePercent: number
    recommendations: string[]
  }
  uncoveredFiles: string[]
  recommendations: string[]
}

export interface CoverageAlert {
  type: 'warning' | 'critical'
  message: string
  timestamp: Date
  coverage: number
}

export interface CoverageTrend {
  date: Date
  coverage: CoverageData
  change: number
}

export interface CoverageAnalysis {
  summary: {
    totalFiles: number
    coveredFiles: number
    uncoveredFiles: number
    averageCoverage: number
  }
  trends: CoverageTrend[]
  hotspots: {
    file: string
    coverage: number
    priority: 'high' | 'medium' | 'low'
  }[]
  recommendations: {
    type: 'add_tests' | 'remove_dead_code' | 'improve_existing'
    description: string
    files: string[]
    impact: 'high' | 'medium' | 'low'
  }[]
}

export interface CoverageConfig {
  enabled: boolean
  threshold: CoverageThreshold
  include: string[]
  exclude: string[]
  reporters: ('html' | 'json' | 'lcov' | 'text')[]
  outputDir: string
  historyEnabled: boolean
  alertsEnabled: boolean
  alertThresholds: {
    warning: number
    critical: number
  }
}

export interface FileCoverage {
  path: string
  lines: {
    total: number
    covered: number
    percentage: number
    uncovered: number[]
  }
  functions: {
    total: number
    covered: number
    percentage: number
    uncovered: string[]
  }
  branches: {
    total: number
    covered: number
    percentage: number
    uncovered: number[]
  }
  statements: {
    total: number
    covered: number
    percentage: number
    uncovered: number[]
  }
}

export interface CoverageMetrics {
  timestamp: Date
  overall: CoverageData
  files: FileCoverage[]
  summary: {
    totalLines: number
    coveredLines: number
    totalFunctions: number
    coveredFunctions: number
    totalBranches: number
    coveredBranches: number
    totalStatements: number
    coveredStatements: number
  }
  deltas?: {
    lines: number
    functions: number
    branches: number
    statements: number
  }
}

export interface CoverageReporter {
  name: string
  generate(metrics: CoverageMetrics): Promise<string>
  getOutputPath(): string
}

export interface CoverageCollector {
  collect(): Promise<CoverageMetrics>
  reset(): Promise<void>
  isEnabled(): boolean
}

export interface CoverageProcessor {
  process(rawCoverage: any): Promise<CoverageMetrics>
  merge(coverage1: CoverageMetrics, coverage2: CoverageMetrics): CoverageMetrics
  filter(coverage: CoverageMetrics, patterns: string[]): CoverageMetrics
}

export interface CoverageValidator {
  validate(coverage: CoverageMetrics, thresholds: CoverageThreshold): {
    passed: boolean
    failures: string[]
    warnings: string[]
  }
}

export interface CoverageNotifier {
  notify(alert: CoverageAlert): Promise<void>
  configure(config: any): void
}

export interface CoverageStorage {
  save(metrics: CoverageMetrics): Promise<void>
  load(date?: Date): Promise<CoverageMetrics | null>
  getHistory(days: number): Promise<CoverageMetrics[]>
  cleanup(retentionDays: number): Promise<void>
}

export interface CoverageVisualization {
  generateChart(data: CoverageTrend[]): Promise<string>
  generateHeatmap(files: FileCoverage[]): Promise<string>
  generateSummaryWidget(metrics: CoverageMetrics): Promise<string>
}

export interface CoverageIntegration {
  name: string
  isAvailable(): Promise<boolean>
  collect(): Promise<CoverageMetrics>
  configure(config: any): void
}

export interface CoveragePlugin {
  name: string
  version: string
  initialize(config: any): Promise<void>
  beforeCollection?(): Promise<void>
  afterCollection?(metrics: CoverageMetrics): Promise<void>
  beforeReport?(metrics: CoverageMetrics): Promise<void>
  afterReport?(reportPath: string): Promise<void>
  cleanup?(): Promise<void>
}

export interface CoverageEvent {
  type: 'collection:start' | 'collection:complete' | 'threshold:failed' | 'alert:generated'
  timestamp: Date
  data: any
}

export type CoverageEventListener = (event: CoverageEvent) => void

export interface CoverageEventEmitter {
  on(event: string, listener: CoverageEventListener): void
  off(event: string, listener: CoverageEventListener): void
  emit(event: string, data: any): void
}

export interface CoverageScheduler {
  schedule(cronExpression: string, task: () => Promise<void>): void
  unschedule(taskId: string): void
  start(): void
  stop(): void
}

export interface CoverageCache {
  get(key: string): Promise<any>
  set(key: string, value: any, ttl?: number): Promise<void>
  delete(key: string): Promise<void>
  clear(): Promise<void>
}

export interface CoverageComparator {
  compare(baseline: CoverageMetrics, current: CoverageMetrics): {
    improved: FileCoverage[]
    degraded: FileCoverage[]
    unchanged: FileCoverage[]
    new: FileCoverage[]
    removed: string[]
    summary: {
      overallChange: number
      significantChanges: number
      regressions: number
      improvements: number
    }
  }
}

export interface CoverageExporter {
  export(metrics: CoverageMetrics, format: 'json' | 'csv' | 'xml'): Promise<string>
  exportHistory(history: CoverageMetrics[], format: 'json' | 'csv'): Promise<string>
}

export interface CoverageImporter {
  import(data: string, format: 'json' | 'lcov' | 'clover'): Promise<CoverageMetrics>
  validate(data: string, format: string): boolean
}

export interface CoverageAggregator {
  aggregate(metrics: CoverageMetrics[]): CoverageMetrics
  aggregateByTimeRange(metrics: CoverageMetrics[], range: 'day' | 'week' | 'month'): CoverageMetrics[]
}

export interface CoveragePredictor {
  predict(history: CoverageMetrics[], days: number): {
    predicted: CoverageData
    confidence: number
    factors: string[]
  }
}

export interface CoverageOptimizer {
  analyze(metrics: CoverageMetrics): {
    redundantTests: string[]
    missingTests: string[]
    optimizationSuggestions: string[]
  }
}

export interface CoverageGoal {
  id: string
  name: string
  target: CoverageThreshold
  deadline: Date
  priority: 'high' | 'medium' | 'low'
  status: 'active' | 'completed' | 'cancelled'
  progress: number
}

export interface CoverageGoalTracker {
  createGoal(goal: Omit<CoverageGoal, 'id' | 'status' | 'progress'>): Promise<CoverageGoal>
  updateGoal(id: string, updates: Partial<CoverageGoal>): Promise<CoverageGoal>
  deleteGoal(id: string): Promise<void>
  getGoals(): Promise<CoverageGoal[]>
  checkProgress(metrics: CoverageMetrics): Promise<void>
}

export interface CoverageTeamMetrics {
  team: string
  members: string[]
  coverage: CoverageMetrics
  contributions: {
    member: string
    linesAdded: number
    testsCovered: number
    coverageContribution: number
  }[]
  goals: CoverageGoal[]
}

export interface CoverageGameification {
  calculateScore(metrics: CoverageMetrics): number
  getBadges(history: CoverageMetrics[]): string[]
  getLeaderboard(teams: CoverageTeamMetrics[]): {
    rank: number
    team: string
    score: number
    badges: string[]
  }[]
}

export interface CoverageCI {
  shouldFailBuild(metrics: CoverageMetrics, thresholds: CoverageThreshold): boolean
  generateComment(metrics: CoverageMetrics, baseline?: CoverageMetrics): string
  createStatus(metrics: CoverageMetrics): {
    state: 'success' | 'failure' | 'pending'
    description: string
    targetUrl?: string
  }
}

export interface CoverageWebhook {
  url: string
  events: string[]
  headers?: Record<string, string>
  payload?: any
}

export interface CoverageWebhookManager {
  register(webhook: CoverageWebhook): Promise<string>
  unregister(id: string): Promise<void>
  trigger(event: string, data: any): Promise<void>
  getWebhooks(): Promise<CoverageWebhook[]>
}