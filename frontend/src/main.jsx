import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './App.css'

const rootElement = document.getElementById('react-root')

if (rootElement) {
  const dataElement = document.getElementById('react-data')
  const data = dataElement ? JSON.parse(dataElement.textContent) : {}

  createRoot(rootElement).render(
    <StrictMode>
      <App data={data} />
    </StrictMode>,
  )
}
