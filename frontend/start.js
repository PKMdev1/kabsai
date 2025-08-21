#!/usr/bin/env node
/**
 * KABS Assistant Frontend Startup Script
 * This script installs dependencies and starts the Next.js development server.
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function checkNodeVersion() {
    const version = process.version;
    const major = parseInt(version.slice(1).split('.')[0]);
    
    if (major < 16) {
        console.log('❌ Error: Node.js 16 or higher is required');
        console.log(`Current version: ${version}`);
        process.exit(1);
    }
    console.log(`✅ Node.js version: ${version}`);
}

function checkPackageManager() {
    try {
        // Check if npm is available
        execSync('npm --version', { stdio: 'ignore' });
        return 'npm';
    } catch (error) {
        try {
            // Check if yarn is available
            execSync('yarn --version', { stdio: 'ignore' });
            return 'yarn';
        } catch (error) {
            console.log('❌ Error: Neither npm nor yarn is available');
            console.log('Please install Node.js and npm/yarn');
            process.exit(1);
        }
    }
}

function installDependencies(packageManager) {
    const nodeModulesPath = path.join(__dirname, 'node_modules');
    
    if (fs.existsSync(nodeModulesPath)) {
        console.log('✅ Dependencies already installed');
        return;
    }
    
    console.log('📦 Installing dependencies...');
    
    const installCmd = packageManager === 'yarn' ? 'yarn install' : 'npm install';
    
    try {
        execSync(installCmd, { 
            stdio: 'inherit',
            cwd: __dirname 
        });
        console.log('✅ Dependencies installed successfully');
    } catch (error) {
        console.log('❌ Failed to install dependencies');
        process.exit(1);
    }
}

function checkEnvFile() {
    const envFile = path.join(__dirname, '.env.local');
    const envExampleFile = path.join(__dirname, '.env.local.example');
    
    if (!fs.existsSync(envFile)) {
        if (fs.existsSync(envExampleFile)) {
            console.log('⚠️  Warning: .env.local file not found');
            console.log('Please create .env.local file from .env.local.example');
            console.log('cp .env.local.example .env.local');
            console.log('Then edit .env.local with your configuration');
        } else {
            console.log('⚠️  Warning: No environment configuration found');
        }
        return false;
    }
    
    console.log('✅ Environment configuration found');
    return true;
}

function startDevServer(packageManager) {
    console.log('\n🚀 Starting KABS Assistant Frontend Development Server...');
    console.log('=' * 60);
    
    const devCmd = packageManager === 'yarn' ? 'yarn dev' : 'npm run dev';
    
    console.log('📍 Server will be available at: http://localhost:3000');
    console.log('🔧 Auto-reload: enabled');
    console.log('=' * 60);
    
    const child = spawn(devCmd, [], {
        stdio: 'inherit',
        shell: true,
        cwd: __dirname
    });
    
    child.on('error', (error) => {
        console.log(`❌ Failed to start development server: ${error.message}`);
        process.exit(1);
    });
    
    child.on('close', (code) => {
        if (code !== 0) {
            console.log(`❌ Development server exited with code ${code}`);
            process.exit(code);
        }
    });
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n🛑 Stopping development server...');
        child.kill('SIGINT');
    });
    
    process.on('SIGTERM', () => {
        console.log('\n🛑 Stopping development server...');
        child.kill('SIGTERM');
    });
}

function main() {
    console.log('KABS Assistant Frontend Startup');
    console.log('=' * 40);
    
    // Check Node.js version
    checkNodeVersion();
    
    // Check package manager
    const packageManager = checkPackageManager();
    console.log(`✅ Using package manager: ${packageManager}`);
    
    // Check environment
    checkEnvFile();
    
    // Install dependencies
    installDependencies(packageManager);
    
    // Start development server
    startDevServer(packageManager);
}

if (require.main === module) {
    main();
}
