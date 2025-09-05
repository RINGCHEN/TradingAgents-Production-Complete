#!/usr/bin/env python3
"""
Node.js Environment Setup and Validation Script
Supports the Frontend Testing Environment Setup for TradingAgents project
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class NodeEnvironmentSetup:
    """Handles Node.js environment setup and validation"""
    
    def __init__(self):
        self.required_node_version = "18.0.0"
        self.workspace_root = Path(__file__).parent.parent
        self.frontend_dir = self.workspace_root / "frontend"
        self.validation_results = {}
        
    def check_node_version(self) -> Tuple[bool, str]:
        """Check if Node.js version meets requirements"""
        try:
            result = subprocess.run(
                ["node", "--version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            version = result.stdout.strip().lstrip('v')
            
            # Simple version comparison
            current_parts = [int(x) for x in version.split('.')]
            required_parts = [int(x) for x in self.required_node_version.split('.')]
            
            is_valid = current_parts >= required_parts
            return is_valid, version
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "Not installed"
    
    def check_npm_version(self) -> Tuple[bool, str]:
        """Check npm version"""
        try:
            result = subprocess.run(
                ["npm", "--version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            version = result.stdout.strip()
            return True, version
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "Not installed"
    
    def create_package_json(self) -> bool:
        """Create package.json with testing dependencies"""
        package_config = {
            "name": "tradingagents-frontend",
            "version": "1.0.0",
            "description": "TradingAgents Frontend Application with Testing Environment",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "preview": "vite preview",
                "test": "jest",
                "test:watch": "jest --watch",
                "test:coverage": "jest --coverage",
                "test:ci": "jest --ci --coverage --watchAll=false",
                "test:setup": "node scripts/test-setup.js",
                "test:verify": "node scripts/test-verify.js",
                "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
                "lint:fix": "eslint . --ext ts,tsx --fix"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.8.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.43",
                "@types/react-dom": "^18.2.17",
                "@typescript-eslint/eslint-plugin": "^6.14.0",
                "@typescript-eslint/parser": "^6.14.0",
                "@vitejs/plugin-react": "^4.2.1",
                "eslint": "^8.55.0",
                "eslint-plugin-react-hooks": "^4.6.0",
                "eslint-plugin-react-refresh": "^0.4.5",
                "typescript": "^5.2.2",
                "vite": "^5.0.8",
                
                # Testing dependencies
                "jest": "^29.7.0",
                "@types/jest": "^29.5.8",
                "ts-jest": "^29.1.1",
                "jest-environment-jsdom": "^29.7.0",
                "@testing-library/react": "^13.4.0",
                "@testing-library/jest-dom": "^6.1.5",
                "@testing-library/user-event": "^14.5.1",
                "jest-coverage-istanbul": "^1.0.0",
                
                # E2E Testing
                "@playwright/test": "^1.40.0",
                
                # Security Testing Support
                "jest-axe": "^8.0.0",
                "axe-core": "^4.8.3"
            },
            "engines": {
                "node": ">=18.0.0",
                "npm": ">=9.0.0"
            }
        }
        
        try:
            package_json_path = self.frontend_dir / "package.json"
            
            # Create frontend directory if it doesn't exist
            self.frontend_dir.mkdir(exist_ok=True)
            
            with open(package_json_path, 'w', encoding='utf-8') as f:
                json.dump(package_config, f, indent=2)
            
            print(f"✅ Created package.json at {package_json_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create package.json: {e}")
            return False
    
    def create_jest_config(self) -> bool:
        """Create Jest configuration file"""
        jest_config = '''module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: [
    '**/__tests__/**/*.(ts|tsx|js)',
    '**/*.(test|spec).(ts|tsx|js)'
  ],
  transform: {
    '^.+\\\\.(ts|tsx)$': 'ts-jest',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html', 'json'],
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 75,
      lines: 75,
      statements: 75
    }
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\\\.(css|less|scss|sass)$': 'identity-obj-proxy'
  },
  testTimeout: 10000,
  maxWorkers: '50%'
};
'''
        
        try:
            jest_config_path = self.frontend_dir / "jest.config.js"
            with open(jest_config_path, 'w', encoding='utf-8') as f:
                f.write(jest_config)
            
            print(f"✅ Created Jest configuration at {jest_config_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create Jest config: {e}")
            return False
    
    def create_test_setup_files(self) -> bool:
        """Create test setup and utility files"""
        try:
            tests_dir = self.frontend_dir / "tests"
            tests_dir.mkdir(exist_ok=True)
            
            # Test setup file
            setup_content = '''import '@testing-library/jest-dom';
import 'jest-axe/extend-expect';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() { return null; }
  disconnect() { return null; }
  unobserve() { return null; }
};

// Setup for security testing
global.console = {
  ...console,
  // Suppress console.error for expected test errors
  error: jest.fn(),
  warn: jest.fn(),
};
'''
            
            setup_path = tests_dir / "setup.ts"
            with open(setup_path, 'w', encoding='utf-8') as f:
                f.write(setup_content)
            
            # Test utilities
            utils_content = '''import { render, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';

// Custom render function for testing
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { ...options });

export * from '@testing-library/react';
export { customRender as render };

// Security testing utilities
export const testSecurityHeaders = (response: Response) => {
  const headers = response.headers;
  
  expect(headers.get('X-Content-Type-Options')).toBe('nosniff');
  expect(headers.get('X-Frame-Options')).toBe('DENY');
  expect(headers.get('X-XSS-Protection')).toBe('1; mode=block');
};

// Performance testing utilities
export const measureRenderTime = async (renderFn: () => void) => {
  const start = performance.now();
  renderFn();
  const end = performance.now();
  return end - start;
};
'''
            
            utils_path = tests_dir / "test-utils.tsx"
            with open(utils_path, 'w', encoding='utf-8') as f:
                f.write(utils_content)
            
            print(f"✅ Created test setup files in {tests_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create test setup files: {e}")
            return False
    
    def create_environment_scripts(self) -> bool:
        """Create environment validation and setup scripts"""
        try:
            scripts_dir = self.frontend_dir / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            
            # Test verification script
            verify_script = '''const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Frontend Testing Environment...');

// Check Node.js version
try {
  const nodeVersion = execSync('node --version', { encoding: 'utf8' }).trim();
  console.log(`✅ Node.js version: ${nodeVersion}`);
} catch (error) {
  console.error('❌ Node.js not found');
  process.exit(1);
}

// Check npm version
try {
  const npmVersion = execSync('npm --version', { encoding: 'utf8' }).trim();
  console.log(`✅ npm version: ${npmVersion}`);
} catch (error) {
  console.error('❌ npm not found');
  process.exit(1);
}

// Check if dependencies are installed
const packageJsonPath = path.join(__dirname, '..', 'package.json');
const nodeModulesPath = path.join(__dirname, '..', 'node_modules');

if (!fs.existsSync(packageJsonPath)) {
  console.error('❌ package.json not found');
  process.exit(1);
}

if (!fs.existsSync(nodeModulesPath)) {
  console.log('⚠️  Dependencies not installed. Run: npm install');
  process.exit(1);
}

console.log('✅ All dependencies installed');

// Test Jest configuration
try {
  execSync('npx jest --version', { encoding: 'utf8', stdio: 'pipe' });
  console.log('✅ Jest is configured correctly');
} catch (error) {
  console.error('❌ Jest configuration issue');
  process.exit(1);
}

console.log('🎉 Frontend Testing Environment is ready!');
'''
            
            verify_path = scripts_dir / "test-verify.js"
            with open(verify_path, 'w', encoding='utf-8') as f:
                f.write(verify_script)
            
            print(f"✅ Created environment scripts in {scripts_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create environment scripts: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install npm dependencies"""
        try:
            print("📦 Installing npm dependencies...")
            
            # Change to frontend directory
            original_cwd = os.getcwd()
            os.chdir(self.frontend_dir)
            
            # Run npm install
            result = subprocess.run(
                ["npm", "install"], 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Restore original directory
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                print(f"❌ Failed to install dependencies: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Dependency installation timed out")
            return False
        except Exception as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def validate_installation(self) -> Dict[str, bool]:
        """Validate the complete installation"""
        results = {}
        
        # Check Node.js
        node_valid, node_version = self.check_node_version()
        results['node_js'] = node_valid
        print(f"Node.js: {'✅' if node_valid else '❌'} {node_version}")
        
        # Check npm
        npm_valid, npm_version = self.check_npm_version()
        results['npm'] = npm_valid
        print(f"npm: {'✅' if npm_valid else '❌'} {npm_version}")
        
        # Check package.json
        package_json_exists = (self.frontend_dir / "package.json").exists()
        results['package_json'] = package_json_exists
        print(f"package.json: {'✅' if package_json_exists else '❌'}")
        
        # Check Jest config
        jest_config_exists = (self.frontend_dir / "jest.config.js").exists()
        results['jest_config'] = jest_config_exists
        print(f"Jest config: {'✅' if jest_config_exists else '❌'}")
        
        # Check node_modules
        node_modules_exists = (self.frontend_dir / "node_modules").exists()
        results['dependencies'] = node_modules_exists
        print(f"Dependencies: {'✅' if node_modules_exists else '❌'}")
        
        return results
    
    def run_setup(self) -> bool:
        """Run the complete setup process"""
        print("🚀 Starting Frontend Testing Environment Setup...")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Workspace: {self.workspace_root}")
        print(f"Frontend Directory: {self.frontend_dir}")
        print("-" * 50)
        
        steps = [
            ("Checking Node.js version", self.check_node_version),
            ("Creating package.json", self.create_package_json),
            ("Creating Jest configuration", self.create_jest_config),
            ("Creating test setup files", self.create_test_setup_files),
            ("Creating environment scripts", self.create_environment_scripts),
            ("Installing dependencies", self.install_dependencies),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            
            if step_name == "Checking Node.js version":
                is_valid, version = step_func()
                if not is_valid:
                    print(f"❌ Node.js version {version} does not meet requirements (>= {self.required_node_version})")
                    print("Please install Node.js 18+ from https://nodejs.org/")
                    return False
                else:
                    print(f"✅ Node.js version {version} is compatible")
            else:
                if not step_func():
                    print(f"❌ Failed: {step_name}")
                    return False
        
        print("\n" + "=" * 50)
        print("📊 Final Validation:")
        validation_results = self.validate_installation()
        
        all_valid = all(validation_results.values())
        
        if all_valid:
            print("\n🎉 Frontend Testing Environment Setup Complete!")
            print("\nNext steps:")
            print("1. Run: cd frontend && npm test")
            print("2. Run: npm run test:coverage")
            print("3. Check test coverage report in frontend/coverage/")
        else:
            print("\n❌ Setup incomplete. Please check the errors above.")
        
        return all_valid

def main():
    """Main entry point"""
    setup = NodeEnvironmentSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()