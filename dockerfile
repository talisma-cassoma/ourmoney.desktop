# Use Node.js as the base image
FROM node:23-alpine

# Set the working directory inside the container
WORKDIR /usr/app

# Install OpenSSL (required by Prisma)
RUN apk add --no-cache openssl

# Copy package files and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy Prisma files
COPY prisma ./prisma

# Install Prisma CLI as a dev dependency
RUN npm install prisma --save-dev

# Expose Prisma Studio port (if using)
EXPOSE 5555

# Declare volume after dependencies are installed
VOLUME /usr/app

# Keep container running for debugging purposes
#CMD ["tail", "-f", "/dev/null"]
CMD ["npx", "prisma", "studio"]
