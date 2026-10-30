import { useState } from 'react';
import Card from '../components/Card';
import CampoTexto from '../components/CampoTexto';
import Boton from '../components/Boton';
import Tabla from '../components/Tabla';

import { consultarGraphQL } from '../service/ConectarAlBackend';
import { useAuth } from '../context/useAuth';

export default function ReservasPagina() {
  const { user } = useAuth();
  const esAdmin = user?.role === 'ADMIN';
  const [dniFiltro, setDniFiltro] = useState('');
  const [reservas, setReservas] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [buscado, setBuscado] = useState(false);

  const QUERY_RESERVAS_CLIENTE = `
    query ObtenerReservasCliente($dni: String) {
      reservasPorCliente(dni: $dni) {
        id
        fechaInicio
        fechaFin
        estado
        montoTotal
        resultadoMantenimiento
        vehiculo {
          patente
          marca
          modelo
        }
      }
    }
  `;

  const MUTATION_CANCELAR_RESERVA = `
    mutation CancelarReserva($id: ID!) {
      cancelarReserva(id: $id) {
        id
        estado
      }
    }
  `;

  const handleBuscarReservas = async (e) => {
    e.preventDefault();
    if (esAdmin && !dniFiltro.trim()) {
      alert('Ingresá un DNI para buscar las reservas.');
      return;
    }

    setCargando(true);
    setBuscado(true);

    try {
      const res = await consultarGraphQL(QUERY_RESERVAS_CLIENTE, {
        dni: esAdmin ? dniFiltro.trim() : null,
      });
      if (res?.data?.reservasPorCliente) {
        setReservas(res.data.reservasPorCliente);
      } else {
        setReservas([]);
      }
    } catch {
      alert('Error al buscar las reservas del cliente.');
    } finally {
      setCargando(false);
    }
  };

  const handleCancelar = async (idReserva) => {
    if (!window.confirm('¿Estás seguro de que querés cancelar esta reserva?')) {
      return;
    }

    try {
      const res = await consultarGraphQL(MUTATION_CANCELAR_RESERVA, { id: idReserva });
      if (res?.data?.cancelarReserva) {
        alert('Reserva cancelada con éxito.');
        setReservas((prev) =>
          prev.map((r) => (r.id === idReserva ? { ...r, estado: 'CANCELADA' } : r))
        );
      }
    } catch {
      alert('Error al intentar cancelar la reserva.');
    }
  };

  const columnas = [
    { header: 'ID Reserva', accessor: 'id' },
    { header: 'Vehículo', accessor: (row) => `${row.vehiculo?.marca || ''} ${row.vehiculo?.modelo || ''} (${row.vehiculo?.patente || ''})` },
    { header: 'Fecha Inicio', accessor: 'fechaInicio' },
    { header: 'Fecha Fin', accessor: 'fechaFin' },
    { header: 'Monto Total', accessor: (row) => `$${row.montoTotal}` },
    { header: 'Estado', accessor: 'estado' },
    { header: 'Mantenimiento', accessor: 'resultadoMantenimiento' },
    {
      header: 'Acciones',
      accessor: (row) =>
        row.estado !== 'CANCELADA' ? (
          <button
            onClick={() => handleCancelar(row.id)}
            style={{
              backgroundColor: '#ef4444',
              color: '#ffffff',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: '600'
            }}
          >
            Cancelar
          </button>
        ) : (
          <span style={{ color: '#9ca3af', fontSize: '12px' }}>Sin acciones</span>
        ),
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <Card title="Mis Reservas">
        <form onSubmit={handleBuscarReservas} style={{ display: 'flex', gap: '15px', alignItems: 'flex-end' }}>
          {esAdmin && <div style={{ flex: 1 }}>
            <CampoTexto label="DNI del Cliente *" placeholder="Ej: 38999111" value={dniFiltro} onChange={(e) => setDniFiltro(e.target.value)} />
          </div>}
          <Boton type="submit" disabled={cargando}>
            {cargando ? 'Buscando...' : 'Buscar Reservas'}
          </Boton>
        </form>
      </Card>

      {buscado && (
        <Card title={`Reservas encontradas (${reservas.length})`}>
          {cargando ? (
            <p style={{ textAlign: 'center', color: '#6b7280' }}>Cargando reservas...</p>
          ) : (
            <Tabla columnas={columnas} datos={reservas} />
          )}
        </Card>
      )}
    </div>
  );
}