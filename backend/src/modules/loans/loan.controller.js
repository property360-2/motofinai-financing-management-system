import * as LoanService from "./loan.service.js";

export const getLoans = async (req, res) => {
  const loans = await LoanService.getAllLoans();
  res.json(loans);
};

export const addLoan = async (req, res) => {
  try {
    const loan = await LoanService.createLoan(req.body, req.user.id);
    res.status(201).json(loan);
  } catch (e) {
    res.status(400).json({ message: e.message });
  }
};

export const updateStatus = async (req, res) => {
  try {
    const loan = await LoanService.updateLoanStatus(req.params.id, req.body.status);
    res.json(loan);
  } catch (e) {
    res.status(400).json({ message: e.message });
  }
};
