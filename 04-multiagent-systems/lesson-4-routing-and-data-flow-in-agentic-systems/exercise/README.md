# Chinese Bank Post Office - Routing Exercise

**Learning Goal**: Implement content-based routing and priority-based routing in a multi-agent system.

## Project Structure

```
exercise/
├── main.py                              # Main entry point with test cases
├── config.py                            # LLM configuration
├── data/
│   └── booking_manager.py               # Booking and customer data management
└── agents/
    ├── urgency_detector/
    │   └── tools.py                     # UrgencyDetector agent + analyze_urgency tool
    ├── request_analyzer/
    │   └── tools.py                     # RequestAnalyzer agent + analyze_request tool
    ├── service_router/
    │   └── tools.py                     # ServiceRouter agent + handle_* tools
    └── orchestrator/
        └── orchestrator.py              # Main orchestrator agent
```

## Key Concepts

### Two-Tiered Routing System:

1. **Content-Based Routing**
   - Analyzes the content of customer requests
   - Detects urgency through keyword matching
   - Classifies service type from request text

2. **Priority-Based Routing**
   - Handles urgent requests with priority
   - Uses urgency flag to affect processing
   - Ensures time-sensitive requests are marked appropriately

### Agent Flow:

```
Customer Request
    ↓
[UrgencyDetector] → Detect urgency (content-based)
    ↓
[RequestAnalyzer] → Classify service type
    ↓
[ServiceRouter] → Route to handler with urgency flag
    ↓
BookingManager → Process with priority (if urgent)
```

## How It Works

1. **Urgency Detection**: Scans request for urgency keywords
2. **Service Classification**: Identifies what service is needed
3. **Priority Routing**: Passes urgency flag to service handlers
4. **Special Handling**: Tracks urgent requests and applies priority indicators

## Running the System

```bash
python main.py
```

The demo will:
- Process test requests in order
- Demonstrate urgency detection
- Show priority handling for urgent requests
- Display final state and metrics

