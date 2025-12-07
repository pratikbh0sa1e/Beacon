#!/bin/bash

# BEACON - SIH Branch Setup Script
# This script creates round-1, round-2, and round-3 branches with proper feature flags

echo "🚀 BEACON - Setting up SIH branches..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}Current branch: ${CURRENT_BRANCH}${NC}"
echo ""

# Ask for confirmation
read -p "This will create round-1, round-2, and round-3 branches. Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Aborted."
    exit 1
fi

# ============================================
# STEP 1: Create Round 1 Branch
# ============================================

echo -e "${YELLOW}Creating round-1 branch...${NC}"

git checkout -b round-1 2>/dev/null || git checkout round-1

# Update feature flag to Round 1
sed -i 's/const CURRENT_ROUND = [0-9];/const CURRENT_ROUND = 1;/' frontend/src/config/featureFlags.js

git add frontend/src/config/featureFlags.js
git commit -m "feat: Round 1 - MVP with core features only (35-40%)" 2>/dev/null || echo "Already committed"

echo -e "${GREEN}✓ Round 1 branch created${NC}"
echo ""

# ============================================
# STEP 2: Create Round 2 Branch
# ============================================

echo -e "${YELLOW}Creating round-2 branch...${NC}"

git checkout -b round-2 2>/dev/null || git checkout round-2

# Update feature flag to Round 2
sed -i 's/const CURRENT_ROUND = [0-9];/const CURRENT_ROUND = 2;/' frontend/src/config/featureFlags.js

git add frontend/src/config/featureFlags.js
git commit -m "feat: Round 2 - Enable workflows, approvals, multilingual (75-80%)" 2>/dev/null || echo "Already committed"

echo -e "${GREEN}✓ Round 2 branch created${NC}"
echo ""

# ============================================
# STEP 3: Create Round 3 Branch
# ============================================

echo -e "${YELLOW}Creating round-3 branch...${NC}"

git checkout -b round-3 2>/dev/null || git checkout round-3

# Update feature flag to Round 3
sed -i 's/const CURRENT_ROUND = [0-9];/const CURRENT_ROUND = 3;/' frontend/src/config/featureFlags.js

git add frontend/src/config/featureFlags.js
git commit -m "feat: Round 3 - Production ready with all features (95-100%)" 2>/dev/null || echo "Already committed"

echo -e "${GREEN}✓ Round 3 branch created${NC}"
echo ""

# ============================================
# Summary
# ============================================

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ All branches created successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Available branches:"
git branch
echo ""
echo -e "${BLUE}Usage:${NC}"
echo "  Round 1 Demo: git checkout round-1"
echo "  Round 2 Demo: git checkout round-2"
echo "  Round 3 Demo: git checkout round-3"
echo ""
echo -e "${YELLOW}Note: Backend is identical across all branches${NC}"
echo -e "${YELLOW}      Only frontend feature flags change${NC}"
echo ""
echo "Read GIT_BRANCH_STRATEGY.txt for detailed instructions"
echo ""

# Return to original branch
git checkout $CURRENT_BRANCH
echo -e "${BLUE}Returned to original branch: ${CURRENT_BRANCH}${NC}"
