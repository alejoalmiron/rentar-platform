import { useCallback, useEffect, useState } from 'react';
import Card from '../components/Card';
import CampoTexto from '../components/CampoTexto';
import Boton from '../components/Boton';
import Tabla from '../components/Tabla';
import { crearVehiculoExterno, getVehiculosExternos } from '../service/ConectarAlBackend';

const estados = {
  PENDIENTE: '#92400e',
  DISPONIBLE: '#166534',
  RECHAZADO: '#b91c1c',
};

export default function VehiculosExternosPagina() {
  const [vehiculos, setVehiculos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [formulario, setFormulario] = useState({
    patente: '',
    marca: '',
    modelo: '',
    anio: '',
    color: '',
    tipo: 'SEDAN',
    precioDiario: '',
  });

  const cargarVehiculos = useCallback(async () => {
    try {
      setCargando(true);
      setVehiculos(await getVehiculosExternos());
    } catch (error) {
      alert(error.message);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    Promise.resolve().then(cargarVehiculos);
    const intervalo = window.setInterval(cargarVehiculos, 5000);
    return () => window.clearInterval(intervalo);
  }, [cargarVehiculos]);

  function cambiarCampo(event) {
    setFormulario((actual) => ({ ...actual, [event.target.name]: event.target.value }));
  }

  async function registrar(event) {
    event.preventDefault();
    setEnviando(true);
    try {
      await crearVehiculoExterno({
        ...formulario,
        patente: formulario.patente.trim().toUpperCase(),
        marca: formulario.marca.trim(),
        modelo: formulario.modelo.trim(),
        anio: formulario.anio ? Number(formulario.anio) : null,
        precioDiario: Number(formulario.precioDiario),
      });
      setFormulario({
        patente: '',
        marca: '',
        modelo: '',
        anio: '',
        color: '',
        tipo: 'SEDAN',
        precioDiario: '',
      });
      await cargarVehiculos();
    } catch (error) {
      alert(error.message);
    } finally {
      setEnviando(false);
    }
  }

  const columnas = [
    { header: 'Patente', accessor: 'patente' },
    { header: 'Marca', accessor: 'marca' },
    { header: 'Modelo', accessor: 'modelo' },
    { header: 'Tipo', accessor: 'tipo' },
    { header: 'Precio Diario', accessor: (vehiculo) => `$${vehiculo.precioDiario}` },
    {
      header: 'Estado',
      accessor: (vehiculo) => (
        <strong style={{ color: estados[vehiculo.estado] || '#374151' }}>
          {vehiculo.estado}
        </strong>
      ),
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <Card title="Registrar vehículo externo">
        <form onSubmit={registrar}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
            <CampoTexto label="Patente *" name="patente" value={formulario.patente} onChange={cambiarCampo} required />
            <CampoTexto label="Marca *" name="marca" value={formulario.marca} onChange={cambiarCampo} required />
            <CampoTexto label="Modelo *" name="modelo" value={formulario.modelo} onChange={cambiarCampo} required />
            <CampoTexto label="Año" name="anio" type="number" value={formulario.anio} onChange={cambiarCampo} />
            <CampoTexto label="Color" name="color" value={formulario.color} onChange={cambiarCampo} />
            <CampoTexto label="Precio Diario ($) *" name="precioDiario" type="number" value={formulario.precioDiario} onChange={cambiarCampo} required />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label htmlFor="tipo" style={{ fontWeight: '600', fontSize: '14px', color: '#374151' }}>Tipo</label>
              <select id="tipo" name="tipo" value={formulario.tipo} onChange={cambiarCampo} style={{ padding: '10px', borderRadius: '6px', border: '1px solid #d1d5db' }}>
                <option value="SEDAN">SEDAN</option>
                <option value="HATCHBACK">HATCHBACK</option>
                <option value="SUV">SUV</option>
                <option value="PICKUP">PICKUP</option>
                <option value="COUPE">COUPE</option>
              </select>
            </div>
          </div>
          <Boton type="submit" disabled={enviando}>
            {enviando ? 'Registrando...' : 'Registrar vehículo'}
          </Boton>
        </form>
      </Card>
      <Card title="Mis incorporaciones">
        {cargando ? <p>Cargando incorporaciones...</p> : <Tabla columnas={columnas} datos={vehiculos} />}
      </Card>
    </div>
  );
}
