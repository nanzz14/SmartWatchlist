import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@/lib/styles.css'
import './index.css'
import App from './App.tsx'
import { AppProviders } from '@/lib/components/smart/providers'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </StrictMode>,
)
