#!/bin/bash

# Detect OS and set PyCharm path
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash / Cygwin)
    PYCHARM_PATH="/c/Users/Derik/AppData/Local/Programs/PyCharm Professional/bin/pycharm64.exe"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    PYCHARM_PATH="/Applications/PyCharm.app/Contents/MacOS/pycharm"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

show_help() {
    echo "Usage: $0 {module|tools|root} [pycharm|code]"
    echo
    echo "Launch a SprigConfig project in the desired IDE."
    echo
    echo "Arguments:"
    echo "  module          Open sprig-config-module"
    echo "  tools           Open sprig-tools"
    echo "  root            Open entire mono-repo"
    echo
    echo "Options:"
    echo "  pycharm         Launch PyCharm (default: VS Code)"
    echo "  code            Launch VS Code (default)"
    echo
    echo "Examples:"
    echo "  $0 module            # Opens module in VS Code"
    echo "  $0 tools pycharm     # Opens tools in PyCharm"
    echo "  $0 root              # Opens root workspace in VS Code"
}

# No arguments = show help
if [[ $# -lt 1 ]]; then
    show_help
    exit 0
fi

PROJECT=$1
IDE_ARG=$2

case "$PROJECT" in
  module)
    PROJECT_PATH="sprig-config-module"
    WORKSPACE_FILE="sprig-config-module.code-workspace"
    ;;
  tools)
    PROJECT_PATH="sprig-tools"
    WORKSPACE_FILE="sprig-tools.code-workspace"
    ;;
  root)
    PROJECT_PATH="."
    WORKSPACE_FILE="sprig-config-root.code-workspace"
    ;;
  -h|--help|help)
    show_help
    exit 0
    ;;
  *)
    echo "❌ Unknown project: $PROJECT"
    show_help
    exit 1
    ;;
esac

# Choose IDE
if [[ "$IDE_ARG" == "pycharm" ]]; then
    IDE="$PYCHARM_PATH"
    TARGET="$PROJECT_PATH"
else
    IDE=${IDE_ARG:-code}
    TARGET="$PROJECT_PATH/$WORKSPACE_FILE"
fi

# Launch IDE
"$IDE" "$TARGET" & disown
