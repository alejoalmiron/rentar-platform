import { Router } from 'express';
import {
  listarVehiculosExternos,
  registrarVehiculoExterno,
} from '../controllers/vehiculoExterno.controller.js';
import { requireAuth, requireRole } from '../auth/middleware.js';

const router = Router();

router.get('/vehiculos-externos', requireAuth, requireRole('CLIENTE'), listarVehiculosExternos);
router.post('/vehiculos-externos', requireAuth, requireRole('CLIENTE'), registrarVehiculoExterno);

export default router;