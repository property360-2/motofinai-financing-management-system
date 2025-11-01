import express from "express";
import authMiddleware from "../../middlewares/authMiddleware.js";
import roleMiddleware from "../../middlewares/roleMiddleware.js";
import * as UserController from "./user.controller.js";

const router = express.Router();
router.use(authMiddleware);

router.get("/", roleMiddleware(["admin"]), UserController.getUsers);
router.patch("/:id/status", roleMiddleware(["admin"]), UserController.changeStatus);

export default router;
