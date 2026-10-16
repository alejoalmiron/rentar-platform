import { Router } from 'express';
import { requireAdminOrOwnCustomer, requireAuth, requireRole } from '../auth/middleware.js';
import { 
  getClientes, 
  getClienteById, 
  createCliente, 
  updateCliente, 
  deleteCliente 
} from '../controllers/cliente.controller.js';

const router = Router();

router.use(requireAuth);
router.get('/', getClientes);
router.get('/:id', requireAdminOrOwnCustomer, getClienteById);
router.post('/', requireRole('ADMIN'), createCliente);
router.put('/:id', requireRole('ADMIN'), updateCliente);
router.delete('/:id', requireRole('ADMIN'), deleteCliente);

export default router;