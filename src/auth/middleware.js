// Middlewares de Express: exigen sesión (401) y rol permitido (403).
import { authenticateRequest, requireRoles } from './jwt.js';

export function requireAuth(req, res, next) {
  try {
    req.auth = authenticateRequest(req);
    next();
  } catch (error) {
    res.status(401).json({ error: error.message, codigo: 'UNAUTHENTICATED' });
  }
}

export function requireRole(...roles) {
  return (req, res, next) => {
    try {
      requireRoles(req.auth, ...roles);
      next();
    } catch (error) {
      res.status(403).json({ error: error.message, codigo: 'FORBIDDEN' });
    }
  };
}

export function requireAdminOrOwnCustomer(req, res, next) {
  if (req.auth.role === 'ADMIN' || req.auth.customerId === req.params.id) return next();
  return res.status(403).json({
    error: 'Solo podés acceder a tus propios datos de cliente',
    codigo: 'FORBIDDEN',
  });
}