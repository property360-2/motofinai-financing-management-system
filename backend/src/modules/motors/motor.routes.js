import express from "express";
import authMiddleware from "../../middlewares/authMiddleware.js";
import roleMiddleware from "../../middlewares/roleMiddleware.js";
import { auditLogger } from "../../middlewares/auditLogger.js";
import * as MotorController from "./motor.controller.js";

const router = express.Router();

router.use(authMiddleware);

router.get("/", roleMiddleware(["admin", "finance"]), MotorController.getMotors);
router.post("/", roleMiddleware(["admin"]), auditLogger, MotorController.addMotor);
router.patch("/:id", roleMiddleware(["admin"]), auditLogger, MotorController.editMotor);
router.delete("/:id", roleMiddleware(["admin"]), auditLogger, MotorController.deleteMotor);

export default router;
