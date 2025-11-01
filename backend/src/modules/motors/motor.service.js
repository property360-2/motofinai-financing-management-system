import { PrismaClient } from "@prisma/client";
import { recordAudit as recordAuditDefault } from "../../utils/audit.js";

let prisma = new PrismaClient();
let auditRecorder = recordAuditDefault;

export const __setTestContext = ({ prismaClient, auditLogger } = {}) => {
  if (prismaClient) prisma = prismaClient;
  if (auditLogger) auditRecorder = auditLogger;
};

export const __resetTestContext = () => {
  prisma = new PrismaClient();
  auditRecorder = recordAuditDefault;
};
const ALLOWED_STATUS = new Set(["available", "reserved", "sold", "repossessed"]);
const REQUIRED_FIELDS = ["type", "brand", "model", "year", "purchasePrice"];
const OPTIONAL_FIELDS = ["status", "color", "chassisNo", "imageUrl"];

const sanitizeMotorPayload = (payload, { isUpdate = false } = {}) => {
  if (!payload || typeof payload !== "object") {
    throw new Error("Invalid payload");
  }

  const data = {};

  for (const field of REQUIRED_FIELDS) {
    const value = payload[field];

    if (value === undefined) {
      if (!isUpdate) throw new Error(`Missing required field: ${field}`);
      continue;
    }

    if (field === "year") {
      const year = parseInt(value, 10);
      if (Number.isNaN(year) || year < 1990) throw new Error("Invalid year supplied");
      data.year = year;
      continue;
    }

    if (field === "purchasePrice") {
      const price = Number(value);
      if (Number.isNaN(price) || price <= 0) throw new Error("Invalid purchase price supplied");
      data.purchasePrice = price;
      continue;
    }

    if (String(value).trim().length === 0) {
      throw new Error(`Field ${field} cannot be empty`);
    }

    data[field] = String(value).trim();
  }

  for (const field of OPTIONAL_FIELDS) {
    if (payload[field] === undefined || payload[field] === null) continue;

    if (field === "status") {
      const status = String(payload.status).toLowerCase();
      if (!ALLOWED_STATUS.has(status)) throw new Error("Invalid status value");
      data.status = status;
      continue;
    }

    const trimmed = String(payload[field]).trim();
    data[field] = trimmed.length ? trimmed : null;
  }

  if (!isUpdate && !data.status) {
    data.status = "available";
  }

  if (isUpdate && Object.keys(data).length === 0) {
    throw new Error("No valid fields provided for update");
  }

  return data;
};

export const getAllMotors = () =>
  prisma.motor.findMany({
    orderBy: { createdAt: "desc" },
  });

export const createMotor = async (payload, actorId) => {
  if (!actorId) throw new Error("Missing actor");
  const data = sanitizeMotorPayload(payload);

  const motor = await prisma.motor.create({ data });

  await auditRecorder({
    userId: actorId,
    module: "motors",
    action: "ADD",
    description: `Added motor ${motor.brand} ${motor.model} (${motor.id})`,
    recordId: motor.id,
  });

  return motor;
};

export const updateMotor = async (id, payload, actorId) => {
  if (!actorId) throw new Error("Missing actor");
  const motorId = parseInt(id, 10);
  if (Number.isNaN(motorId)) throw new Error("Invalid motor id");

  await prisma.motor.findUniqueOrThrow({ where: { id: motorId } });

  const data = sanitizeMotorPayload(payload, { isUpdate: true });

  const updated = await prisma.motor.update({ where: { id: motorId }, data });

  await auditRecorder({
    userId: actorId,
    module: "motors",
    action: "EDIT",
    description: `Updated motor ${updated.id}`,
    recordId: updated.id,
  });

  return updated;
};

export const archiveMotor = async (id, userId) => {
  if (!userId) throw new Error("Missing actor");
  const motorId = parseInt(id, 10);
  if (Number.isNaN(motorId)) throw new Error("Invalid motor id");

  const motor = await prisma.motor.findUnique({ where: { id: motorId } });
  if (!motor) throw new Error("Motor not found");

  await prisma.archive.create({
    data: {
      module: "motors",
      recordId: motor.id,
      archivedBy: userId,
      reason: "Archived by admin",
      dataSnapshot: motor,
    },
  });

  await prisma.motor.delete({ where: { id: motor.id } });

  await auditRecorder({
    userId,
    module: "motors",
    action: "ARCHIVE",
    description: `Archived motor ${motor.id}`,
    recordId: motor.id,
  });

  return motor;
};
