import jwt from "jsonwebtoken";
import dotenv from "dotenv";
dotenv.config();

export const signToken = (payload) =>
  jwt.sign(payload, process.env.JWT_SECRET, { expiresIn: "1d" });

export const verifyToken = (token) =>
  jwt.verify(token, process.env.JWT_SECRET);
