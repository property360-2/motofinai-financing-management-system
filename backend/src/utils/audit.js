import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export const recordAudit = async ({ userId, module, action, description, recordId = null }) => {
  if (!userId || !module || !action) return;

  await prisma.auditLog.create({
    data: {
      userId,
      module,
      action,
      recordId,
      description,
    },
  });
};
