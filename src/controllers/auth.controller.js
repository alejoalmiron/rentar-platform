import { customerClient } from '../grpc/customer.client.js';
import { toHttpError } from '../grpc/httpErrors.js';
import { revokeToken, signToken } from '../auth/jwt.js';

export async function login(req, res) {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ error: 'Usuario y contraseña son obligatorios', codigo: 'INVALID_ARGUMENT' });
  }

  try {
    const user = await customerClient.authenticate(username, password);
    const token = signToken({
      id: user.userId,
      username: user.username,
      role: user.role,
      customerId: user.customerId,
    });
    return res.json({
      token,
      expiresIn: 28800,
      user: {
        id: user.userId,
        username: user.username,
        role: user.role,
        customerId: user.customerId || null,
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