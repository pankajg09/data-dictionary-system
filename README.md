# Data Dictionary System

A powerful tool for analyzing code and generating comprehensive data dictionaries using AI. This system helps developers understand code structure, relationships, and documentation through automated analysis.

## 🌟 Features

- **Code Analysis**: Analyzes code using AI (OpenAI GPT or Google Gemini) to extract:
  - Data structures and tables
  - Data relationships
  - Important code snippets with explanations
  - Data sources and transformations
  - Potential reuse opportunities
  - Documentation summaries

- **Modern Web Interface**: 
  - Clean and intuitive UI for code submission
  - Real-time analysis results
  - Support for multiple file formats
  - Interactive visualization of relationships

- **Flexible Architecture**:
  - FastAPI backend with async support
  - React frontend with Material-UI
  - Support for multiple AI providers
  - Configurable analysis parameters

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Node.js 16+
- OpenAI API key or Google Gemini API key

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create .env file
cp .env.example .env

# Add your API keys
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
```

4. Start the backend server:
```bash
python -m uvicorn main:app --reload --port 3001 --host 0.0.0.0
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the frontend server:
```bash
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend: http://localhost:3001
- API Documentation: http://localhost:3001/docs

## 💡 Usage

1. Access the web interface at http://localhost:3000
2. Upload your code file or paste code directly
3. Click "Analyze" to start the analysis
4. View the comprehensive analysis results including:
   - Data structures
   - Relationships
   - Code snippets
   - Documentation
   - Reuse opportunities

## 🔧 Configuration

The system supports various configuration options:

- Multiple AI providers (OpenAI/Gemini)
- Custom analysis parameters
- CORS settings for different environments
- Port configurations

## 📝 License

Copyright © 2024 Pankaj Gupta. All rights reserved.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

## 📞 Contact

Pankaj Goyal - pankajgoyal09@gmail.com

---

Made with ❤️ by Pankaj Goyal 