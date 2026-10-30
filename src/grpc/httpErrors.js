// Traduce los códigos de error gRPC a respuestas HTTP y a errores GraphQL.
import grpc from '@grpc/grpc-js';

const grpcToHttpStatus = new Map([
  [grpc.status.INVALID_ARGUMENT, 400],
  [grpc.status.UNAUTHENTICATED, 401],
  [grpc.status.PERMISSION_DENIED, 403],
  [grpc.status.NOT_FOUND, 404],
  [grpc.status.ALREADY_EXISTS, 409],
  [grpc.status.FAILED_PRECONDITION, 409],
  [grpc.status.ABORTED, 409],
  [grpc.status.DEADLINE_EXCEEDED, 504],
  [grpc.status.UNAVAILABLE, 503],
  [grpc.status.UNIMPLEMENTED, 501],
]);

export function toHttpError(error) {
  return {
    status: grpcToHttpStatus.get(error?.code) || 500,
    body: {
      error: error?.details || error?.message || 'Error al comunicarse con un servicio interno',
      codigo: typeof error?.code === 'number' ? grpc.status[error.code] : 'INTERNAL',
    },
  };
}

// GraphQL informa el error dentro de errors[].extensions, no con el estado HTTP.
export function toGraphqlError(error) {
  const mapped = toHttpError(error);
  const graphqlError = new Error(mapped.body.error);
  graphqlError.extensions = {
    code: mapped.body.codigo,
    http: { status: mapped.status },
  };
  return graphqlError;
}