import express from "express";
import * as AuthController from "./auth.controller.js";
import authMiddleware from "../../middlewares/authMiddleware.js";
import roleMiddleware from "../../middlewares/roleMiddleware.js";

const router = express.Router();

router.post("/login", AuthController.login);
router.post(
  "/register",
  authMiddleware,
  roleMiddleware(["admin"]),
  AuthController.register
);
router.post("/logout", authMiddleware, AuthController.logout);

export default router;
