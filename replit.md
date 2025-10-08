# AI-Based Answer Sheet Evaluation System

## Project Overview
A modern, responsive web UI/UX for an AI-powered answer sheet evaluation system. The platform allows teachers to upload answer keys and students to submit handwritten answer sheet images for automated evaluation using ML/NLP technology.

## Recent Changes (October 8, 2025)
- Complete UI implementation with separate HTML, CSS, and JavaScript files
- Landing page with animated gradient design and floating cards
- Role-based authentication (Teacher/Student) with smooth transitions
- Teacher dashboard with answer key upload, submission review, and evaluation interface
- Student dashboard with answer sheet upload, results viewing, and performance analytics
- Dark/light mode toggle across all pages
- Responsive design using CSS Flexbox/Grid
- Interactive features: file uploads with preview, modals, progress animations, canvas charts

## Project Architecture

### File Structure
```
├── index.html                 # Landing page
├── login.html                 # Login page
├── signup.html               # Signup page
├── teacher-dashboard.html    # Teacher dashboard
├── student-dashboard.html    # Student dashboard
├── css/
│   ├── global.css           # Global styles and theme variables
│   ├── landing.css          # Landing page styles
│   ├── auth.css             # Login/signup styles
│   └── dashboard.css        # Dashboard styles
├── js/
│   ├── theme.js             # Dark/light mode toggle
│   ├── landing.js           # Landing page interactions
│   ├── auth.js              # Authentication logic
│   ├── dashboard.js         # Dashboard interactions
│   └── chart.js             # Performance chart rendering
└── images/                   # Image assets folder
```

### Key Features

#### For Teachers
- Upload answer keys (descriptive & MCQ)
- View student submissions with filters
- AI-powered evaluation simulation
- Review and adjust evaluation results
- Question-wise breakdown and feedback

#### For Students
- Upload handwritten answer sheet images (multiple pages)
- View AI-generated results and scores
- Performance analytics with charts
- Question-wise feedback
- Subject-wise performance tracking

### Design System
- **Color Palette**: AI-inspired blues (#6366f1), purples (#8b5cf6), cyan accents (#06b6d4)
- **Typography**: Segoe UI with proper hierarchy
- **Components**: Cards, buttons, forms, modals, progress bars
- **Animations**: Fade-in, slide-in, float animations
- **Responsive**: Mobile-first design with breakpoints at 768px and 1024px

### Interactive Features
1. **File Upload**: Drag-and-drop with image preview
2. **Navigation**: Smooth scrolling, section switching
3. **Forms**: Client-side validation and submission
4. **Charts**: Canvas-based performance visualization
5. **Modals**: Result details popup
6. **Theme Toggle**: Persistent dark/light mode

## Technical Details

### Technologies Used
- Pure HTML5 (semantic markup)
- CSS3 (Flexbox, Grid, custom properties, animations)
- Vanilla JavaScript (ES6+)
- Canvas API for charts
- LocalStorage for theme and user data

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Responsive across desktop, tablet, mobile

### Future Integration Points
- ML/NLP model integration for OCR and evaluation
- Backend API for data persistence
- Real-time evaluation processing
- Database storage for exams and results
- User authentication system
- File storage service for answer sheets

## Development Notes
- All interactive features are functional with simulated data
- Ready for backend/ML integration
- No external dependencies or frameworks
- Clean, modular code structure
- Accessible design with proper semantic HTML
