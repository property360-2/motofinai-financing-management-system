import express from "express";
import authMiddleware from "../../middlewares/authMiddleware.js";
import roleMiddleware from "../../middlewares/roleMiddleware.js";
import { auditLogger } from "../../middlewares/auditLogger.js";
import * as TermController from "./term.controller.js";

const router = express.Router();

router.use(authMiddleware);

router.get("/", roleMiddleware(["admin", "finance"]), TermController.list);
router.post("/", roleMiddleware(["admin"]), auditLogger, TermController.create);
router.patch("/:id", roleMiddleware(["admin"]), auditLogger, TermController.update);
router.delete("/:id", roleMiddleware(["admin"]), auditLogger, TermController.remove);

export default router;
