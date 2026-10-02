"""Re-export meeting_intelligence package under app namespace for convenience."""

import sys

import meeting_intelligence

# Mirror all modules
sys.modules["app"] = meeting_intelligence
