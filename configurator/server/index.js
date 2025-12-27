const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const { readConfig, writeConfigAtomic } = require('./configManager');

const app = express();
const root = path.resolve(__dirname, '..');

app.use(express.static(root));
app.use(bodyParser.json({ limit: '1mb' }));

// Allow cross-origin requests from the Vite dev server (and others) during development
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

app.get('/api/config', async (req, res) => {
  try {
    const obj = await readConfig();
    // return JSON with content and path so client can save back to same file
    res.json({ content: obj.content, path: obj.path });
  } catch (e) {
    console.error('read config failed', e);
    res.status(500).send('Unable to read config');
  }
});

app.post('/api/config', async (req, res) => {
  const { content, path: targetPath } = req.body || {};
  if (typeof content !== 'string') return res.status(400).send('Missing content');
  try {
    await writeConfigAtomic(content, targetPath);
    res.sendStatus(200);
  } catch (e) {
    console.error('save failed', e);
    res.status(500).send('Save failed');
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log('Configurator server listening on', port));
