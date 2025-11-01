import * as UserService from "./user.service.js";

export const getUsers = async (req, res) => {
  const users = await UserService.getAll();
  res.json(users);
};

export const changeStatus = async (req, res) => {
  const { id } = req.params;
  const { status } = req.body;
  const updated = await UserService.updateStatus(parseInt(id), status);
  res.json(updated);
};
