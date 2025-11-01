import { PrismaClient } from "@prisma/client";
import bcrypt from "bcrypt";

const prisma = new PrismaClient();

async function main() {
  console.log("🌱 Seeding initial data...");

  // Clear existing
  await prisma.auditLog.deleteMany();
  await prisma.loanDocument.deleteMany();
  await prisma.payment.deleteMany();
  await prisma.loanApplication.deleteMany();
  await prisma.motor.deleteMany();
  await prisma.financingTerm.deleteMany();
  await prisma.user.deleteMany();

  // Users
  const adminPass = await bcrypt.hash("admin123", 10);
  const financePass = await bcrypt.hash("finance123", 10);

  const admin = await prisma.user.create({
    data: {
      username: "admin",
      email: "admin@motofinai.com",
      password: adminPass,
      role: "admin",
      status: "active",
    },
  });

  const finance = await prisma.user.create({
    data: {
      username: "finance",
      email: "finance@motofinai.com",
      password: financePass,
      role: "finance",
      status: "active",
    },
  });

  // Financing Terms
  const terms = await prisma.financingTerm.createMany({
    data: [
      { termYears: 1, interestRate: 5.0 },
      { termYears: 2, interestRate: 8.0 },
      { termYears: 3, interestRate: 10.5 },
      { termYears: 4, interestRate: 12.0 },
      { termYears: 5, interestRate: 15.0 },
    ],
  });

  // Motors
  await prisma.motor.createMany({
    data: [
      {
        type: "Scooter",
        brand: "Honda",
        model: "Click 125i",
        year: 2024,
        color: "Red",
        purchasePrice: 85000.0,
        status: "available",
        imageUrl: "/assets/motors/honda-click.jpg",
      },
      {
        type: "Underbone",
        brand: "Yamaha",
        model: "Sniper 155",
        year: 2023,
        color: "Blue",
        purchasePrice: 110000.0,
        status: "available",
        imageUrl: "/assets/motors/sniper.jpg",
      },
      {
        type: "Backbone",
        brand: "Suzuki",
        model: "Gixxer 150",
        year: 2022,
        color: "Black",
        purchasePrice: 95000.0,
        status: "available",
        imageUrl: "/assets/motors/gixxer.jpg",
      },
    ],
  });

  console.log("✅ Seeding completed successfully!");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
