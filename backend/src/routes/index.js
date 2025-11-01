import express from "express";
import authRoutes from "../modules/auth/auth.routes.js";
import userRoutes from "../modules/users/user.routes.js";

const router = express.Router();
router.use("/auth", authRoutes);
router.use("/users", userRoutes);

router.get("/", (req, res) => res.json({ message: "MotofinAI API up ✅" }));
export default router;
