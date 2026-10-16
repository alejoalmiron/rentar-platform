import { randomUUID } from 'node:crypto';
import jwt from 'jsonwebtoken';

const revokedTokens = new Map();
const tokenLifetimeSeconds = 8 * 60 * 60;

export class AuthenticationError extends Error {
  constructor(message = 'Se requiere iniciar sesión') {
    super(message);
    this.code = 16;
  }
}

export class AuthorizationError extends Error {
  constructor(message = 'No tenés permisos para realizar esta operación') {
    super(message);
    this.code = 7;
  }
}

function getSecret() {
  const secret = process.env.JWT_SECRET;
  const isExampleSecret = /^(cambiar-por|rentar-compose-development)/i.test(secret || '');
  if (!secret || secret.length < 32 || (process.env.NODE_ENV === 'production' && isExampleSecret)) {
    throw new Error('Definí JWT_SECRET aleatorio de al menos 32 caracteres en el entorno');
  }
  return secret;
}

export function validateJwtConfiguration() {
  getSecret();
}

function pruneRevokedTokens(now) {
  for (const [tokenId, expiresAt] of revokedTokens) {
    if (expiresAt <= now) revokedTokens.delete(tokenId);
  }
}

export function signToken(user) {
  return jwt.sign({
    username: user.username,
    role: user.role,
    customerId: user.customerId || null,
  }, getSecret(), {
    algorithm: 'HS256',
    expiresIn: tokenLifetimeSeconds,
    issuer: 'rentar-api-gateway',
    subject: String(user.id),
    jwtid: randomUUID(),
  });
}

export function verifyToken(token) {
  let payload;
  try {
    payload = jwt.verify(token, getSecret(), {
      algorithms: ['HS256'],
      issuer: 'rentar-api-gateway',
    });
  } catch {
    throw new AuthenticationError('Token inválido o vencido');
  }

  const now = Math.floor(Date.now() / 1000);
  pruneRevokedTokens(now);
  if (typeof payload !== 'object' || !payload.sub || !['ADMIN', 'CLIENTE'].includes(payload.role)
    || !payload.exp || payload.exp <= now || revokedTokens.has(payload.jti)) {
    throw new AuthenticationError('Token vencido o revocado');
  }

  return payload;
}

export function getBearerToken(request) {
  const header = request.get?.('authorization') || request.headers?.authorization || '';
  const match = /^Bearer\s+([^\s]+)$/i.exec(header);
  return match?.[1] || null;
}

export function authenticateRequest(request) {
  const token = getBearerToken(request);
  if (!token) throw new AuthenticationError();
  return { ...verifyToken(token), token };
}

export function optionalAuthentication(request) {
  try {
    return authenticateRequest(request);
  } catch {
    return null;
  }
}

export function revokeToken(auth) {
  if (auth?.jti && auth.exp) revokedTokens.set(auth.jti, auth.exp);
}

export function requireRoles(auth, ...roles) {
  if (!auth) throw new AuthenticationError();
  if (!roles.includes(auth.role)) throw new AuthorizationError();
}