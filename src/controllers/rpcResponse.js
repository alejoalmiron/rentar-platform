// Respuesta común de los controladores: ejecuta la llamada y traduce el resultado o el error.
import { toHttpError } from '../grpc/httpErrors.js';

export async function respondWithRpc(res, operation, mapResponse = (response) => response, successStatus = 200) {
  try {
    const response = await operation();
    return res.status(successStatus).json(mapResponse(response));
  } catch (error) {
    const mapped = toHttpError(error);
    return res.status(mapped.status).json(mapped.body);
  }
}