import { customerClient } from '../grpc/customer.client.js';
import { toHttpError } from '../grpc/httpErrors.js';
import { revokeToken, signToken } from '../auth/jwt.js';

// Customer Service valida la contraseña; el Gateway emite el JWT.
export async function login(req, res) {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ error: 'Usuario y contraseña son obligatorios', codigo: 'INVALID_ARGUMENT' });
  }

  try {
    const user = await customerClient.authenticate(username, password);
    const userId = user.userId || user.user_id;
    const customerId = user.customerId || user.customer_id;
    if (!userId || (user.role === 'CLIENTE' && !customerId)) {
      return res.status(503).json({
        error: 'El servicio de clientes devolvió una identidad incompleta',
        codigo: 'IDENTITY_INCOMPLETE',
      });
    }
    const token = signToken({
      id: userId,
      username: user.username,
      role: user.role,
      customerId,
    });
    return res.json({
      token,
      expiresIn: 28800,
      user: {
        id: userId,
        username: user.username,
        role: user.role,
        customerId: customerId || null,
      },
    });
  } catch (error) {
    const mapped = toHttpError(error);
    return res.status(mapped.status).json(mapped.body);
  }
}

export function logout(req, res) {
  revokeToken(req.auth);
  return res.status(204).end();
}