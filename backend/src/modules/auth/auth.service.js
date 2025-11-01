import { PrismaClient } from "@prisma/client";
import { comparePassword, hashPassword } from "../../utils/password.js";
import { signToken } from "../../utils/jwt.js";
import { recordAudit } from "../../utils/audit.js";
const prisma = new PrismaClient();

const ALLOWED_ROLES = new Set(["admin", "finance"]);
const sanitizeUser = (user) => {
  if (!user) return user;
  const { password, ...safeUser } = user;
  return safeUser;
};

export const register = async (payload, actorId = null) => {
  const { username, email, password, role } = payload;
  if (!username || !email || !password || !role) throw new Error("Missing required fields");
  if (!ALLOWED_ROLES.has(role)) throw new Error("Invalid role");

  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) throw new Error("Email already in use");

  const hashed = await hashPassword(password);
  const user = await prisma.user.create({
    data: { username, email, password: hashed, role, status: "active" },
  });

  await recordAudit({
    userId: actorId ?? user.id,
    module: "users",
    action: "ADD",
    description: actorId
      ? `Created ${role} account (${email})`
      : `Registered new ${role} account (${email})`,
    recordId: user.id,
  });

  return sanitizeUser(user);
};

export const login = async (email, password) => {
  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) throw new Error("Invalid credentials");
  if (user.status !== "active") throw new Error("Account is not active. Contact an administrator.");

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

  await recordAudit({
    userId: user.id,
    module: "auth",
    action: "LOGIN",
    description: "User logged in",
  });

  return { token, user: sanitizeUser(user) };
};

export const logout = async (userId) => {
  if (!userId) return;

  await recordAudit({
    userId,
    module: "auth",
    action: "LOGOUT",
    description: "User logged out",
  });
};
