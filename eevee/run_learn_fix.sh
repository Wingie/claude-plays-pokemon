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

# Function to generate comprehensive analysis prompt for Claude Code
generate_analysis_prompt() {
    log "${PURPLE}📝 Generating comprehensive analysis prompt...${NC}"
    
    local prompt_file="analysis_prompt.txt"
    local most_recent_session=$(ls -1dt runs/session_* 2>/dev/null | head -1)
    
    cat > "$prompt_file" << 'EOF'
# AI Pokemon Learning System Analysis

Please analyze the recent AI Pokemon learning sessions and provide insights on the template selection system, learning effectiveness, and recommendations for improvements.

## Context
This is an AI-powered Pokemon gameplay system that uses:
- **Pure AI-driven template selection** (no keyword detection)
- **Visual analysis** to choose between battle_analysis, exploration_strategy, stuck_recovery
- **Real-time learning** with periodic template improvements
- **Gemini 2.0 Flash** for template enhancement

## Key Focus Areas
1. **Template Selection Accuracy**: Is AI correctly choosing templates based on visual context?
2. **Learning System Effectiveness**: Are template improvements actually working?
3. **Stuck Pattern Recovery**: How well does the system handle repetitive actions?
4. **Performance Trends**: Are metrics improving over time?

## Recent Session Data
EOF

    # Add recent session data if available
    if [ -n "$most_recent_session" ] && [ -f "$most_recent_session/session_data.json" ]; then
        echo "" >> "$prompt_file"
        echo "### Most Recent Session: $most_recent_session" >> "$prompt_file"
        echo "\`\`\`json" >> "$prompt_file"
        cat "$most_recent_session/session_data.json" >> "$prompt_file"
        echo "\`\`\`" >> "$prompt_file"
    fi
    
    # Add periodic reviews if available
    local periodic_reviews=$(find runs/session_* -name "periodic_review_turn_*.md" 2>/dev/null | head -3)
    if [ -n "$periodic_reviews" ]; then
        echo "" >> "$prompt_file"
        echo "### Recent AI Analysis & Improvements" >> "$prompt_file"
        for review in $periodic_reviews; do
            echo "" >> "$prompt_file"
            echo "#### $(basename "$review")" >> "$prompt_file"
            echo "\`\`\`markdown" >> "$prompt_file"
            cat "$review" >> "$prompt_file"
            echo "\`\`\`" >> "$prompt_file"
        done
    fi
    
    # Add template change logs if available
    local change_logs=$(find runs/prompt_changes/ -name "change_*.json" 2>/dev/null | head -5)
    if [ -n "$change_logs" ]; then
        echo "" >> "$prompt_file"
        echo "### Template Changes Applied" >> "$prompt_file"
        for change_log in $change_logs; do
            echo "" >> "$prompt_file"
            echo "#### $(basename "$change_log")" >> "$prompt_file"
            echo "\`\`\`json" >> "$prompt_file"
            cat "$change_log" >> "$prompt_file"
            echo "\`\`\`" >> "$prompt_file"
        done
    fi
    
    # Add current template versions
    if [ -f "prompts/base/base_prompts.yaml" ]; then
        echo "" >> "$prompt_file"
        echo "### Current Template Versions" >> "$prompt_file"
        echo "\`\`\`yaml" >> "$prompt_file"
        grep -A 5 -B 5 "version:" "prompts/base/base_prompts.yaml" >> "$prompt_file"
        echo "\`\`\`" >> "$prompt_file"
    fi
    
    # Add learning event logs if available
    local learning_logs=$(find runs/ -name "learning_events_*.log" 2>/dev/null | head -2)
    if [ -n "$learning_logs" ]; then
        echo "" >> "$prompt_file"
        echo "### Learning Events History" >> "$prompt_file"
        for log_file in $learning_logs; do
            echo "" >> "$prompt_file"
            echo "#### $(basename "$log_file")" >> "$prompt_file"
            echo "\`\`\`" >> "$prompt_file"
            cat "$log_file" >> "$prompt_file"
            echo "\`\`\`" >> "$prompt_file"
        done
    fi
    
    # Add analysis questions
    cat >> "$prompt_file" << 'EOF'

## Analysis Questions
1. **Template Selection**: Is the AI correctly identifying battle vs exploration contexts?
2. **Learning Effectiveness**: Are template improvements actually fixing identified issues?
3. **Stuck Pattern Handling**: How well does the recovery system work?
4. **Performance Metrics**: Are navigation efficiency and battle win rates improving?
5. **System Architecture**: Any improvements to the learning or template system?

## Expected Output
Please provide:
1. **Executive Summary**: Overall system performance and key insights
2. **Template Analysis**: Accuracy of AI template selection
3. **Learning Assessment**: Effectiveness of the improvement system
4. **Recommendations**: Specific improvements to implement
5. **Updated Specifications**: Any architecture changes needed

Focus on actionable insights and concrete recommendations for improving the AI Pokemon learning system.
EOF

    echo "  📄 Analysis prompt generated: $prompt_file"
    echo "  📊 Included session data, reviews, and template changes"
    echo ""
}

# Function to invoke Claude Code with comprehensive context
invoke_claude_code() {
    log "${PURPLE}🚀 Invoking Claude Code for analysis...${NC}"
    
    local prompt_file="analysis_prompt.txt"
    local project_dir="/Users/wingston/code/claude-plays-pokemon/eevee"
    
    if [ ! -f "$prompt_file" ]; then
        echo -e "${RED}❌ Analysis prompt file not found: $prompt_file${NC}"
        return 1
    fi
    
    echo "  📂 Project directory: $project_dir"
    echo "  📝 Prompt file: $prompt_file"
    echo "  🤖 Model: claude-sonnet-4"
    echo ""
    
    # Launch Claude Code with context
    claude-code \
        --prompt-file "$prompt_file" \
        --directory "$project_dir" \
        --model claude-sonnet-4 \
        --verbose
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log "${GREEN}✅ Claude Code analysis completed successfully${NC}"
        
        # Clean up prompt file
        rm -f "$prompt_file"
        echo "  🧹 Cleaned up temporary prompt file"
    else
        log "${RED}❌ Claude Code analysis failed (exit code: $exit_code)${NC}"
        echo "  📄 Prompt file preserved for manual review: $prompt_file"
    fi
    
    echo ""
    return $exit_code
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
    
    # Generate comprehensive analysis prompt and invoke Claude Code
    generate_analysis_prompt
    invoke_claude_code
    
    log "${GREEN}🎉 Learning automation completed!${NC}"
    echo ""
    echo "📂 Check the runs/ directory for detailed session data"
    echo "📊 Review periodic_review_turn_*.md files for AI analysis"
    echo "📝 Check prompts/base/base_prompts.yaml for template updates"
    echo ""
}

# Run main function
main "$@"