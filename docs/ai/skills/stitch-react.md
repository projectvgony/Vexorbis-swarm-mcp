# Stitch-to-React Skill

Guide for agents to convert Stitch designs into React component systems using the Stitch MCP server.

---

## When to Use This Skill

- Converting Stitch designs to React components
- Generating component libraries from design systems
- Creating new UI screens from Stitch projects
- Automating design-to-code workflows

## The Stitch-to-React Protocol

### 1. Discover Available Stitch Projects
List all Stitch projects and their screens:
```
Use stitch MCP tools to list projects
Format: Show each project with its screens and screen IDs
```

### 2. Select Target Screen
Identify the specific project and screen to convert:
- **Project Name**: e.g., "Podcast App"
- **Screen Name**: e.g., "Landing Page"
- **Screen ID**: Obtained from project listing

### 3. Download Design Assets
Retrieve both HTML and image assets:
```
Download HTML: Use stitch MCP to get Tailwind-based HTML
Download Image: Get the design preview image
Save to: ./tmp/${screen-name}.html and ./tmp/${screen-name}.png
```

### 4. Generate React Component System
Convert HTML to well-structured React components:
- **Analyze Structure**: Identify distinct UI sections
- **Component Breakdown**: Separate into logical components
  - Layout components (Header, Footer, Navigation)
  - Feature components (Hero, Card, Form)
  - Primitive components (Button, Input, Badge)
- **Best Practices**:
  - Use functional components with hooks
  - Extract reusable primitives
  - Maintain design system tokens (colors, spacing)
  - Keep Tailwind CSS classes from original design

### 5. Setup Build Environment
Create a Vite + React development environment:
```powershell
npm create vite@latest . -- --template react
npm install
npm run dev
```

## Success Metrics

- All Stitch design elements are preserved in React components
- Component hierarchy is logical and reusable
- Development server runs successfully
- Design matches original Stitch screen
