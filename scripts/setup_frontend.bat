@echo off
REM Sets up the CareerOS frontend on Windows.
cd ..\frontend
npm install
copy .env.example .env
echo Frontend setup complete. Run: npm run dev
