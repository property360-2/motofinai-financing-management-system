import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { createMotor, updateMotor, archiveMotor, getAllMotors, __setTestContext } from "../src/modules/motors/motor.service.js";

let mockPrisma;
let auditSpy;

beforeEach(() => {
  mockPrisma = {
    motor: {
      findMany: vi.fn().mockResolvedValue([]),
      create: vi.fn(),
      findUniqueOrThrow: vi.fn(),
      update: vi.fn(),
      findUnique: vi.fn(),
      delete: vi.fn(),
    },
    archive: {
      create: vi.fn(),
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

describe("motor.service", () => {
  const basePayload = {
    type: "Scooter",
    brand: "Honda",
    model: "Click 125i",
    year: "2024",
    purchasePrice: "85000",
  };

  it("returns motors via getAllMotors", async () => {
    await getAllMotors();
    expect(mockPrisma.motor.findMany).toHaveBeenCalledWith({
      orderBy: { createdAt: "desc" },
    });
  });

  it("throws when actorId missing on create", async () => {
    await expect(createMotor(basePayload, null)).rejects.toThrow("Missing actor");
  });

  it("rejects when required fields are missing", async () => {
    await expect(
      createMotor({ ...basePayload, brand: undefined }, 1)
    ).rejects.toThrow("Missing required field: brand");
  });

  it("creates motor with normalized values and records audit", async () => {
    mockPrisma.motor.create.mockResolvedValue({
      id: 10,
      ...basePayload,
      year: 2024,
      purchasePrice: 85000,
      status: "available",
    });

    await createMotor(basePayload, 99);

    expect(mockPrisma.motor.create).toHaveBeenCalledWith({
      data: {
        type: "Scooter",
        brand: "Honda",
        model: "Click 125i",
        year: 2024,
        purchasePrice: 85000,
        status: "available",
      },
    });

    expect(auditSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        userId: 99,
        module: "motors",
        action: "ADD",
        recordId: 10,
      })
    );
  });

  it("throws on update with invalid id", async () => {
    await expect(updateMotor("abc", {}, 1)).rejects.toThrow("Invalid motor id");
  });

  it("updates motor with sanitized payload", async () => {
    mockPrisma.motor.findUniqueOrThrow.mockResolvedValue({
      id: 5,
    });
    mockPrisma.motor.update.mockResolvedValue({
      id: 5,
      status: "reserved",
    });

    await updateMotor(
      "5",
      {
        status: "reserved",
        purchasePrice: "120000.50",
      },
      7
    );

    expect(mockPrisma.motor.update).toHaveBeenCalledWith({
      where: { id: 5 },
      data: {
        status: "reserved",
        purchasePrice: 120000.5,
      },
    });

    expect(auditSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        userId: 7,
        action: "EDIT",
        recordId: 5,
      })
    );
  });

  it("throws when archiving unknown motor", async () => {
    mockPrisma.motor.findUnique.mockResolvedValue(null);
    await expect(archiveMotor(1, 3)).rejects.toThrow("Motor not found");
  });

  it("archives motor and logs audit", async () => {
    const motor = { id: 2, brand: "Yamaha" };
    mockPrisma.motor.findUnique.mockResolvedValue(motor);
    mockPrisma.motor.delete.mockResolvedValue(motor);

    await archiveMotor("2", 8);

    expect(mockPrisma.archive.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          module: "motors",
          archivedBy: 8,
          recordId: 2,
        }),
      })
    );

    expect(mockPrisma.motor.delete).toHaveBeenCalledWith({ where: { id: 2 } });
    expect(auditSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        userId: 8,
        action: "ARCHIVE",
        recordId: 2,
      })
    );
  });
});
