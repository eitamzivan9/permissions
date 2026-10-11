import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Self-hosted (not Google Fonts) so it keeps working on the closed network.
import '@fontsource/assistant/400.css'
import '@fontsource/assistant/500.css'
import '@fontsource/assistant/600.css'
import '@fontsource/assistant/700.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
