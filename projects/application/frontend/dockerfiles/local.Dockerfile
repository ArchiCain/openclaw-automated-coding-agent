FROM node:20-alpine

WORKDIR /app

# Install dependencies if needed
# Volume mounting will overlay this, so we install on startup
COPY package*.json ./

# Expose service port
EXPOSE 3000

# Install dependencies and start Angular dev server
# Use --host 0.0.0.0 to allow connections from outside container
CMD sh -c "npm install && ng serve --host 0.0.0.0 --port 3000"
