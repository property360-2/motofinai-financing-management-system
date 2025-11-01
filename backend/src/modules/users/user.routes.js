import express from "express";
import authMiddleware from "../../middlewares/authMiddleware.js";
import roleMiddleware from "../../middlewares/roleMiddleware.js";
import * as UserController from "./user.controller.js";

const router = express.Router();
router.use(authMiddleware, roleMiddleware(["admin"]));

router.get("/", UserController.getUsers);
router.post("/", UserController.createUser);
router.patch("/:id/status", UserController.changeStatus);

export default router;
