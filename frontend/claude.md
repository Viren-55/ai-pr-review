# GenAI Code Review - Frontend

## Quick Reference & Navigation

### Project Structure
```
frontend/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Main landing page
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── CodeInput.tsx      # Code input form
│   ├── CodeReviewer.tsx   # Main review component
│   ├── FeatureSection.tsx # Feature showcase
│   ├── Header.tsx         # Navigation header
│   ├── Footer.tsx         # Page footer
│   ├── PRQuestionBox.tsx  # PR question input
│   ├── ReviewResults.tsx  # Review output display
│   └── ui/               # Reusable UI components
├── lib/hooks/            # Custom React hooks
└── package.json          # Dependencies & scripts
```

### Development Commands
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint

# Type checking
npm run type-check
```

### Key Components

#### Main Page (`app/page.tsx`)
- Landing page with hero section
- Feature showcase
- Code review interface

#### CodeReviewer (`components/CodeReviewer.tsx`)
- Main review functionality
- Handles code input and analysis
- Displays review results

#### UI Components (`components/ui/`)
- Button: Reusable button component
- LoadingSpinner: Loading states
- Tabs: Tab navigation

### Development Notes
- Built with Next.js 14+ (App Router)
- Styled with Tailwind CSS
- TypeScript for type safety
- Custom hooks for state management

### Common Issues & Solutions
- If dev server fails: Check port 3000 availability
- Type errors: Run `npm run type-check`
- Styling issues: Check Tailwind config

### Testing
- Use Playwright for UI testing
- Test on multiple viewports
- Check accessibility compliance

### Backend Integration
- API endpoints expected at backend service
- Review results fetched via HTTP requests
- Error handling for network issues