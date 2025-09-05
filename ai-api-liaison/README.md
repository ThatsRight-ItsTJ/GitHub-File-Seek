# AI-Powered Task Management System

An intelligent task management system that uses Natural Language Processing (NLP) and Machine Learning (ML) to analyze, categorize, and predict task properties from Jira data. The system features advanced BERT embeddings, XGBoost models, and an interactive Streamlit dashboard.

Link to the video demonstration:- https://drive.google.com/file/d/1FMaZ8xEeqLmVfFCda9zzBMGdhKYhocL-/view?usp=sharing

## ⚡ Quick Start (5 minutes)

1. **Clone & Setup:**
   ```bash
   git clone https://github.com/Harshkkk6/-AI-Powered-Task-Management-System.git
   cd AI-Powered-Task-Management-System
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

2. **Run the App:**
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Open Browser:** Go to **http://localhost:8501**

4. **Start Using:** Add your first task and watch AI predict its type and priority!

📖 **For detailed setup instructions, see [SETUP.md](SETUP.md)**

## 🚀 Features

- **Smart Task Classification**: Automatically categorizes tasks using BERT embeddings and TF-IDF features
- **Priority Prediction**: Predicts task priority using XGBoost with advanced feature engineering
- **Interactive Dashboard**: User-friendly Streamlit interface with multiple pages
- **Workload Analysis**: Real-time workload visualization and team capacity analysis
- **Deadline Alerts**: Automated deadline tracking and overdue task notifications
- **Similar Task Finder**: AI-powered task similarity matching
- **Data Export**: Easy export functionality for task data
- **Smart Assignment**: AI-powered team member recommendations
- **Recent Tasks Management**: View and delete tasks with bulk operations
- **Team Health Monitoring**: Comprehensive alerts and performance tracking

## 📋 Project Structure

```
├── streamlit_app.py                    # Interactive web application
├── train_model.py                      # Task classification model training
├── train_priority_model.py             # Priority prediction model training
├── train_tfidf_vectorizer.py           # TF-IDF vectorizer training for tasks
├── train_priority_tfidf_vectorizer.py  # TF-IDF vectorizer training for priority
├── analyze_data.py                     # Data analysis and visualization
├── create_task_notebook.py             # Task creation and management utilities
├── task_management_project.ipynb       # Main analysis notebook
├── jira_dataset.csv                    # Raw Jira dataset
├── cleaned_jira_dataset.csv            # Processed and cleaned dataset
├── task_classifier.pkl                 # Saved task classification model
├── priority_predictor.pkl              # Saved priority prediction model
├── tfidf_vectorizer.pkl                # TF-IDF vectorizer for task classification
├── priority_tfidf_vectorizer.pkl       # TF-IDF vectorizer for priority prediction
├── data_analysis.png                   # Generated analysis visualizations
├── requirements.txt                    # Project dependencies
└── README.md                          # Project documentation
```

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Harshkkk6/-AI-Powered-Task-Management-System.git
   cd AI-Powered-Task-Management-System
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Quick Start

### Running the Streamlit App

1. **Start the Streamlit application:**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Open your web browser** at the provided URL (usually http://localhost:8501)

3. **Navigate through the app pages:**
   - **New Task**: Submit and analyze new tasks
   - **Live Dashboard**: View workload visualizations
   - **Smart Predictor**: Get AI predictions for task properties
   - **Alerts**: Monitor deadlines and overdue tasks
   - **Data Export**: Export task data

### Training Models (Optional)

If you want to retrain the models with your own data:

1. **Train the task classification model:**
   ```bash
   python train_model.py
   ```

2. **Train the priority prediction model:**
   ```bash
   python train_priority_model.py
   ```

3. **Train TF-IDF vectorizers:**
   ```bash
   python train_tfidf_vectorizer.py
   python train_priority_tfidf_vectorizer.py
   ```

## 📊 App Features

### 🆕 New Task Page
- Submit task descriptions with optional deadline and assignee
- Automatic issue type and priority prediction
- AI-powered assignee recommendations based on workload
- Similar task suggestions with similarity scores

### 📊 Live Dashboard
- Interactive workload visualization
- Filter by priority and issue type
- Real-time team capacity analysis
- Bar charts showing task distribution

### 🧠 Smart Predictor
- Paste any task description for instant predictions
- View confidence scores for predictions
- Test different scenarios and descriptions

### 📎 Alerts Panel
- Tasks due in the next 3 days
- Overdue task tracking
- Visual indicators for urgency levels
- Deadline management

### 📤 Data Export
- Download complete task list as CSV
- Export filtered data
- Backup functionality

## 🤖 AI Models

### Task Classification Model
- **Algorithm**: XGBoost with BERT embeddings
- **Features**: BERT embeddings + TF-IDF + categorical features
- **Performance**: High accuracy for issue type prediction
- **Input**: Task summary text
- **Output**: Issue type (Bug, Story, Task, etc.)

### Priority Prediction Model
- **Algorithm**: XGBoost with advanced feature engineering
- **Features**: BERT embeddings + TF-IDF + project type + text length
- **Performance**: Optimized for priority classification
- **Input**: Task summary and metadata
- **Output**: Priority level (High, Medium, Low, etc.)

### BERT Integration
- **Model**: all-MiniLM-L6-v2 (Sentence Transformers)
- **Purpose**: Generate semantic embeddings for text
- **Benefits**: Better understanding of task context and meaning

## 📈 Performance & Metrics

- **Accuracy**: High prediction accuracy for both classification tasks
- **Confidence Scores**: Probabilistic predictions with confidence levels
- **Similarity Matching**: Cosine similarity for finding related tasks
- **Real-time Processing**: Fast inference for interactive use

## 🔧 Technical Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **ML Framework**: Scikit-learn, XGBoost
- **NLP**: Sentence Transformers (BERT), NLTK, TF-IDF
- **Data Processing**: Pandas, NumPy
- **Visualization**: Matplotlib, Seaborn
- **Model Persistence**: Joblib

## 📝 Usage Examples

### Submitting a New Task
1. Go to "New Task" page
2. Enter task description: "Fix login authentication bug in user portal"
3. Set optional deadline and assignee
4. Submit to get automatic predictions:
   - Issue Type: Bug (95% confidence)
   - Priority: High (87% confidence)
   - Recommended Assignee: John Doe (least loaded)

### Finding Similar Tasks
1. Enter task description
2. View similar tasks with similarity scores
3. Learn from previous solutions and approaches

### Monitoring Deadlines
1. Check "Alerts" page
2. View tasks due soon (yellow indicators)
3. Address overdue tasks (red indicators)

## 🛠️ Development

### Project Structure
- **Models**: Pre-trained ML models for predictions
- **Data**: CSV files with Jira dataset
- **Scripts**: Training and utility scripts
- **App**: Streamlit web application

### Adding New Features
1. Modify `streamlit_app.py` for UI changes
2. Update training scripts for model improvements
3. Add new data processing in analysis scripts

## 📊 Data Sources

- **Jira Dataset**: Historical task data from Jira
- **Features**: Task summaries, priorities, assignees, deadlines
- **Processing**: Cleaned and preprocessed for ML training

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Jira**: For providing the dataset
- **Streamlit**: For the excellent web application framework
- **Hugging Face**: For the Sentence Transformers library
- **XGBoost**: For the powerful gradient boosting implementation
- **Scikit-learn**: For comprehensive ML tools
- **NLTK**: For NLP capabilities

## 📞 Support

For questions, issues, or contributions, please:
- Open an issue on GitHub
- Check the documentation
- Review the code comments

---

**Made with ❤️ for better task management**
