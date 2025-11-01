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

const MIN_TERM = 1;
const MAX_TERM = 7;

const sanitizeTermPayload = (payload, { isUpdate = false } = {}) => {
  if (!payload || typeof payload !== "object") throw new Error("Invalid payload");

  const data = {};

  if (!isUpdate || payload.termYears !== undefined) {
    const years = Number(payload.termYears);
    if (!Number.isInteger(years) || years < MIN_TERM || years > MAX_TERM) {
      throw new Error(`termYears must be an integer between ${MIN_TERM} and ${MAX_TERM}`);
    }
    data.termYears = years;
  }

  if (!isUpdate || payload.interestRate !== undefined) {
    const rate = Number(payload.interestRate);
    if (Number.isNaN(rate) || rate <= 0 || rate >= 100) {
      throw new Error("interestRate must be a positive number below 100");
    }
    data.interestRate = rate;
  }

  if (isUpdate && Object.keys(data).length === 0) {
    throw new Error("No valid fields supplied");
  }

  return data;
};

export const listTerms = async () =>
  prisma.financingTerm.findMany({
    orderBy: { termYears: "asc" },
  });

export const createTerm = async (payload, actorId) => {
  if (!actorId) throw new Error("Missing actor");
  const data = sanitizeTermPayload(payload);

  const term = await prisma.financingTerm.create({ data });

  await auditRecorder({
    userId: actorId,
    module: "financingTerms",
    action: "ADD",
    description: `Created ${term.termYears}-year term at ${term.interestRate}%`,
    recordId: term.id,
  });

  return term;
};

export const updateTerm = async (id, payload, actorId) => {
  if (!actorId) throw new Error("Missing actor");
  const termId = parseInt(id, 10);
  if (Number.isNaN(termId)) throw new Error("Invalid term id");

  await prisma.financingTerm.findUniqueOrThrow({ where: { id: termId } });

  const data = sanitizeTermPayload(payload, { isUpdate: true });

  const term = await prisma.financingTerm.update({
    where: { id: termId },
    data,
  });

  await auditRecorder({
    userId: actorId,
    module: "financingTerms",
    action: "EDIT",
    description: `Updated term ${term.id}`,
    recordId: term.id,
  });

  return term;
};

export const deleteTerm = async (id, actorId) => {
  if (!actorId) throw new Error("Missing actor");
  const termId = parseInt(id, 10);
  if (Number.isNaN(termId)) throw new Error("Invalid term id");

  const usageCount = await prisma.loanApplication.count({ where: { termId } });
  if (usageCount > 0) {
    throw new Error("Cannot delete a financing term that is used by loan applications");
  }

  const term = await prisma.financingTerm.delete({
    where: { id: termId },
  });

  await auditRecorder({
    userId: actorId,
    module: "financingTerms",
    action: "DELETE",
    description: `Deleted term ${term.id}`,
    recordId: term.id,
  });

  return term;
};
