# =============================================================================
# Otomeshon Frontend Dockerfile - Next.js Multi-Stage Production Build
# =============================================================================
#
# This Dockerfile creates a production-ready container for the Otomeshon frontend
# Next.js application. It uses a multi-stage build approach to optimize image size,
# security, and performance while supporting both development and production workflows.
#
# Key Features:
# - Multi-stage build for optimized production images
# - Next.js standalone output for minimal runtime dependencies
# - Security-first approach with non-root user execution
# - Alpine Linux base for minimal attack surface
# - Optimized Node.js dependency caching
# - Development and production configurations
#
# Build Stages:
# 1. Base: Common dependencies and system setup
# 2. Development: Hot-reload development environment
# 3. Build: Next.js application compilation
# 4. Production: Minimal runtime environment
#
# Usage:
#   Development: docker build --target development -t otomeshon-frontend:dev .
#   Production:  docker build --target production -t otomeshon-frontend:prod .
# =============================================================================

# BASE STAGE - Common foundation for all build stages
# Uses Node.js 20 Alpine for minimal size and security
FROM node:20-alpine as base

# Set working directory for all subsequent operations
WORKDIR /app

# SYSTEM DEPENDENCIES INSTALLATION
# Install essential system packages for development and runtime
RUN apk add --no-cache \
    curl \      # HTTP client for health checks and external API calls
    bash \      # Enhanced shell for debugging and script execution
    git         # Version control for installing packages from Git repositories

# =============================================================================
# DEVELOPMENT STAGE - Optimized for development workflow
# =============================================================================
FROM base as development

# DEPENDENCY INSTALLATION
# Copy package files first to leverage Docker layer caching
COPY package*.json ./

# Install all dependencies including development dependencies for hot reload
RUN npm ci

# APPLICATION SOURCE CODE
# Copy the entire source code for development
COPY . .

# NETWORK CONFIGURATION
# Expose port for development server
EXPOSE 3000

# DEVELOPMENT SERVER STARTUP
# Start Next.js development server with hot reload and external access
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# =============================================================================
# BUILD STAGE - Next.js application compilation and optimization
# =============================================================================
FROM base as build

# DEPENDENCY INSTALLATION
# Copy package files first to leverage Docker layer caching
COPY package*.json ./

# Install all dependencies including development dependencies needed for build
RUN npm ci

# APPLICATION SOURCE CODE
# Copy the entire source code for compilation
COPY . .

# NEXT.JS BUILD PROCESS
# Build the Next.js application for production deployment
# This creates optimized static assets, server-side rendering components,
# and generates the standalone server.js file for production
RUN npm run build

# =============================================================================
# PRODUCTION STAGE - Minimal runtime environment
# =============================================================================
FROM node:20-alpine as production

# APPLICATION DIRECTORY SETUP
# Create application directory for the production runtime
WORKDIR /app

# SYSTEM DEPENDENCIES FOR RUNTIME
# Install minimal system dependencies needed for production operation
RUN apk add --no-cache curl    # HTTP client for health checks

# APPLICATION DEPLOYMENT
# Copy the standalone build output from the build stage
# Next.js standalone build includes only necessary runtime files
COPY --from=build /app/.next/standalone ./     # Copy standalone server and dependencies
COPY --from=build /app/.next/static ./.next/static  # Copy static assets for serving

# SECURITY CONFIGURATION
# Create non-root user and group for secure container execution
RUN addgroup -g 1001 -S nextjs && \    # Create nextjs group with specific GID
    adduser -S nextjs -u 1001           # Create nextjs user with specific UID

# FILE OWNERSHIP CONFIGURATION
# Set proper file ownership for the non-root user
RUN chown -R nextjs:nextjs /app

# USER SWITCH
# Switch to non-root user for security best practices
USER nextjs

# HEALTH CHECK CONFIGURATION
# Comprehensive health check for container orchestration and monitoring
HEALTHCHECK --interval=30s \      # Check every 30 seconds
    --timeout=30s \               # Allow 30 seconds for response
    --start-period=5s \           # Wait 5 seconds before first check
    --retries=3 \                 # Retry 3 times before marking unhealthy
    CMD curl -f http://localhost:3000/ || exit 1  # Use root endpoint for health check

# NETWORK CONFIGURATION
# Expose the port that the Next.js server will listen on
EXPOSE 3000

# PRODUCTION SERVER STARTUP
# Start the Next.js standalone server
# The server.js file is generated by Next.js standalone build and contains
# all necessary dependencies for serving the application
CMD ["node", "server.js"]
