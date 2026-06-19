#!/bin/bash

# Auto-release script: commit, push, check pipeline, and bump version

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Auto Release Workflow ===${NC}"

# Check if there are any changes to commit
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo -e "${YELLOW}There are uncommitted changes. Please commit or stash them first.${NC}"
    exit 1
fi

# Get current version from git tag
CURRENT_VERSION=$(git tag --sort=-v:refname | head -1 | sed 's/^v//')
if [ -z "$CURRENT_VERSION" ]; then
    CURRENT_VERSION="1.0.0"
fi

echo -e "${BLUE}Current version: v${CURRENT_VERSION}${NC}"

# Ask for version bump type
echo -e "${YELLOW}Select version bump type:${NC}"
echo "1) Patch (bug fixes) - e.g., 1.0.0 -> 1.0.1"
echo "2) Minor (new features) - e.g., 1.0.0 -> 1.1.0"
echo "3) Major (breaking changes) - e.g., 1.0.0 -> 2.0.0"
echo "4) Custom version"

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        NEW_VERSION=$(python3 -c "import re; v=re.split('[.-]', '$CURRENT_VERSION'); v[2]=str(int(v[2])+1); print('.'.join(v[:3]))")
        ;;
    2)
        NEW_VERSION=$(python3 -c "import re; v=re.split('[.-]', '$CURRENT_VERSION'); v[1]=str(int(v[1])+1); v[2]='0'; print('.'.join(v[:3]))")
        ;;
    3)
        NEW_VERSION=$(python3 -c "import re; v=re.split('[.-]', '$CURRENT_VERSION'); v[0]=str(int(v[0])+1); v[1]='0'; v[2]='0'; print('.'.join(v[:3]))")
        ;;
    4)
        read -p "Enter new version (e.g., 2.0.0): " NEW_VERSION
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}Bumping version from ${CURRENT_VERSION} to ${NEW_VERSION}${NC}"

# Create git tag
TAG_NAME="v${NEW_VERSION}"
echo -e "${BLUE}Creating git tag: ${TAG_NAME}${NC}"
git tag -a "${TAG_NAME}" -m "Release version ${NEW_VERSION}"

# Push tag
echo -e "${BLUE}Pushing tag to remote...${NC}"
git push origin "${TAG_NAME}"

echo -e "${GREEN}Tag pushed successfully!${NC}"

# Check CI pipeline status
echo -e "${BLUE}Checking CI pipeline status...${NC}"
sleep 10  # Give GitHub some time to start the workflow

WORKFLOW_RUN_ID=$(gh api repos/mshegolev/graphql-mcp/actions/workflows/ci.yml/runs --jq '.workflow_runs[0].id' 2>/dev/null)

if [ -n "$WORKFLOW_RUN_ID" ]; then
    echo -e "${BLUE}Latest CI workflow run ID: ${WORKFLOW_RUN_ID}${NC}"
    echo -e "${BLUE}Monitoring pipeline status...${NC}"
    
    # Monitor the workflow for up to 30 minutes
    for i in {1..180}; do
        STATUS=$(gh api repos/mshegolev/graphql-mcp/actions/runs/${WORKFLOW_RUN_ID} --jq '.status,.conclusion' 2>/dev/null | tr '\n' ' ')
        RUNNING_STATUS=$(echo $STATUS | awk '{print $1}')
        CONCLUSION_STATUS=$(echo $STATUS | awk '{print $2}')
        
        if [ "$RUNNING_STATUS" = "completed" ]; then
            if [ "$CONCLUSION_STATUS" = "success" ]; then
                echo -e "${GREEN}✅ CI Pipeline completed successfully!${NC}"
                break
            else
                echo -e "${RED}❌ CI Pipeline failed with conclusion: ${CONCLUSION_STATUS}${NC}"
                echo -e "${YELLOW}Check the workflow at: https://github.com/mshegolev/graphql-mcp/actions/runs/${WORKFLOW_RUN_ID}${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}⏳ Pipeline still running... (attempt $i/180)${NC}"
            sleep 10
        fi
        
        if [ $i -eq 180 ]; then
            echo -e "${RED}⏰ Pipeline check timed out after 30 minutes${NC}"
            exit 1
        fi
    done
else
    echo -e "${YELLOW}Could not retrieve workflow run ID. Please check manually.${NC}"
fi

# Check if there's a publish workflow that should run
PUBLISH_WORKFLOW_RUN_ID=$(gh api repos/mshegolev/graphql-mcp/actions/workflows/publish.yml/runs --jq '.workflow_runs[0].id' 2>/dev/null)

if [ -n "$PUBLISH_WORKFLOW_RUN_ID" ]; then
    echo -e "${BLUE}Publish workflow detected. Monitoring...${NC}"
    
    # Monitor the publish workflow for up to 30 minutes
    for i in {1..180}; do
        STATUS=$(gh api repos/mshegolev/graphql-mcp/actions/runs/${PUBLISH_WORKFLOW_RUN_ID} --jq '.status,.conclusion' 2>/dev/null | tr '\n' ' ')
        RUNNING_STATUS=$(echo $STATUS | awk '{print $1}')
        CONCLUSION_STATUS=$(echo $STATUS | awk '{print $2}')
        
        if [ "$RUNNING_STATUS" = "completed" ]; then
            if [ "$CONCLUSION_STATUS" = "success" ]; then
                echo -e "${GREEN}✅ Publish Pipeline completed successfully!${NC}"
                echo -e "${GREEN}🎉 Version ${NEW_VERSION} has been published to PyPI!${NC}"
                break
            else
                echo -e "${RED}❌ Publish Pipeline failed with conclusion: ${CONCLUSION_STATUS}${NC}"
                echo -e "${YELLOW}Check the workflow at: https://github.com/mshegolev/graphql-mcp/actions/runs/${PUBLISH_WORKFLOW_RUN_ID}${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}⏳ Publish Pipeline still running... (attempt $i/180)${NC}"
            sleep 10
        fi
        
        if [ $i -eq 180 ]; then
            echo -e "${RED}⏰ Publish Pipeline check timed out after 30 minutes${NC}"
            exit 1
        fi
    done
else
    echo -e "${YELLOW}No publish workflow detected. Package will be published when tag is pushed.${NC}"
fi

echo -e "${GREEN}=== Release Workflow Completed Successfully ===${NC}"
echo -e "${GREEN}Version ${NEW_VERSION} released and published!${NC}"