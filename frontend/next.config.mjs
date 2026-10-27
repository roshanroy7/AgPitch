/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export", // build plain HTML/JS files (the "out" folder) for Azure Static Web Apps
  agentRules: false, // don't generate AGENTS.md in the project
  devIndicators: false, // hide the Next.js "N" badge while developing
};

export default nextConfig;
