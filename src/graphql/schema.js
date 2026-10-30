export const typeDefs = `
  """Categoría de carrocería admitida para un vehículo."""
  enum TipoVehiculo {
    """Sedán de cuatro puertas."""
    SEDAN
    """Vehículo utilitario deportivo."""
    SUV
    """Camioneta tipo pickup."""
    PICKUP
    """Vehículo cupé."""
    COUPE
    """Vehículo compacto hatchback."""
    HATCHBACK
  }

  """Estado operativo/comercial registrado para un vehículo."""
  enum EstadoVehiculo {
    """Vehículo habilitado para operar."""
    DISPONIBLE
    """Vehículo actualmente en alquiler."""
    EN_ALQUILER
  }

  """Datos de un vehículo devueltos por las consultas."""
  type Vehiculo {
    """Identificador del servicio de vehículos."""
    id: ID!
    """Patente única del vehículo."""
    patente: String!
    """Marca del fabricante."""
    marca: String!
    """Modelo del vehículo."""
    modelo: String!
    """Año de fabricación."""
    anio: Int!
    """Color; puede no estar informado."""
    color: String
    """Categoría del vehículo."""
    tipo: TipoVehiculo!
    """Precio por día en la moneda configurada por el sistema."""
    precioDiario: Float!
    """Estado registrado para el vehículo."""
    estado: EstadoVehiculo!
    """Indica si el registro continúa activo."""
    activo: Boolean!
    """Resultado de la verificación policial: PENDIENTE, VALIDADO o ROBADO."""
    estadoVerificacion: String
  }

  """Datos públicos de un cliente."""
  type Cliente {
    """Identificador del servicio de clientes."""
    id: ID!
    """Documento nacional de identidad."""
    dni: String!
    """Nombre del cliente."""
    nombre: String!
    """Apellido del cliente."""
    apellido: String!
    """Correo electrónico."""
    email: String!
    """Teléfono; puede no estar informado."""
    telefono: String
  }

  """Reserva o alquiler registrado."""
  type Reserva {
    """Identificador de la reserva."""
    id: ID!
    """Inicio del período en formato ISO-8601."""
    fechaInicio: String!
    """Fin del período en formato ISO-8601."""
    fechaFin: String!
    """Estado actual de la reserva."""
    estado: EstadoReserva!
    """Importe calculado por Rental Service."""
    montoTotal: Float!
    """Mantenimiento preventivo: PENDIENTE, REALIZADO o NO_REALIZADO."""
    resultadoMantenimiento: String
    """Cliente asociado a la reserva; puede ser null si el registro ya no existe en Customer Service."""
    cliente: Cliente
    """Vehículo asociado a la reserva; puede ser null si el registro ya no existe en Vehicle Service."""
    vehiculo: Vehiculo
  }

  """Estados de ciclo de vida de una reserva."""
  enum EstadoReserva {
    """Reserva confirmada y vigente."""
    CONFIRMADA
    """Reserva cancelada."""
    CANCELADA
    """Alquiler finalizado."""
    FINALIZADA
  }

  """Consultas de vehículos, reservas e historial."""
  type Query {
    """
    Devuelve vehículos operativos y sin solapamientos durante el período solicitado.
    Los filtros de marca, modelo, tipo y precio son opcionales.
    """
    vehiculosDisponibles(
      """Filtra por categoría de vehículo."""
      tipo: String
      """Filtra por marca (coincidencia exacta en el servicio actual)."""
      marca: String
      """Filtra por modelo (coincidencia exacta en el servicio actual)."""
      modelo: String
      """Precio diario mínimo inclusivo."""
      precioMin: Float
      """Precio diario máximo inclusivo."""
      precioMax: Float
      """Inicio del período solicitado, en formato ISO-8601."""
      fechaInicio: String!
      """Fin del período solicitado, posterior al inicio, en formato ISO-8601."""
      fechaFin: String!
    ): [Vehiculo!]!

    """
    Devuelve las reservas de un cliente. Un cliente autenticado solo puede consultar las propias;
    el DNI es opcional para el cliente y obligatorio para el administrador.
    """
    reservasPorCliente(dni: String): [Reserva!]!

    """
    Devuelve el historial. El administrador puede consultar todos los registros;
    el cliente autenticado recibe únicamente los propios.
    """
    historialReservas(estado: String, patente: String): [Reserva!]!
  }

  """Operaciones que cambian el estado de una reserva."""
  type Mutation {
    """
    Cancela una reserva. El cliente solo puede cancelar una reserva propia que todavía no comenzó;
    el administrador puede cancelar reservas de cualquier cliente.
    """
    cancelarReserva(id: ID!): Reserva!
  }
`;