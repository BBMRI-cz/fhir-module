# Combined FHIR Module and UI Setup

This setup combines both the FHIR module (Python Flask) and the UI (Next.js) into a single container for simplified deployment.

## Files Created/Modified

- `Dockerfile.combined` - Multi-stage Dockerfile that builds both services
- `compose.yaml` - Updated to use the new combined service
- `test-combined.ps1` - PowerShell test script for Windows
- `test-combined.sh` - Bash test script for Linux/Mac

## How It Works

The combined container runs both services simultaneously:

1. **FHIR Module**: Runs on port 5000 (exposed as 5001)
2. **UI**: Runs on port 3000

Both services are started by a simple bash script that runs them in the background and waits for both processes.

## Usage

### Combined Service (New)

```bash
# Combined FHIR module and UI
docker-compose --profile combined up fhir-combined

# Combined service with debug support
docker-compose --profile combined-debug up fhir-combined-debug
```

### Original Separate Services (Still Available)

```bash
# Development (separate containers)
docker-compose --profile dev up fhir-module

# Production (separate containers)
docker-compose --profile prod up fhir-module

# UI only
docker-compose --profile ui up fhir-ui

# Debug mode (separate containers)
docker-compose --profile debug up fhir-module-debug
```

## Testing

Run the test script to verify both services are working:

**Windows:**

```powershell
.\test-combined.ps1
```

**Linux/Mac:**

```bash
./test-combined.sh
```

## Access Points

- **FHIR Module**: http://localhost:5001
- **UI**: http://localhost:3000

## Benefits

- Single container to manage
- Simplified deployment
- No need for service orchestration between containers
- Shared networking and volumes
- Easier to scale as a unit

## Notes

- The container uses a simple process management approach (no supervisor)
- Both services run in the background and the container waits for both
- Signal handling ensures proper shutdown of both services
- All original functionality is preserved
