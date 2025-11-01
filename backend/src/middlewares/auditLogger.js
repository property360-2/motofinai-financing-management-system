import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

const METHOD_TO_ACTION = {
  POST: "ADD",
  PUT: "EDIT",
  PATCH: "EDIT",
  DELETE: "DELETE",
};

export const auditLogger = (req, res, next) => {
  res.on("finish", () => {
    const action = METHOD_TO_ACTION[req.method];
    if (!action || !req.user || res.statusCode >= 400) return;

    const module = req.baseUrl || req.originalUrl;
    const description = `${req.method} ${req.originalUrl}`;

    prisma.auditLog
      .create({
        data: {
          userId: req.user.id,
          module,
          action,
          description,
        },
      })
      .catch((err) => {
        console.error("Failed to record audit log:", err.message);
      });
  });
  next();
};
