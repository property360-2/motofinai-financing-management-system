import * as TermService from "./term.service.js";

export const list = async (req, res) => {
  try {
    const terms = await TermService.listTerms();
    res.json(terms);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
};

export const create = async (req, res) => {
  try {
    const term = await TermService.createTerm(req.body, req.user.id);
    res.status(201).json(term);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
};

export const update = async (req, res) => {
  try {
    const term = await TermService.updateTerm(req.params.id, req.body, req.user.id);
    res.json(term);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
};

export const remove = async (req, res) => {
  try {
    await TermService.deleteTerm(req.params.id, req.user.id);
    res.json({ message: "Financing term deleted" });
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
};
