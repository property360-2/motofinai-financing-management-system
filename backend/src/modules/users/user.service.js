import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

export const getAll = () => prisma.user.findMany({ select: { id: true, username: true, email: true, role: true, status: true } });
export const updateStatus = (id, status) => prisma.user.update({ where: { id }, data: { status } });
