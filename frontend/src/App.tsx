import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Evaluator from './pages/Evaluator'
import CohortList from './pages/CohortList'
import CohortDetail from './pages/CohortDetail'
import Watchlist from './pages/Watchlist'
import Newsletter from './pages/Newsletter'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/evaluator" element={<Evaluator />} />
        <Route path="/cohorts" element={<CohortList />} />
        <Route path="/cohorts/:id" element={<CohortDetail />} />
        <Route path="/watchlist" element={<Watchlist />} />
        <Route path="/newsletter" element={<Newsletter />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}
