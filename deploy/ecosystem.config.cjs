module.exports = {
  apps: [
    {
      name: "idbi-frontend",
      cwd: "/opt/idbi-platform/frontend",
      script: "node_modules/.bin/next",
      args: "start --port 3000",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "512M",
      env: {
        NODE_ENV: "production",
        PORT: 3000,
      },
    },
  ],
};
