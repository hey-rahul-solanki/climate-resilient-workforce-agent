import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const agentTarget = process.env.AGENT_PROXY_TARGET ?? 'http://127.0.0.1:8010'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': agentTarget, '/agent': agentTarget } },
})
