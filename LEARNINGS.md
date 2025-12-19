## Learnings

### 2025-12-19 — `run.sh` backend not ready (port already in use)
- **Symptom**: Backend health check never becomes ready; logs show `Address already in use`.
- **Root cause**: A prior `uvicorn`/Python process was already listening on **TCP 8000** (and sometimes the Vite dev server on **5173**).
- **Fix**: Updated `run.sh` to proactively **free ports 8000 and 5173** before starting backend/frontend, so rerunning `./run.sh` replaces any already-running dev instances.
- **Debug tip**: Identify the blocker with `lsof -nP -iTCP:8000 -sTCP:LISTEN` (and similarly for `5173`).

---

## Best Practices

Patterns and practices extracted from this project that can be reused in other projects.

### 1. Database Migration Lifecycle

Integrate Alembic migrations into shell scripts to ensure database schema is always in sync with code.

```bash
# init.sh - Run on first setup
mkdir -p backend/data
cd backend && python -m alembic upgrade head

# run.sh - Check before each run (idempotent)
cd backend
if python3.12 -m alembic upgrade head; then
    echo "✅ Database migrations up to date"
else
    echo "❌ Failed to apply database migrations"
    exit 1
fi

# test.sh - Isolated test database
export DATABASE_URL="sqlite:///backend/data/test.db"
rm -f backend/data/test.db
cd backend && python -m alembic upgrade head
# ... run tests ...
rm -f backend/data/test.db  # cleanup
```

**Benefits:**
- No "it works on my machine" issues
- New team members get correct schema on first setup
- Pulling new code with migrations automatically applies them

---

### 2. Repository Pattern for Data Access

Encapsulate all database operations in repository classes for clean separation of concerns.

```python
class EntityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def query(
        self,
        region_id: int | None = None,
        year: int | None = None,
        limit: int | None = None,
    ) -> list[Entity]:
        """Query with flexible filters."""
        query = self.session.query(Entity)
        if region_id:
            query = query.filter(Entity.region_id == region_id)
        if year:
            query = query.filter(Entity.year == year)
        if limit:
            query = query.limit(limit)
        return query.all()

    def bulk_insert(self, records: list[dict], ...) -> int:
        """Bulk insert normalized records."""
        ...

    def get_statistics(self, ...) -> dict[str, Any]:
        """Aggregate statistics for dashboards."""
        ...

    def delete_by_source(self, source_id: int) -> int:
        """Delete all records from a specific source."""
        ...
```

**Benefits:**
- Business logic stays clean (no SQL in API handlers)
- Easy to test with mock repositories
- Swap databases without changing application code

---

### 3. Data Normalizer Pattern

Create dedicated normalizer classes to handle messy external data formats.

```python
class DataNormalizer:
    """Normalize external data into standardized structure."""

    def normalize_record(
        self,
        record: dict[str, Any],
        field_mapping: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        """
        Normalize a single record.
        Returns None if record is invalid.
        """
        ...

    def normalize_batch(
        self,
        records: list[dict[str, Any]],
        field_mapping: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Normalize multiple records, filtering out invalid ones."""
        return [
            n for r in records
            if (n := self.normalize_record(r, field_mapping)) is not None
        ]
```

**Benefits:**
- Single place to fix parsing bugs
- Handles variations in source data (different field names, formats)
- Reusable across multiple data sources

---

### 4. Tabbed UI with Shared State

Lift shared state to the parent component so it persists across tab switches.

```jsx
function App() {
  // Shared state - persists across tabs
  const [selectedRegion, setSelectedRegion] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("demographics");

  return (
    <div className="app">
      <header>
        <h1>App Title</h1>
      </header>

      {/* Tab Navigation */}
      <nav className="tab-nav">
        <button
          className={`tab-button ${activeTab === "demographics" ? "active" : ""}`}
          onClick={() => setActiveTab("demographics")}
        >
          Demographics
        </button>
        <button
          className={`tab-button ${activeTab === "industry" ? "active" : ""}`}
          onClick={() => setActiveTab("industry")}
        >
          Industry
        </button>
      </nav>

      {/* Tab Content - pass shared state as props */}
      {activeTab === "demographics" ? (
        <DemographicsTab
          selectedRegion={selectedRegion}
          setSelectedRegion={setSelectedRegion}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />
      ) : (
        <IndustryTab
          selectedRegion={selectedRegion}
          setSelectedRegion={setSelectedRegion}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />
      )}
    </div>
  );
}
```

