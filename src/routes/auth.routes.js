import { Router } from 'express';
import { login, logout } from '../controllers/auth.controller.js';
import { requireAuth } from '../auth/middleware.js';

const router = Router();

router.post('/login', login);
router.post('/logout', requireAuth, logout);

export default router;