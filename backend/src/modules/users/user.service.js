import { PrismaClient } from "@prisma/client";
import { hashPassword } from "../../utils/password.js";
import { recordAudit } from "../../utils/audit.js";

const prisma = new PrismaClient();
const ALLOWED_ROLES = new Set(["admin", "finance"]);
const ALLOWED_STATUS = new Set(["active", "suspended"]);

const selectFields = {
  id: true,
  username: true,
  email: true,
  role: true,
  status: true,
  lastLogin: true,
  createdAt: true,
};

export const getAll = () =>
  prisma.user.findMany({
    select: selectFields,
    orderBy: { createdAt: "desc" },
  });

export const createUser = async (payload, actorId) => {
  const { username, email, password, role, status = "active" } = payload;
  if (!actorId) throw new Error("Missing actor");
  if (!username || !email || !password || !role) throw new Error("Missing required fields");
  if (!ALLOWED_ROLES.has(role)) throw new Error("Invalid role");
  if (!ALLOWED_STATUS.has(status)) throw new Error("Invalid status");

  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) throw new Error("Email already in use");

  const hashed = await hashPassword(password);
  const user = await prisma.user.create({
    data: { username, email, password: hashed, role, status },
    select: selectFields,
  });

  await recordAudit({
    userId: actorId,
    module: "users",
    action: "ADD",
    description: `Created ${role} account (${email})`,
    recordId: user.id,
  });

  return user;
};

export const updateStatus = async (id, status, actorId) => {
  if (!actorId) throw new Error("Missing actor");
  if (!ALLOWED_STATUS.has(status)) throw new Error("Invalid status");

  const user = await prisma.user.update({
    where: { id },
    data: { status },
    select: selectFields,
  });

  await recordAudit({
    userId: actorId,
    module: "users",
    action: "EDIT",
    description: `Changed status for ${user.email} to ${status}`,
    recordId: user.id,
  });

  return user;
};
