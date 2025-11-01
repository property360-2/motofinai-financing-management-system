import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

export const auditLogger = async (req, res, next) => {
  res.on("finish", async () => {
    const actions = ["POST", "PATCH", "DELETE"];
    if (actions.includes(req.method) && req.user) {
      await prisma.auditLog.create({
        data: {
          userId: req.user.id,
          module: req.originalUrl,
          action: req.method,
          description: `${req.method} ${req.originalUrl}`,
        },
      });
    }
  });
  next();
};
