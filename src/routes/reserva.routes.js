import { Router } from "express";
import { requireAuth } from "../auth/middleware.js";
import { crearReserva, cancelarReserva } from "../controllers/reserva.controller.js";

const router = Router();

router.use(requireAuth);
router.post("/", crearReserva);
router.patch("/:id/cancelar", cancelarReserva);
export default router;