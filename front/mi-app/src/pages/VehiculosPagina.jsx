import { useState, useEffect, useCallback } from 'react';
import Card from '../components/Card';
import CampoTexto from '../components/CampoTexto';
import Boton from '../components/Boton';
import Tabla from '../components/Tabla';

import { getVehiculos, crearVehiculo } from '../service/ConectarAlBackend';

export default function VehiculosPagina() {
  const [vehiculos, setVehiculos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [enviando, setEnviando] = useState(false);

  const [patente, setPatente] = useState('');
  const [marca, setMarca] = useState('');
  const [modelo, setModelo] = useState('');
  const [anio, setAnio] = useState('');
  const [color, setColor] = useState('');
  const [tipo, setTipo] = useState('SEDAN');
  const [precioDiario, setPrecioDiario] = useState('');

  const cargarListaVehiculos = useCallback(async () => {
    try {
      setCargando(true);
      const data = await getVehiculos();
      setVehiculos(Array.isArray(data) ? data : []);
    } catch {
      alert('Error al obtener la lista de vehículos desde el servidor.');
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    Promise.resolve().then(cargarListaVehiculos);
  }, [cargarListaVehiculos]);

  const handleAgregarVehiculo = async (e) => {
    e.preventDefault();

    if (!patente || !marca || !modelo || !anio || !precioDiario) {
      alert('Por favor, completá los campos obligatorios.');
      return;
    }

    setEnviando(true);

    const nuevoVehiculo = {
      patente: patente.trim().toUpperCase(),
      marca: marca.trim(),
      modelo: modelo.trim(),
      anio: parseInt(anio, 10),
      color: color.trim(),
      tipo,
      precioDiario: parseFloat(precioDiario)
    };

    try {
      await crearVehiculo(nuevoVehiculo);
      alert('¡Vehículo registrado con éxito!');
      
      setPatente('');
      setMarca('');
      setModelo('');
      setAnio('');
      setColor('');
      setTipo('SEDAN');
      setPrecioDiario('');

      await cargarListaVehiculos();
    } catch {
      alert('Error al registrar el vehículo. Verificá que la patente no esté duplicada.');
    } finally {
      setEnviando(false);
    }
  };

  const columnas = [
    { header: 'Patente', accessor: 'patente' },
    { header: 'Marca', accessor: 'marca' },
    { header: 'Modelo', accessor: 'modelo' },
    { header: 'Año', accessor: 'anio' },
    { header: 'Color', accessor: 'color' },
    { header: 'Tipo', accessor: 'tipo' },
    { header: 'Precio Diario', accessor: (row) => `$${row.precioDiario}` },
    { header: 'Verificación', accessor: 'estadoVerificacion' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Formulario de Alta */}
      <Card title="Administración de Vehículos (ABM - REST)">
        <form onSubmit={handleAgregarVehiculo}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '20px' }}>
            <CampoTexto 
              label="Patente *" 
              placeholder="Ej: AA123BC" 
              value={patente} 
              onChange={(e) => setPatente(e.target.value)} 
            />
            <CampoTexto 
              label="Marca *" 
              placeholder="Ej: Toyota" 
              value={marca} 
              onChange={(e) => setMarca(e.target.value)} 
            />
            <CampoTexto 
              label="Modelo *" 
              placeholder="Ej: Corolla" 
              value={modelo} 
              onChange={(e) => setModelo(e.target.value)} 
            />
            <CampoTexto 
              label="Año *" 
              type="number" 
              placeholder="Ej: 2022" 
              value={anio} 
              onChange={(e) => setAnio(e.target.value)} 
            />
            <CampoTexto 
              label="Color" 
              placeholder="Ej: Gris" 
              value={color} 
              onChange={(e) => setColor(e.target.value)} 
            />
            
            {/* Selector de Tipo de Vehículo */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <label style={{ fontWeight: '600', fontSize: '14px', color: '#374151' }}>Tipo de Vehículo</label>
              <select 
                value={tipo} 
                onChange={(e) => setTipo(e.target.value)}
                style={{
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #d1d5db',
                  fontSize: '14px',
                  backgroundColor: '#ffffff',
                  color: '#1f2937',
                  colorScheme: 'light'
                }}
              >
                <option value="SEDAN" style={{ color: '#1f2937', backgroundColor: '#ffffff' }}>SEDAN</option>
                <option value="HATCHBACK" style={{ color: '#1f2937', backgroundColor: '#ffffff' }}>HATCHBACK</option>
                <option value="SUV" style={{ color: '#1f2937', backgroundColor: '#ffffff' }}>SUV</option>
                <option value="PICKUP" style={{ color: '#1f2937', backgroundColor: '#ffffff' }}>PICKUP</option>
              </select>
            </div>

            <CampoTexto 
              label="Precio Diario ($) *" 
              type="number" 
              placeholder="Ej: 45000" 
              value={precioDiario} 
              onChange={(e) => setPrecioDiario(e.target.value)} 
            />
          </div>

          <Boton type="submit" disabled={enviando}>
            {enviando ? 'Guardando...' : 'Agregar Vehículo'}
          </Boton>
        </form>
      </Card>

      {/* Listado de Vehículos */}
      <Card title={`Listado de Vehículos Registrados (${vehiculos.length})`}>
        {cargando ? (
          <p style={{ textAlign: 'center', color: '#6b7280' }}>Cargando vehículos...</p>
        ) : (
          <Tabla columnas={columnas} datos={vehiculos} />
        )}
      </Card>
    </div>
  );
}