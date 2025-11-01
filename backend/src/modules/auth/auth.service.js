import { PrismaClient } from "@prisma/client";
import { comparePassword, hashPassword } from "../../utils/password.js";
import { signToken } from "../../utils/jwt.js";
const prisma = new PrismaClient();

export const register = async (payload) => {
  const { username, email, password, role } = payload;
  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) throw new Error("Email already in use");

  const hashed = await hashPassword(password);
  const user = await prisma.user.create({
    data: { username, email, password: hashed, role },
  });
  return user;
};

export const login = async (email, password) => {
  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) throw new Error("Invalid credentials");

  const valid = await comparePassword(password, user.password);
  if (!valid) throw new Error("Invalid credentials");

  const token = signToken({
    id: user.id,
    role: user.role,
    username: user.username,
  });

  await prisma.user.update({
    where: { id: user.id },
    data: { lastLogin: new Date() },
  });

  return { token, user };
};
