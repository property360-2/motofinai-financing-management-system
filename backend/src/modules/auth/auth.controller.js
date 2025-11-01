import * as AuthService from "./auth.service.js";

export const register = async (req, res) => {
  try {
    const user = await AuthService.register(req.body, req.user?.id);
    res.status(201).json({ message: "User created", user });
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
};

export const login = async (req, res) => {
  try {
    const { email, password } = req.body;
    const { token, user } = await AuthService.login(email, password);
    res.json({ token, user });
  } catch (err) {
    res.status(401).json({ message: err.message });
  }
};

export const logout = async (req, res) => {
  try {
    await AuthService.logout(req.user.id);
    res.json({ message: "Logged out" });
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
};
