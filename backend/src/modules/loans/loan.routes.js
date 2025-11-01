import express from "express";
import authMiddleware from "../../middlewares/authMiddleware.js";
import roleMiddleware from "../../middlewares/roleMiddleware.js";
import * as LoanController from "./loan.controller.js";
import { auditLogger } from "../../middlewares/auditLogger.js";

const router = express.Router();

router.use(authMiddleware, roleMiddleware(["finance", "admin"]), auditLogger);

router.get("/", LoanController.getLoans);
router.post("/", LoanController.addLoan);
router.patch("/:id/status", LoanController.updateStatus);

export default router;
