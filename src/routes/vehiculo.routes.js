import { Router } from 'express';
import { requireAuth, requireRole } from '../auth/middleware.js';
import { 
  getVehiculos, 
  getVehiculoById, 
  createVehiculo, 
  updateVehiculo, 
  deleteVehiculo 
} from '../controllers/vehiculo.controller.js';

const router = Router();

router.use(requireAuth);
router.get('/', getVehiculos);
router.get('/:id', getVehiculoById);
router.post('/', requireRole('ADMIN'), createVehiculo);
router.put('/:id', requireRole('ADMIN'), updateVehiculo);
router.delete('/:id', requireRole('ADMIN'), deleteVehiculo);

export default router;