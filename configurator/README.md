# HangarBuddy Configurator

Local UI to edit HangarBuddy.config on device.

Run locally (install deps first):

```bash
cd configurator
npm install
npm run dev        # starts vite dev server
# or build
npm run build
npm run preview    # preview built site
# start server to expose API
npm start
```

Server starts on port 3000 by default and exposes:
- `GET /api/config` — returns current HangarBuddy.config
- `POST /api/config` — save config (body: { content: string }) — server writes atomically and creates a timestamped backup
