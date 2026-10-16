import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { revokeToken, signToken, validateJwtConfiguration, verifyToken } from './jwt.js';

process.env.JWT_SECRET = 'unit-test-secret-with-at-least-32-characters';

after(() => {
  delete process.env.JWT_SECRET;
});

test('JWT incluye identidad y rol autenticados', () => {
  const token = signToken({ id: 'user-1', username: 'cliente', role: 'CLIENTE', customerId: 'customer-1' });
  const claims = verifyToken(token);

  assert.equal(claims.sub, 'user-1');
  assert.equal(claims.role, 'CLIENTE');
  assert.equal(claims.customerId, 'customer-1');
});

test('JWT manipulado o revocado es rechazado', () => {
  const token = signToken({ id: 'user-2', username: 'admin', role: 'ADMIN' });
  const [header, payload, signature] = token.split('.');
  const changedSignature = `${signature[0] === 'A' ? 'B' : 'A'}${signature.slice(1)}`;
  assert.throws(() => verifyToken(`${header}.${payload}.${changedSignature}`), { code: 16 });

  const claims = verifyToken(token);
  revokeToken(claims);
  assert.throws(() => verifyToken(token), { code: 16 });
});

test('producción rechaza el secreto de ejemplo', () => {
  const previousEnvironment = process.env.NODE_ENV;
  process.env.NODE_ENV = 'production';
  process.env.JWT_SECRET = 'cambiar-por-un-secreto-aleatorio-de-al-menos-32-caracteres';
  try {
    assert.throws(() => validateJwtConfiguration(), /no usar un ejemplo/);
  } finally {
    if (previousEnvironment === undefined) delete process.env.NODE_ENV;
    else process.env.NODE_ENV = previousEnvironment;
    process.env.JWT_SECRET = 'unit-test-secret-with-at-least-32-characters';
  }
});