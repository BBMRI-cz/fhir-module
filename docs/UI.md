# User Interface (UI)

The FHIR module includes a modern web-based user interface built with Next.js, providing an intuitive way to manage and monitor the FHIR data synchronization process.

## Overview

The UI application (`fhir-place`) is a Next.js application that offers:

- **User Authentication**: Secure login system with NextAuth.js
- **Dashboard**: Real-time monitoring of system health and synchronization status
- **Backend Control**: Start, stop, and manage the FHIR module backend operations
- **Settings Management**: User profile and system configuration
- **Modern Design**: Responsive UI with Tailwind CSS and dark/light theme support

## Features

### Authentication System

- Secure user registration and login
- Session management with NextAuth.js
- Password validation with configurable requirements
- User profile management

### Dashboard

- Real-time system health monitoring
- Synchronization status indicators
- Prometheus metrics integration
- System uptime and performance metrics

### Backend Control

- Start/stop FHIR module operations
- Monitor synchronization processes
- View operation logs and status
- Manual trigger for data synchronization

### Settings

- User profile management
- Password change functionality
- Theme switching (light/dark mode)
- Font size adjustment for accessibility

## Architecture

The UI is built using:

- **Framework**: Next.js 14 with App Router
- **Authentication**: NextAuth.js with custom credentials provider
- **Database**: SQLite for user data persistence
- **Styling**: Tailwind CSS with shadcn/ui components
- **State Management**: React hooks and server actions
- **Testing**: Jest with React Testing Library

## Development Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Local Development

1. Navigate to the UI directory:

   ```bash
   cd ui/fhir-place
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Initialize the database:

   ```bash
   npm run db:init
   ```

4. Start the development server:

   ```bash
   npm run dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Available Scripts

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm run start`: Start production server
- `npm run db:init`: Initialize database with seed data
- `npm run db:generate`: Generate database schema
- `npm run db:migrate`: Run database migrations
- `npm run test`: Run tests
- `npm run test:watch`: Run tests in watch mode

## Docker Deployment

The UI is containerized and deployed alongside the main FHIR module using Docker Compose.

### Running with Docker Compose

From the project root directory:

```bash
docker compose --profile ui up
```

Note that the UI container is **heavily** dependant on the prod / dev ones and monitoring

```bash
# Best to the whole stack
docker compose --profile dev -- profile monitoring --profile ui up
```

The UI will be available at [http://localhost:3000](http://localhost:3000).

### Database Persistence

The SQLite database is stored in the `/app/data` directory within the container and persisted using Docker volumes. The database is automatically initialized on first run with default user accounts.

## Environment Variables

The UI application uses the following environment variables:

### Core Configuration

| Variable name     | Default value | Description                                                |
| ----------------- | ------------- | ---------------------------------------------------------- |
| `NODE_ENV`        | `development` | Node.js environment mode (development/production)          |
| `PORT`            | `3000`        | Port on which the application runs                         |
| `NEXTAUTH_SECRET` | _required_    | Secret key for NextAuth.js session encryption              |
| `AUTH_TRUST_HOST` | `false`       | Set to `true` for Docker deployment to trust proxy headers |

### Backend Integration

| Variable name     | Default value            | Description                          |
| ----------------- | ------------------------ | ------------------------------------ |
| `BACKEND_API_URL` | `http://localhost:5000`  | URL of the FHIR module backend API   |
| `PROMETHEUS_URL`  | `http://prometheus:9090` | URL of the Prometheus metrics server |

### Password Validation Configuration

| Variable name                    | Default value         | Description                             |
| -------------------------------- | --------------------- | --------------------------------------- | ---------------------------------------- |
| `PASSWORD_MIN_LENGTH`            | `8`                   | Minimum password length requirement     |
| `PASSWORD_MAX_LENGTH`            | `128`                 | Maximum password length requirement     |
| `PASSWORD_REQUIRE_UPPERCASE`     | `false`               | Require uppercase letters in passwords  |
| `PASSWORD_REQUIRE_LOWERCASE`     | `false`               | Require lowercase letters in passwords  |
| `PASSWORD_REQUIRE_NUMBERS`       | `false`               | Require numbers in passwords            |
| `PASSWORD_REQUIRE_SPECIAL_CHARS` | `false`               | Require special characters in passwords |
| `PASSWORD_SPECIAL_CHARS`         | `!@#$%^&\*()\_+-=[]{} | ;:,.<>?`                                | Allowed special characters for passwords |

### Example .env Configuration

```bash
# Core Configuration
NODE_ENV=production
PORT=3000
NEXTAUTH_SECRET=your-secret-key-change-in-production
AUTH_TRUST_HOST=true

# Backend Integration
BACKEND_API_URL=http://fhir-module:5000
PROMETHEUS_URL=http://prometheus:9090

# Password Requirements (optional)
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL_CHARS=true
```

## Security Considerations

### Environment Variables

- Sensitive variables like `NEXTAUTH_SECRET` should be kept secure
- Use strong, randomly generated secrets in production
- Never commit sensitive environment variables to version control

## Monitoring and Logging

The UI integrates with the monitoring stack:

- **Prometheus Integration**: Queries metrics from the Prometheus server
- **Health Checks**: Real-time system health monitoring
- **Error Tracking**: Client-side error logging and reporting
- **Performance Metrics**: Page load times and user interaction tracking

## Troubleshooting

### Common Issues

1. **Database Connection Issues**

   - Ensure the database is properly initialized: `npm run db:init`
   - Check that the data directory has proper permissions

2. **Authentication Problems**

   - Verify `NEXTAUTH_SECRET` is set and consistent
   - Check that `AUTH_TRUST_HOST` is set to `true` in Docker environments

3. **Backend Connection Issues**

   - Verify `BACKEND_API_URL` points to the correct FHIR module endpoint
   - Ensure the backend service is running and accessible

4. **Build Failures**
   - Clear node_modules and reinstall: `rm -rf node_modules && npm install`
   - Check Node.js version compatibility (requires 18+)

### Logs

Application logs can be viewed using:

```bash
# Docker logs
docker logs fhir-ui -f

# Development logs
npm run dev
```

## Contributing

When contributing to the UI:

1. Follow the existing code style and patterns
2. Write tests for new features
3. Update documentation for any new environment variables
4. Ensure responsive design works on all screen sizes
5. Test authentication flows thoroughly
