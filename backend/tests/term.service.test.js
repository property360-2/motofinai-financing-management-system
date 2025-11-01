import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import {
  listTerms,
  createTerm,
  updateTerm,
  deleteTerm,
  __setTestContext,
} from "../src/modules/financingTerms/term.service.js";

let mockPrisma;
let auditSpy;

beforeEach(() => {
  mockPrisma = {
    financingTerm: {
      findMany: vi.fn().mockResolvedValue([]),
      create: vi.fn(),
      findUniqueOrThrow: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    loanApplication: {
      count: vi.fn(),
    },
  };

  auditSpy = vi.fn().mockResolvedValue();

  __setTestContext({
    prismaClient: mockPrisma,
    auditLogger: auditSpy,
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("financing term service", () => {
  it("lists terms ordered by years", async () => {
    await listTerms();
    expect(mockPrisma.financingTerm.findMany).toHaveBeenCalledWith({
      orderBy: { termYears: "asc" },
    });
  });

  it("throws when actor missing on create", async () => {
    await expect(
      createTerm({ termYears: 1, interestRate: 5 }, null)
    ).rejects.toThrow("Missing actor");
  });

  it("validates term years range", async () => {
    await expect(
      createTerm({ termYears: 0, interestRate: 5 }, 1)
    ).rejects.toThrow("termYears must be an integer between 1 and 7");
  });

  it("validates interest rate bounds", async () => {
    await expect(
      createTerm({ termYears: 2, interestRate: 120 }, 1)
    ).rejects.toThrow("interestRate must be a positive number below 100");
  });

  it("creates term with numeric values and logs audit", async () => {
    mockPrisma.financingTerm.create.mockResolvedValue({
      id: 4,
      termYears: 3,
      interestRate: 7.5,
    });

    await createTerm({ termYears: "3", interestRate: "7.5" }, 12);

    expect(mockPrisma.financingTerm.create).toHaveBeenCalledWith({
      data: { termYears: 3, interestRate: 7.5 },
    });
    expect(auditSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        userId: 12,
        action: "ADD",
        recordId: 4,
      })
    );
  });

  it("throws when updating with invalid id", async () => {
    await expect(updateTerm("nan", {}, 1)).rejects.toThrow("Invalid term id");
  });

  it("updates term with sanitized data", async () => {
    mockPrisma.financingTerm.findUniqueOrThrow.mockResolvedValue({ id: 2 });
    mockPrisma.financingTerm.update.mockResolvedValue({
      id: 2,
      interestRate: 9,
    });

    await updateTerm("2", { interestRate: "9.0" }, 5);

    expect(mockPrisma.financingTerm.update).toHaveBeenCalledWith({
      where: { id: 2 },
      data: { interestRate: 9 },
    });
    expect(auditSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        userId: 5,
        action: "EDIT",
        recordId: 2,
      })
    );
  });

  it("prevents deleting a term in use by loans", async () => {
    mockPrisma.loanApplication.count.mockResolvedValue(3);

    await expect(deleteTerm("1", 7)).rejects.toThrow(
      "Cannot delete a financing term that is used by loan applications"
    );
  });

  it("deletes unused term and records audit", async () => {
    mockPrisma.loanApplication.count.mockResolvedValue(0);
    mockPrisma.financingTerm.delete.mockResolvedValue({
      id: 6,
    });

    await deleteTerm("6", 7);

    expect(mockPrisma.financingTerm.delete).toHaveBeenCalledWith({
      where: { id: 6 },
    });
    expect(auditSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        userId: 7,
        action: "DELETE",
        recordId: 6,
      })
    );
  });
});
