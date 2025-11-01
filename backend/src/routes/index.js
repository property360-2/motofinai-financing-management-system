import express from "express";
import authRoutes from "../modules/auth/auth.routes.js";
import userRoutes from "../modules/users/user.routes.js";
import motorRoutes from "../modules/motors/motor.routes.js";
import termRoutes from "../modules/financingTerms/term.routes.js";

const router = express.Router();
router.use("/auth", authRoutes);
router.use("/users", userRoutes);
router.use("/motors", motorRoutes);
router.use("/financing-terms", termRoutes);

router.get("/", (req, res) => res.json({ message: "MotofinAI API up ✅" }));
export default router;
