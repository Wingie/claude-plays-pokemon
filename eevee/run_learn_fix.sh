#!/bin/bash

# AI Template Learning Automation Script
# Runs learning cycles and invokes Claude Code for analysis

echo "🤖 AI TEMPLATE LEARNING AUTOMATION"
echo "=================================="
echo ""

# Configuration
GOAL="walk around and win pokemon battles"
REVIEW_FREQ=4
PYTHON_CMD="python"
EEVEE_DIR="/Users/wingston/code/claude-plays-pokemon/eevee"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to log with timestamp
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

# Function to run learning session
run_learning_session() {
    local turns=$1
    local session_name=$2
    
    log "${YELLOW}Starting $session_name (${turns} turns)...${NC}"
    echo ""
    
    cd "$EEVEE_DIR" || {
        echo -e "${RED}Error: Could not cd to $EEVEE_DIR${NC}"
        exit 1
    }
    
    # Run the learning session
    $PYTHON_CMD run_eevee.py \
        --goal "$GOAL" \
        --episode-review-frequency $REVIEW_FREQ \
        --max-turns $turns \
        --no-interactive \
        --verbose
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log "${GREEN}✅ $session_name completed successfully${NC}"
    else
        log "${RED}❌ $session_name failed (exit code: $exit_code)${NC}"
    fi
    
    echo ""
    return $exit_code
}

# Function to show session analysis
analyze_sessions() {
    log "${PURPLE}📊 Analyzing recent sessions...${NC}"
    
    # Find the 3 most recent session directories
    recent_sessions=$(ls -1dt runs/session_* 2>/dev/null | head -3)
    
    if [ -z "$recent_sessions" ]; then
        echo "No recent sessions found"
        return
    fi
    
    echo ""
    echo "Recent Sessions:"
    for session in $recent_sessions; do
        if [ -f "$session/session_data.json" ]; then
            turns=$(jq -r '.turns | length' "$session/session_data.json" 2>/dev/null || echo "?")
            echo "  📁 $session ($turns turns)"
            
            # Check for episode review
            if [ -f "$session/episode_review.md" ]; then
                echo "    📋 Episode review available"
            fi
            
            # Check for periodic reviews
            periodic_reviews=$(ls "$session"/periodic_review_turn_* 2>/dev/null | wc -l)
            if [ "$periodic_reviews" -gt 0 ]; then
                echo "    🔄 $periodic_reviews periodic reviews"
            fi
        fi
    done
    echo ""
}

# Function to check template updates
check_template_updates() {
    log "${PURPLE}🔍 Checking for template updates...${NC}"
    
    # Check if YAML files have recent modifications
    template_file="prompts/base/base_prompts.yaml"
    if [ -f "$template_file" ]; then
        # Get modification time
        mod_time=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$template_file" 2>/dev/null || stat -c "%y" "$template_file" 2>/dev/null)
        echo "  📝 Template file: $template_file"
        echo "  🕒 Last modified: $mod_time"
        
        # Check for version numbers in the file
        versions=$(grep -o 'version: [0-9.]*' "$template_file" 2>/dev/null | head -3)
        if [ -n "$versions" ]; then
            echo "  📊 Template versions:"
            echo "$versions" | sed 's/^/    /'
        fi
    else
        echo "  ❌ Template file not found: $template_file"
    fi
    echo ""
}

# Main execution
main() {
    log "${GREEN}🚀 Starting AI Template Learning Automation${NC}"
    echo ""
    
    # Session 1: Quick 4-turn learning cycle
    if ! run_learning_session 4 "Session 1 (Quick Learning)"; then
        echo -e "${RED}First session failed, continuing...${NC}"
    fi
    
    # Brief pause between sessions
    log "⏳ Waiting 5 seconds before next session..."
    sleep 5
    
    # Session 2: Extended 12-turn learning cycle  
    if ! run_learning_session 12 "Session 2 (Extended Learning)"; then
        echo -e "${RED}Second session failed, continuing with analysis...${NC}"
    fi
    
    # Analysis
    analyze_sessions
    check_template_updates
    
    # Skip Claude Code launch - manual analysis instead
    log "${PURPLE}📊 Analysis Summary${NC}"
    echo ""
    echo "Recent learning sessions completed - ready for manual analysis!"
    echo ""
    echo "Key insights to review:"
    echo "• Template selection behavior (AI vs fallback)"
    echo "• Stuck pattern analysis and recovery"
    echo "• Template improvement opportunities"
    echo ""
    
    log "${GREEN}🎉 Learning automation completed!${NC}"
    echo ""
    echo "📂 Check the runs/ directory for detailed session data"
    echo "📊 Review periodic_review_turn_*.md files for AI analysis"
    echo "📝 Check prompts/base/base_prompts.yaml for template updates"
    echo ""
}

# Run main function
main "$@"