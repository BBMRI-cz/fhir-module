# FHIR Place UI

A Next.js application for managing FHIR data with authentication and SQLite database.

## Features

- User authentication with NextAuth.js
- SQLite database for data persistence
- Modern UI with Tailwind CSS
- Docker support for containerized deployment

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Local Development

1. Install dependencies:

   ```bash
   npm install
   ```

2. Initialize the database:

   ```bash
   npm run db:init
   ```

3. Start the development server:

   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Docker Deployment

The application is configured to run in Docker containers with the main `compose.yaml` file.

### Environment Variables

The following environment variables are required:

- `NEXTAUTH_SECRET`: Secret key for NextAuth.js (change in production)
- `AUTH_TRUST_HOST`: Set to `true` for Docker deployment
- `NODE_ENV`: Set to `production` for Docker
- `PORT`: Application port (default: 3000)

### Running with Docker Compose

1. From the project root, run:

   ```bash
   docker-compose --profile dev up fhir-ui
   ```

2. The UI will be available at [http://localhost:3000](http://localhost:3000)

### Database

The SQLite database is stored in the `/app/data` directory and persisted using Docker volumes. The database will be automatically initialized on first run.

## Available Scripts

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm run start`: Start production server
- `npm run db:init`: Initialize database with seed data
- `npm run db:generate`: Generate database schema
- `npm run db:migrate`: Run database migrations
