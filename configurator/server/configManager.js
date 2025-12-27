const fs = require('fs');
const path = require('path');

// candidate locations (prefer home first)
const homePath = path.join(require('os').homedir(), 'HangarBuddy.config');
const candidatePaths = [
    homePath,
    path.resolve(__dirname, '../../HangarBuddy.config'),
    path.resolve(__dirname, '../HangarBuddy.config'),
    path.resolve(__dirname, './HangarBuddy.config')
];

function findConfigPath() {
    for (const p of candidatePaths) {
        if (fs.existsSync(p)) return p;
    }
    // fallback to home path
    return homePath;
}

async function readConfig() {
    const p = findConfigPath();
    const txt = await fs.promises.readFile(p, 'utf8');
    return { path: p, content: txt };
}

async function writeConfigAtomic(content /*, targetPath - ignored */) {
    // Always write to the user's home HangarBuddy.config
    const home = require('os').homedir();
    const CONFIG_PATH = path.join(home, 'HangarBuddy.config');
    const dir = path.dirname(CONFIG_PATH);
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const backup = path.join(dir, `HangarBuddy.config.${ts}.bak`);
    const tmp = CONFIG_PATH + '.tmp';
    // create backup if exists
    try {
        await fs.promises.copyFile(CONFIG_PATH, backup);
    } catch (e) {
        // ignore if missing
    }
    await fs.promises.writeFile(tmp, content, 'utf8');
    await fs.promises.rename(tmp, CONFIG_PATH);
}

module.exports = { readConfig, writeConfigAtomic };
