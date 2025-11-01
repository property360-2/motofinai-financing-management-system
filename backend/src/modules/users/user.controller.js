import * as UserService from "./user.service.js";

export const getUsers = async (req, res) => {
  try {
    const users = await UserService.getAll();
    res.json(users);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
};

export const createUser = async (req, res) => {
  try {
    const user = await UserService.createUser(req.body, req.user.id);
    res.status(201).json(user);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
};

export const changeStatus = async (req, res) => {
  try {
    const id = parseInt(req.params.id, 10);
    const { status } = req.body;
    const updated = await UserService.updateStatus(id, status, req.user.id);
    res.json(updated);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
};
