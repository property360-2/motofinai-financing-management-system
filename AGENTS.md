# Repository Guidelines

## Project Structure & Module Organization
MotofinAI is split into `backend/` (Express + Prisma), `frontend/` (React via Vite), and supporting notes in `documentation/`. Backend feature logic lives under `src/modules/<feature>/{*.controller.js, *.service.js, *.routes.js}`, with shared helpers in `src/middlewares/` and `src/utils/`. Database assets reside in `prisma/` (`schema.prisma`, `seed.js`). The frontend keeps UI primitives in `src/components/`, screens in `src/pages/`, routing helpers in `src/routes/`, and shared state inside `src/context/`.

## Build, Test, and Development Commands
- `cd backend && npm install` — install API dependencies (run once per clone).
- `cd backend && npm run dev` — start the REST API with Nodemon; Prisma expects a reachable MySQL `DATABASE_URL`.
- `cd backend && npx prisma migrate dev` and `npm run seed` — apply schema changes and populate baseline data.
- `cd frontend && npm install` then `npm run dev` — launch the React client on Vite’s dev server; keep `.env` values aligned with the backend port.
- `cd frontend && npm run build` or `npm run lint` — produce a production bundle or run the ESLint suite before opening a PR.

## Coding Style & Naming Conventions
Source uses modern ES modules, 2-space indentation, and semicolons. Prefer double quotes for strings, `camelCase` for variables/functions, and `PascalCase` for React components and controller/service classes. Group backend logic by feature inside `src/modules`, keeping request validation in middlewares and data access inside services. Run `npm run lint` (frontend) before commits; mirror that style manually when touching backend files.

## Testing Guidelines
Automated tests are not yet configured. When adding features, include at least a manual test plan in the PR description and, where feasible, add `*.test.js` files under `backend/src/__tests__/` or `frontend/src/__tests__/` using Jest/Vitest-style assertions. Seed predictable fixtures through Prisma so tests can run repeatably against a local MySQL instance.

## Commit & Pull Request Guidelines
History currently uses concise sentence-style summaries (e.g., `initialized the project and added the rbac login`). Keep messages in the imperative mood, under ~72 characters, and include a short body when context matters. Pull requests should link the relevant issue, describe the change, note any schema migrations or seeds, and attach screenshots or API samples when UI or contract changes are involved.

## Configuration & Environment Notes
Copy `backend/.env.example` to `.env`, then provide `DATABASE_URL`, `JWT_SECRET`, and optional `PORT`. Run `npx prisma generate` after updating the schema. The frontend expects the backend at `http://localhost:5000`; if that changes, surface the new base URL via a Vite env (for example, `VITE_API_BASE_URL`). Store secrets outside version control and avoid committing `.env` files or database dumps.
