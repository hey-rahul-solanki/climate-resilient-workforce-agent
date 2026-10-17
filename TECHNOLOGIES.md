# Technologies and Dependencies

## Overview

This document lists all technologies, APIs, libraries, and tools used in the Climate-Resilient Workforce Agent project.

---

## Backend Technologies

### Core Framework
- **Python** 3.11+
  - Primary programming language
  - Version: 3.11 or higher
  - Purpose: Backend logic and API

- **FastAPI**
  - Web framework for building APIs
  - Version: Latest
  - Purpose: REST API endpoints
  - Features: Async support, automatic docs, validation

- **Uvicorn**
  - ASGI server
  - Version: Latest
  - Purpose: Running FastAPI application
  - Command: `uvicorn workforce_agent.api:app`

### Data Validation
- **Pydantic** v2
  - Data validation using Python type annotations
  - Version: 2.x
  - Purpose: Request/response validation, settings management

- **Pydantic Settings**
  - Environment variable management
  - Version: Latest
  - Purpose: Configuration from .env files

### Database
- **PostgreSQL** 16
  - Relational database
  - Version: 16 Alpine (Docker)
  - Purpose: Data persistence
  - Features: UUID PKs, JSONB, soft deletes, UTC timestamps

- **pgAdmin 4**
  - Database management tool
  - Version: Latest
  - Purpose: Database administration GUI
  - Docker: dpage/pgadmin4

- **asyncpg** / **psycopg3**
  - PostgreSQL async driver
  - Version: Latest
  - Purpose: Database connectivity

- **SQLAlchemy** 2.0 / **SQLModel**
  - ORM and database toolkit
  - Version: Latest
  - Purpose: Database models and queries

### Security
- **PyJWT** / **python-jose**
  - JWT token handling
  - Version: Latest
  - Purpose: Authentication tokens

- **Passlib** / **bcrypt**
  - Password hashing
  - Version: Latest
  - Purpose: Secure password storage
  - Algorithm: bcrypt (cost factor 12)

- **cryptography**
  - Cryptographic primitives
  - Version: Latest
  - Purpose: Security operations

### HTTP Client
- **HTTPX**
  - Async HTTP client
  - Version: 0.27+
  - Purpose: External API calls (weather, location)

---

## Frontend Technologies

### Core Framework
- **React** 19
  - UI library
  - Version: 19.x
  - Purpose: User interface

- **TypeScript**
  - Typed JavaScript
  - Version: Latest
  - Purpose: Type safety

- **Vite**
  - Build tool and dev server
  - Version: Latest
  - Purpose: Fast development and production builds

### UI Components
- **Material UI (MUI)** v5/v6
  - React component library
  - Version: Latest
  - Purpose: Pre-built UI components
  - Note: Optional - simple HTML/CSS can be used instead

- **Leaflet**
  - Open-source JavaScript library for mobile-friendly interactive maps
  - Version: Latest
  - Purpose: Map display (optional)
  - Note: Only used in dynamic mode with OSM

### Styling
- **CSS**
  - Cascading Style Sheets
  - Purpose: Styling
  - Note: Simple CSS for static mode

- **Emotion**
  - CSS-in-JS library
  - Version: Latest
  - Purpose: Styling with MUI (optional)

### HTTP Client
- **Axios** / **Fetch**
  - HTTP client for browser
  - Version: Latest
  - Purpose: API calls from frontend

---

## External APIs (Dynamic Mode Only)

### Weather APIs

#### Open-Meteo (Free, No API Key Required)
- **URL**: https://api.open-meteo.com/v1/forecast
- **Type**: Free weather API
- **Features**:
  - Hourly forecasts
  - Temperature, precipitation, wind, humidity
  - No API key required
  - Rate limited but generous
- **Usage**: Primary weather source for dynamic mode
- **Documentation**: https://open-meteo.com/

#### Meteor (Optional)
- **URL**: https://api.meteor.com
- **Type**: Commercial weather API
- **Features**:
  - Advanced weather data
  - Historical data
  - Custom alerts
- **Usage**: Alternative weather source
- **Requirement**: API key required
- **Environment Variable**: `WORKFORCE_METEOR_API_KEY`

### Location Services

#### OpenStreetMap Nominatim (Free, No API Key Required)
- **URL**: https://nominatim.openstreetmap.org
- **Type**: Free geocoding service
- **Features**:
  - Address to coordinates (geocoding)
  - Coordinates to address (reverse geocoding)
  - No API key required
  - Rate limited (1 request/second)
- **Usage**: Location intelligence in dynamic mode
- **Documentation**: https://nominatim.openstreetmap.org/
- **Rate Limit**: 1 request per second
- **Environment Variable**: `WORKFORCE_OSM_RATE_LIMIT`

