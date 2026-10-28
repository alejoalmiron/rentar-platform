import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navegacion from './components/Navegacion';
import RutaProtegida from './components/RutaProtegida';
import { AuthProvider } from './context/AuthContext.jsx';
import LoginPagina from './pages/LoginPagina';

import DisponibilidadPagina from './pages/DisponibilidadPagina';
import NuevaReservaPagina from './pages/NuevaReservaPagina';
import ReservasPagina from './pages/ReservasPagina';
import HistorialPagina from './pages/HistorialPagina';
import VehiculosPagina from './pages/VehiculosPagina';
import ClientesPagina from './pages/ClientesPagina';
import VehiculosExternosPagina from './pages/VehiculosExternosPagina';

function RutasProtegidas() {
  return (
    <RutaProtegida>
      <Navegacion />
      <main style={{ padding: '2rem', backgroundColor: '#f9fafb', minHeight: 'calc(100vh - 65px)', boxSizing: 'border-box' }}>
        <Routes>
          <Route path="/" element={<DisponibilidadPagina />} />
          <Route path="/reservar" element={<NuevaReservaPagina />} />
          <Route path="/mis-reservas" element={<ReservasPagina />} />
          <Route path="/historial" element={<HistorialPagina />} />
          <Route path="/mis-vehiculos-externos" element={<RutaProtegida roles={['CLIENTE']}><VehiculosExternosPagina /></RutaProtegida>} />
          <Route path="/admin/vehiculos" element={<RutaProtegida roles={['ADMIN']}><VehiculosPagina /></RutaProtegida>} />
          <Route path="/admin/clientes" element={<RutaProtegida roles={['ADMIN']}><ClientesPagina /></RutaProtegida>} />
          <Route path="*" element={<DisponibilidadPagina />} />
        </Routes>
      </main>
    </RutaProtegida>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPagina />} />
          <Route path="/*" element={<RutasProtegidas />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}