import bcrypt from "bcrypt";

export const hashPassword = async (plain) => await bcrypt.hash(plain, 10);
export const comparePassword = async (plain, hash) => await bcrypt.compare(plain, hash);
