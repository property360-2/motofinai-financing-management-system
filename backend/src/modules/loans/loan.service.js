import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

export const getAllLoans = async () =>
  prisma.loanApplication.findMany({
    include: { motor: true, term: true, createdByUser: true },
    orderBy: { id: "desc" },
  });

export const createLoan = async (data, userId) => {
  return prisma.loanApplication.create({
    data: {
      ...data,
      createdBy: userId,
      applicationStatus: "pending",
    },
  });
};

export const updateLoanStatus = async (id, status) => {
  return prisma.loanApplication.update({
    where: { id: parseInt(id) },
    data: { applicationStatus: status },
  });
};
