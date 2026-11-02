#!/bin/bash
# RepoPilot Development Setup Script
set -e

echo "🚀 Setting up RepoPilot development environment..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites satisfied${NC}"

# Setup Backend
echo -e "\n${BLUE}Setting up backend...${NC}"
cd "$(dirname "$0")/../backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

source venv/bin/activate
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created from template${NC}"
    echo "⚠️  Please edit backend/.env and add your LLM API key"
fi

# Setup Frontend
echo -e "\n${BLUE}Setting up frontend...${NC}"
cd ../frontend

if [ ! -d "node_modules" ]; then
    npm install --silent
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
fi

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo ""
echo "To start the development servers:"
echo "  Backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "Or use Docker:"
echo "  docker-compose up --build"
