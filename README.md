# 🚀 Future-Forward Career Planner

An AI-powered Streamlit application that provides in-depth career analysis and generates personalized learning paths for any domain. Get a 5-10 year forecast, discover emerging job roles, and receive a curated list of learning resources (videos, articles, or projects) tailored to your preferred style.

![Future-Forward Career Planner Screenshot](https://i.imgur.com/8aB7J3E.png)

## ✨ Features

-   **🤖 AI-Powered Domain Analysis:** Get a futuristic forecast of any career field, including an overview, 5-10 year outlook, and key growth areas.
-   **💼 Emerging Role Identification:** Discover new and emerging job roles within your chosen domain, complete with descriptions and required skills.
-   **📚 Personalized Learning Paths:** Generate a step-by-step learning plan based on your preferred style:
    -   **Visual:** A curated path of YouTube tutorials.
    -   **Reading:** A list of relevant articles and guides.
    -   **Practical:** A sequence of project-based learning steps.
-   **🌐 Automated Resource Curation:** The application automatically searches Google and YouTube to find relevant, high-quality resources for your learning steps.
-   **📈 Structured & Reliable AI Output:** Leverages Pydantic to ensure the AI's response is always structured, reliable, and validated.
-   **🖥️ Interactive Web Interface:** Built with the user-friendly and fast Streamlit framework.

---

## 🛠️ How It Works

The application operates through a core `CareerCounselorAgent` that follows a two-step process:

1.  **Analysis Phase:**
    -   The user enters a career domain (e.g., "Quantum Computing").
    -   The agent uses a **LangChain Expression Language (LCEL)** chain, powered by the **Google Gemini** model, to analyze the domain.
    -   The AI's output is parsed and validated against a Pydantic `DomainAnalysis` model to structure the information.

2.  **Learning Path Generation:**
    -   The agent extracts the required skills from the most prominent emerging role identified in the analysis.
    -   Based on the user's selected learning style (e.g., 'visual'), a second LCEL chain generates a `LearningPath` object, outlining the curriculum.
    -   For each step in the curriculum, the agent performs a targeted search using the **YouTube and Google Search APIs** to find a relevant video or article link.
    -   The final, resource-filled analysis and learning path are displayed to the user.

---

## ⚙️ Tech Stack

-   **Framework:** [Streamlit](https://streamlit.io/)
-   **LLM:** [Google Gemini](https://ai.google.dev/)
-   **LLM Orchestration:** [LangChain](https://www.langchain.com/) (using LCEL)
-   **Data Validation:** [Pydantic](https://pydantic.dev/)
-   **Search APIs:** [Google Search API](https://developers.google.com/custom-search/v1/overview) & [YouTube Data API v3](https://developers.google.com/youtube/v3)

---

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### 1. Prerequisites

-   Python 3.8+
-   A **Google API Key**. You can get one from the [Google AI Studio](https://makersuite.google.com/app/apikey).
-   A **YouTube API Key**. You can get one from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials). Make sure the "YouTube Data API v3" is enabled for your project.

### 2. Clone the Repository

```bash
git clone [https://github.com/Bhavanam-Gireesh-Reddy/Gen-AI-Prototype.git](https://github.com/Bhavanam-Gireesh-Reddy/Gen-AI-Prototype.git)
cd Gen-AI-Prototype