### AI Services

#### Google Gemini (Optional)
- **URL**: https://ai.google.dev/
- **Type**: AI language model
- **Features**:
  - Natural language understanding
  - Smart suggestions
  - Context-aware responses
- **Usage**: AI-powered scheduling suggestions
- **Requirement**: API key required
- **Environment Variable**: `WORKFORCE_GEMINI_API_KEY`
- **Documentation**: https://ai.google.dev/docs

---

## Cloud Services (Dynamic Mode Only)

### Google Cloud Platform (GCP)

#### Cloud Run
- **Type**: Serverless compute platform
- **Purpose**: Hosting FastAPI backend
- **Features**:
  - Auto-scaling
  - Managed infrastructure
  - Pay-per-use
- **Environment Variables**:
  - `WORKFORCE_GCP_PROJECT_ID`
  - `WORKFORCE_GCP_LOCATION`

#### Vertex AI
- **Type**: AI platform
- **Purpose**: AI model hosting and inference
- **Features**:
  - Model deployment
  - Session/memory support
  - Model safety controls
- **Usage**: Advanced AI features (optional)

#### Cloud Storage
- **Type**: Object storage
- **Purpose**: File storage (attachments, images)
- **Features**:
  - Scalable storage
  - CDN integration
- **Usage**: Storing user attachments, profile pictures

---

## Development Tools

### Package Managers
- **pip**
  - Python package manager
  - Purpose: Installing Python dependencies

- **uv** (Optional)
  - Fast Python package installer
  - Purpose: Faster dependency installation
  - Command: `uv pip install`

- **npm**
  - Node.js package manager
  - Purpose: Installing frontend dependencies

### Version Control
- **Git**
  - Version control system
  - Purpose: Code versioning

- **GitHub**
  - Git hosting service
  - Purpose: Remote repository, CI/CD

### Code Quality
- **pytest**
  - Python testing framework
  - Purpose: Unit and integration tests

- **ESLint**
  - JavaScript/TypeScript linter
  - Purpose: Code quality checks

- **Prettier**
  - Code formatter
  - Purpose: Consistent code formatting

### IDE/Editor
- **VS Code** / **Windsurf**
  - Code editor
  - Purpose: Development environment

---

## Containerization

### Docker
- **Docker**
  - Container platform
  - Version: Latest
  - Purpose: Containerizing applications

- **Docker Compose**
  - Multi-container orchestration
  - Version: Latest
  - Purpose: Running development and production stacks

### Docker Images Used
- `postgres:16-alpine` - PostgreSQL database
- `dpage/pgadmin4:latest` - pgAdmin web interface
- Custom images:
  - `workforce-backend` - FastAPI backend
  - `workforce-frontend` - React frontend

---

## Static Data (Static Mode)

### Fixture Files
- **weather.json**
  - Location: `data/fixtures/weather.json`
  - Purpose: Pre-configured weather data
  - Content: Hourly weather for demo sites

- **locations.json**
  - Location: `data/fixtures/locations.json`
  - Purpose: Pre-configured site locations
  - Content: Site coordinates and metadata

### Data Sources
- **Vadodara, Gujarat, India**
  - Coordinates: 22.3072, 73.1812
  - Timezone: Asia/Kolkata
  - Demo site: VAD-PLANT-01

- **Mumbai, Maharashtra, India**
  - Coordinates: 19.0760, 72.8777
  - Timezone: Asia/Kolkata
  - Demo site: MUM-SITE-01

---

## Testing Tools

### Backend Testing
- **pytest**
  - Python testing framework
  - Purpose: Unit tests, integration tests

- **respx**
  - HTTP mocking library
  - Purpose: Mocking external API calls

- **pytest-asyncio**
  - Async test support
  - Purpose: Testing async functions

### Frontend Testing
- **Vitest** (Optional)
  - Unit test framework
  - Purpose: Frontend unit tests

- **Testing Library** (Optional)
  - React testing utilities
  - Purpose: Component testing

---

## Deployment Tools

### CI/CD
- **GitHub Actions**
  - CI/CD platform
  - Purpose: Automated testing and deployment

### Build Tools
- **Vite**
  - Frontend build tool
  - Purpose: Production builds

- **Python setuptools**
  - Python packaging
  - Purpose: Building Python packages

---

## Documentation Tools

### Markdown
- **Markdown**
  - Markup language
  - Purpose: Documentation files

### API Documentation
- **Swagger/OpenAPI**
  - API specification
  - Purpose: Auto-generated API docs
  - URL: /docs (FastAPI)
  - URL: /redoc (FastAPI)

---

## Monitoring & Observability

### Health Checks
- **FastAPI /health endpoint**
  - Purpose: Liveness probe
  - Response: Status and version

