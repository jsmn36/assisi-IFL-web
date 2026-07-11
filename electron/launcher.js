/**
 * Launcher script that strips ELECTRON_RUN_AS_NODE before spawning Electron.
 * This variable is set by Claude Code and other Node.js environments
 * and would otherwise force Electron into Node.js-only mode.
 */
const { spawn } = require('child_process');
const path = require('path');
const electronPath = require('./node_modules/electron');

const env = { ...process.env, NODE_ENV: process.env.NODE_ENV || 'development' };
delete env.ELECTRON_RUN_AS_NODE;

const child = spawn(electronPath, [__dirname], {
  stdio: 'inherit',
  env,
});

child.on('close', (code) => process.exit(code || 0));