**Benefits:**
- Region selection persists when switching tabs
- Centralized state management
- Each tab component stays focused on its own data fetching

---

### 5. Shell Script Port Management

Proactively free ports before starting dev servers to prevent "address already in use" errors.

```bash
ensure_port_free() {
    local port=$1
    local service_name=$2

    if ! command -v lsof >/dev/null 2>&1; then
        return 0  # Skip if lsof not available
    fi

    local pids
    pids=$(lsof -t -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)

    if [ -n "$pids" ]; then
        echo "⚠️  Port $port in use. Stopping existing $service_name..."
        kill $pids 2>/dev/null || true
        sleep 1
        # Force kill if still running
        pids=$(lsof -t -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
        if [ -n "$pids" ]; then
            kill -9 $pids 2>/dev/null || true
        fi
    fi
}

# Usage
ensure_port_free 8000 "backend"
ensure_port_free 5173 "frontend"
```

**Benefits:**
- `./run.sh` always works, even if previous run crashed
- No manual port hunting/killing needed
- Graceful shutdown attempted before force kill

---

### 6. Dataset Configuration Objects

Use frozen dataclasses to define type-safe, immutable dataset configurations.

```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class DatasetConfig:
    dataset_id: str
    dim_geo: str = "geo"
    dim_time: str = "time"
    dim_sex: str = "sex"
    dim_age: str = "age"
    value_field: str = "value"
    default_params: dict[str, Any] | None = None

# Define datasets
DEMO_PJAN = DatasetConfig(
    dataset_id="demo_pjan",
    default_params={"unit": "NR"},
)

STS_INPR_M = DatasetConfig(
    dataset_id="sts_inpr_m",
    dim_sex="",  # Not applicable
    dim_age="",  # Not applicable
    default_params={"unit": "I15", "s_adj": "SCA"},
)

# Registry for lookup
DATASETS: dict[str, DatasetConfig] = {
    cfg.dataset_id: cfg for cfg in [DEMO_PJAN, STS_INPR_M]
}
```

**Benefits:**
- Type-safe configuration
- Immutable (frozen) prevents accidental modification
- Easy to add new datasets without changing parsing code

---

### 7. Consistent API Response Structure

Use a standard response envelope for all list endpoints.

```python
@app.get("/api/data/entity")
async def query_entity(
    region_code: str | None = None,
    year: int | None = None,
    limit: int = Query(default=1000, le=10000),
) -> dict[str, Any]:
    with get_session() as session:
        repo = EntityRepository(session)
        data = repo.query(region_code=region_code, year=year, limit=limit)

        return {
            "count": len(data),
            "data": [
                {
                    "id": d.id,
                    "region_code": d.region.code if d.region else None,
                    "year": d.year,
                    "value": d.value,
                }
                for d in data
            ],
        }
```

**Benefits:**
- Frontend always knows what to expect (`count` + `data` array)
- Easy to add pagination later (`offset`, `total`, `has_more`)
- Consistent error handling across endpoints

---

### 8. Test Database Isolation

Use a separate database for tests to ensure clean, reproducible test runs.

```bash
# test.sh
if [ "$FRONTEND_ONLY" = false ]; then
    # Use separate test database
    export DATABASE_URL="sqlite:///backend/data/test_demographics.db"

    # Clean state for each run
    rm -f backend/data/test_demographics.db
    mkdir -p backend/data

    # Apply migrations
    cd backend && python -m alembic upgrade head && cd ..
fi

# Run tests...

# Cleanup
rm -f backend/data/test_demographics.db
```

**Benefits:**
- Tests don't pollute development database
- Each test run starts fresh
- CI/CD gets reproducible results

---

### Summary: Project Template Checklist

When starting a new project, include:

- [ ] `init.sh` with migration step after dependency install
- [ ] `run.sh` with migration check + port management
- [ ] `test.sh` with isolated test database
- [ ] Repository classes for each entity type
- [ ] Normalizer classes for external data sources
- [ ] Frozen dataclass configs for datasets
- [ ] Consistent API response envelope
- [ ] Tabbed UI pattern with lifted state
