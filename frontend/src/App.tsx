import { Routes, Route, Navigate } from 'react-router-dom';
import { Shell } from './components/shell/Shell';
import { useSession } from './contexts/SessionContext';

// Pages
import { Settings } from './pages/Settings';
import { Overview } from './pages/Overview';
import { Schedule } from './pages/Schedule';
import { Ask } from './pages/Ask';
import { Meetings } from './pages/Meetings';
import { People } from './pages/People';
import { Network } from './pages/Network';
import { Health } from './pages/Health';
import { Trends } from './pages/Trends';
import { Reports } from './pages/Reports';

function App() {
  const { sessionId } = useSession();

  return (
    <Shell>
      <Routes>
        {/* Redirect to settings if no session */}
        <Route
          path="/"
          element={sessionId ? <Overview /> : <Navigate to="/settings" replace />}
        />
        <Route path="/settings" element={<Settings />} />
        <Route path="/schedule" element={<Schedule />} />
        <Route path="/ask" element={<Ask />} />
        <Route path="/meetings" element={<Meetings />} />
        <Route path="/people" element={<People />} />
        <Route path="/network" element={<Network />} />
        <Route path="/health" element={<Health />} />
        <Route path="/trends" element={<Trends />} />
        <Route path="/reports" element={<Reports />} />
      </Routes>
    </Shell>
  );
}

export default App;

// Made with Bob
