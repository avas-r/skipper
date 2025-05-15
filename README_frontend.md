# Skipper Frontend

This is the web frontend for the Skipper Automation Platform. It provides a user interface for managing automation agents, jobs, packages, and schedules.

## Features

- Dashboard with system overview
- Agent management
- Job management
- Package management
- Schedule management
- Queue monitoring

## Getting Started

### Prerequisites

- Node.js 16+ and npm

### Development Setup

1. Install dependencies:

```bash
npm install
```

2. Configure environment:

Create a `.env` file in the root directory with the following content:

```
REACT_APP_API_URL=http://localhost:8000
```

3. Start development server:

```bash
npm start
```

### Building for Production

```bash
npm run build
```

This will create a production build in the `build` directory.

## Docker Deployment

The project includes a Dockerfile to build a containerized version for production:

```bash
docker build -t skipper-frontend:latest .
```

You can also use the included docker-compose.yml from the main repository to deploy the entire stack.

## Configuration

Configure the application using the following environment variables:

- `REACT_APP_API_URL`: URL of the API server (e.g., https://api.skipper2.com)

## Domain Setup

The frontend is configured to be deployed at: `https://skipper2.com`

API endpoints will be available at: `https://api.skipper2.com`