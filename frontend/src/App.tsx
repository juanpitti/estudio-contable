import { BrowserRouter, Routes, Route } from 'react-router'
import { ThemeProvider } from './components/ui/theme-provider'
import Home from './pages/Home'

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/*" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}