- **FastAPI /ready endpoint**
  - Purpose: Readiness probe
  - Response: Database and dependency status

### Logging
- **Python logging**
  - Purpose: Application logging
  - Level: INFO, WARNING, ERROR

---

## Security Standards

### Authentication
- **JWT (JSON Web Tokens)**
  - Algorithm: HS256
  - Token type: Access + Refresh
  - Access token expiry: 15-60 minutes
  - Refresh token expiry: 7-30 days

### Password Security
- **bcrypt**
  - Algorithm: bcrypt
  - Cost factor: 12
  - Purpose: Password hashing

### HTTPS/TLS
- **SSL/TLS**
  - Purpose: Encrypted communication
  - Required for production

---

## Browser Compatibility

### Supported Browsers
- **Chrome** (Latest)
- **Firefox** (Latest)
- **Safari** (Latest)
- **Edge** (Latest)

### Mobile Support
- **iOS Safari** (Latest)
- **Chrome Mobile** (Latest)
- **Responsive Design**: Yes

---

## Licensing

### Open Source Licenses
- **Python**: Python Software Foundation License
- **FastAPI**: MIT License
- **React**: MIT License
- **PostgreSQL**: PostgreSQL License
- **Material UI**: MIT License
- **Leaflet**: BSD 2-Clause

### API Terms of Service
- **Open-Meteo**: Free for non-commercial use
- **OpenStreetMap**: ODbL (Open Database License)
- **Google Gemini**: Google AI Terms of Service

---

## Dependencies Summary

### Python Dependencies (pyproject.toml)
```
- fastapi
- uvicorn
- pydantic
- pydantic-settings
- httpx
- asyncpg
- sqlalchemy
- pyjwt
- passlib
- pytest
- respx
```

### Node.js Dependencies (package.json)
```
- react
- typescript
- vite
- @mui/material
- @mui/icons-material
- axios
- leaflet
```

---

## Environment Variables Summary

### Required for Static Mode
```bash
WORKFORCE_MODE=static
WORKFORCE_WEATHER_SOURCE=fixture
WORKFORCE_FIXTURE_PATH=./data/fixtures/weather.json
WORKFORCE_LOCATION_SOURCE=static
WORKFORCE_AI_SOURCE=rule_based
```

### Optional for Dynamic Mode
```bash
# Weather
WORKFORCE_WEATHER_SOURCE=open-meteo
WORKFORCE_OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1/forecast
WORKFORCE_METEOR_API_KEY=your_key

# Location
WORKFORCE_LOCATION_SOURCE=osm
WORKFORCE_OSM_NOMINATIM_BASE=https://nominatim.openstreetmap.org

# AI
WORKFORCE_AI_SOURCE=gemini
WORKFORCE_GEMINI_API_KEY=your_key

# GCP
WORKFORCE_GCP_PROJECT_ID=your_project_id
WORKFORCE_GCP_LOCATION=us-central1
```

---

## Alternatives Considered

### Weather APIs
- Open-Meteo (Chosen - Free, no key)
- Tomorrow.io (Alternative - Paid)
- AccuWeather (Alternative - Paid)
- WeatherAPI (Alternative - Free tier available)

### Maps
- OpenStreetMap (Chosen - Free, no key)
- Google Maps (Alternative - Paid)
- Mapbox (Alternative - Paid)

### AI Services
- Rule-based (Chosen for static mode)
- Google Gemini (Optional for dynamic mode)
- OpenAI GPT (Alternative)
- Anthropic Claude (Alternative)

---

## Version Requirements

### Minimum Versions
- Python: 3.11+
- Node.js: 18+
- PostgreSQL: 16+
- Docker: 20.10+

### Recommended Versions
- Python: 3.12
- Node.js: 20 LTS
- PostgreSQL: 16 Alpine
- Docker: Latest

---

## Additional Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Material UI: https://mui.com/
- Open-Meteo: https://open-meteo.com/
- OpenStreetMap: https://www.openstreetmap.org/

### Learning Resources
- Python Async: https://docs.python.org/3/library/asyncio.html
- Pydantic: https://docs.pydantic.dev/
- TypeScript: https://www.typescriptlang.org/docs/

---

## Future Additions (Optional)

### Potential Integrations
- Slack integration for notifications
- WhatsApp for SMS alerts
- Google Calendar API for scheduling
- Microsoft Outlook integration
- Additional weather providers
- Advanced AI models
- Real-time data streaming
- Mobile app (React Native)

### Scalability Options
- Redis for caching
- Message queue (RabbitMQ, Kafka)
- Load balancer (Nginx)
- CDN (Cloudflare, CloudFront)
- Monitoring (Prometheus, Grafana)
