import { StrictMode, Suspense, lazy } from 'react'
import { createRoot } from 'react-dom/client'

// Rebuild switch: new Liquid Glass UI by default; the legacy monolith stays
// reachable via ?legacy=1 until cutover. lazy() keeps the two module graphs
// (and their colliding stylesheets) mutually exclusive at runtime.
const legacy = new URLSearchParams(window.location.search).has('legacy')
const App = lazy(() => (legacy ? import('./App.jsx') : import('./AppNext.jsx')))

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Suspense fallback={null}>
      <App />
    </Suspense>
  </StrictMode>
)
