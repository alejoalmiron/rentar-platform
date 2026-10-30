// Los contratos gRPC prefijan los valores de enum con el nombre del enum
// (TIPO_VEHICULO_SEDAN); REST, GraphQL y el frontend usan el valor de dominio
// (SEDAN). Estas funciones traducen entre ambas representaciones.

export function toProtoEnum(prefix, value) {
  if (value === undefined || value === null || value === '') return `${prefix}_UNSPECIFIED`;
  return `${prefix}_${String(value).toUpperCase()}`;
}

export function fromProtoEnum(prefix, value) {
  if (typeof value !== 'string' || value === `${prefix}_UNSPECIFIED`) return null;
  return value.startsWith(`${prefix}_`) ? value.slice(prefix.length + 1) : value;
}
