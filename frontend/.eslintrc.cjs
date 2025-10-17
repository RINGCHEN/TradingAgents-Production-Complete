module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
    jest: true
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended'
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaFeatures: {
      jsx: true
    },
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  plugins: [
    'react',
    '@typescript-eslint',
    'react-hooks'
  ],
  rules: {
    // React 相關規則
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off',
    'react/jsx-uses-react': 'off',
    'react/jsx-uses-vars': 'warn', // Downgraded
    'react/no-unknown-property': 'warn', // Downgraded
    'react/display-name': 'warn', // Downgraded
    'react/no-unescaped-entities': 'warn', // Downgraded
    
    // TypeScript 相關規則
    '@typescript-eslint/no-unused-vars': 'warn',
    '@typescript-eslint/no-explicit-any': 'warn',
    
    // 一般規則
    'no-console': 'warn',
    'no-debugger': 'warn',
    'no-duplicate-imports': 'warn', // Downgraded
    'no-unused-vars': 'off', // Use TypeScript version
    'no-undef': 'off', // TypeScript handles this
    'no-unreachable': 'warn', // Downgraded
    'no-case-declarations': 'warn', // Downgraded
    'no-redeclare': 'warn', // Downgraded
    'no-cond-assign': 'warn', // Downgraded
    'no-control-regex': 'warn', // Downgraded
    'no-empty-pattern': 'warn' // Downgraded
  },
  settings: {
    react: {
      version: 'detect'
    }
  },
  ignorePatterns: [
    'build/',
    'dist/',
    'node_modules/',
    '*.config.js',
    '*.config.ts',
    'public/'
  ]
};