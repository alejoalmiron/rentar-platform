import { useState, useCallback } from 'react';
import Card from '../components/Card';
import CampoTexto from '../components/CampoTexto';
import Boton from '../components/Boton';
import Tabla from '../components/Tabla';

import { consultarGraphQL } from '../service/ConectarAlBackend';

const QUERY_HISTORIAL = `
  query ObtenerHistorialReservas($estado: String, $patente: String) {
    historialReservas(estado: $estado, patente: $patente) {
      id
      fechaInicio
      fechaFin
      estado
      montoTotal
      cliente {
        dni
        nombre
        apellido
      }
      vehiculo {
        patente
        marca
        modelo
      }
    }
  }
`;

export default function HistorialPagina() {
  const [historial, setHistorial] = useState([]);
  const [cargando, setCargando] = useState(false);

  const [estadoFiltro, setEstadoFiltro] = useState('');
  const [patenteFiltro, setPatenteFiltro] = useState('');

  const cargarHistorial = useCallback(async () => {
    if (!estadoFiltro && !patenteFiltro.trim()) {
      setHistorial([]);
      return;
    }

    setCargando(true);

    try {
      const variables = {
        estado: estadoFiltro || null,
        patente: patenteFiltro.trim().toUpperCase() || null,
      };

      const res = await consultarGraphQL(QUERY_HISTORIAL, variables);

      if (res?.data?.historialReservas) {
        setHistorial(res.data.historialReservas);
      } else {
        setHistorial([]);
      }
    } catch {
      alert('Error al cargar el historial de reservas desde el servidor.');
    } finally {
      setCargando(false);
    }
  }, [estadoFiltro, patenteFiltro]);

  const handleFiltrar = (e) => {
    e.preventDefault();
    cargarHistorial();
  };

  const columnas = [
    { header: 'ID', accessor: 'id' },
    {
      header: 'Cliente',
      accessor: (row) =>
        row.cliente
          ? `${row.cliente.apellido}, ${row.cliente.nombre} (${row.cliente.dni})`
          : 'N/A',
    },
    {
      header: 'Vehículo',
      accessor: (row) =>
        row.vehiculo
          ? `${row.vehiculo.marca} ${row.vehiculo.modelo} [${row.vehiculo.patente}]`
          : 'N/A',
    },
    { header: 'Fecha Inicio', accessor: 'fechaInicio' },
    { header: 'Fecha Fin', accessor: 'fechaFin' },
    { header: 'Monto Total', accessor: (row) => `$${row.montoTotal}` },
    {
      header: 'Estado',
      accessor: (row) => (
        <span
          style={{
            fontWeight: '600',
            color:
              row.estado === 'CONFIRMADA' || row.estado === 'ACTIVA'
                ? '#16a34a'
                : row.estado === 'CANCELADA'
                ? '#dc2626'
                : '#4b5563',
          }}
        >
          {row.estado}
        </span>
      ),
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Filtros de Búsqueda */}
      <Card title="Historial General de Reservas">
        <form onSubmit={handleFiltrar}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '15px',
              marginBottom: '20px',
            }}
          >
            <CampoTexto
              label="Filtrar por Patente"
              placeholder="Ej: AA123BC"
              value={patenteFiltro}
              onChange={(e) => setPatenteFiltro(e.target.value)}
            />

            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <label style={{ fontWeight: '600', fontSize: '14px', color: '#374151' }}>
                Filtrar por Estado
              </label>
              <select
                value={estadoFiltro}
                onChange={(e) => setEstadoFiltro(e.target.value)}
                style={{
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #d1d5db',
                  fontSize: '14px',
                  backgroundColor: '#ffffff',
                  color: '#1f2937',
                  colorScheme: 'light',
                }}
              >
                <option value="">Todos los estados</option>
                <option value="CONFIRMADA">CONFIRMADA</option>
                <option value="FINALIZADA">FINALIZADA</option>
                <option value="CANCELADA">CANCELADA</option>
              </select>
            </div>
          </div>

          <Boton type="submit" disabled={cargando}>
            {cargando ? 'Filtrando...' : 'Aplicar Filtros'}
          </Boton>
        </form>
      </Card>

      {/* Listado de Historial */}
      <Card title={`Registros Encontrados (${historial.length})`}>
        {cargando ? (
          <p style={{ textAlign: 'center', color: '#6b7280' }}>
            Cargando historial...
          </p>
        ) : (
          <Tabla columnas={columnas} datos={historial} />
        )}
      </Card>
    </div>
  );
}