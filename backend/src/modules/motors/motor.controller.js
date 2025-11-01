import * as MotorService from "./motor.service.js";

export const getMotors = async (req, res) => {
  try {
    const data = await MotorService.getAllMotors();
    res.json(data);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
};

export const addMotor = async (req, res) => {
  try {
    const motor = await MotorService.createMotor(req.body, req.user.id);
    res.status(201).json(motor);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
};

export const editMotor = async (req, res) => {
  try {
    const updated = await MotorService.updateMotor(req.params.id, req.body, req.user.id);
    res.json(updated);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
};

export const deleteMotor = async (req, res) => {
  try {
    const archived = await MotorService.archiveMotor(req.params.id, req.user.id);
    res.json({ message: "Motor archived successfully", archived });
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
};
