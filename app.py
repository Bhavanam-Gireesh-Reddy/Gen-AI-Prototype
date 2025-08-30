# app.py

import streamlit as st
from typing import List
import sys

# LangChain & Pydantic Imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field, ValidationError

# Imports for Search Tools
from googleapiclient.discovery import build
from googlesearch import search

# --- 1. Define Data Schemas (Pydantic Models) ---
# (This section is unchanged from your original code)

class EmergingRole(BaseModel):
    title: str = Field(description="The title of the emerging job role.")
    description: str = Field(description="What this role involves and why it's emerging.")
    required_skills: List[str] = Field(description="A list of key skills needed for this role.")

class DomainAnalysis(BaseModel):
    domain_overview: str = Field(description="A concise, engaging summary of what this domain is about.")
    future_outlook_summary: str = Field(description="A 5-10 year projection for this domain, highlighting key trends and disruptions.")
    growth_areas: List[str] = Field(description="A list of specific areas projected to see significant growth.")
    emerging_roles: List[EmergingRole] = Field(description="A list of new and emerging job roles in this domain.")

class LearningStep(BaseModel):
    step: int = Field(description="The sequential number of the learning step.")
    title: str = Field(description="A clear and descriptive title for this learning step.")
    type: str = Field(description="The type of learning content, e.g., 'reading', 'video', 'project'.")
    content: str = Field(description="For 'video' or 'reading', a concise topic suitable for a web search. For 'project', a brief description of the project.")

class LearningPath(BaseModel):
    path: List[LearningStep] = Field(description="The full list of structured learning steps.")


# --- 2. The Career Counselor Agent (Modified for Streamlit) ---

class CareerCounselorAgent:
    """An AI agent that provides career analysis and learning paths using external tools."""

    def __init__(self, google_api_key: str, youtube_api_key: str):
        """Initializes the agent with API keys from Streamlit secrets."""
        try:
            self.model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7, google_api_key=google_api_key)
            self.youtube_service = build('youtube', 'v3', developerKey=youtube_api_key)
        except Exception as e:
            st.error(f"Failed to initialize Google services: {e}")
            st.stop()
        self._create_chains()

    # The search tool methods remain the same
    def _search_youtube_video(self, query: str) -> str:
        try:
            search_response = self.youtube_service.search().list(
                q=f"{query} tutorial", part='snippet', maxResults=1, type='video', videoDefinition='high'
            ).execute()
            if search_response.get("items"):
                video_id = search_response['items'][0]['id']['videoId']
                return f"https://www.youtube.com/watch?v={video_id}"
            return "No relevant video found."
        except Exception as e:
            st.warning(f"YouTube API Error for query '{query}': {e}")
            return "Could not fetch video link due to an API error."

    def _search_for_article(self, query: str) -> str:
        try:
            # Adding a pause to prevent being blocked by Google search
            search_results = search(f"{query} article tutorial", num_results=1, lang="en", pause=2.0)
            return next(search_results, "No relevant article found.")
        except Exception as e:
            st.warning(f"Web Search Error for query '{query}': {e}")
            return "Could not fetch article link due to a search error."

    # The chain creation method remains the same
    def _create_chains(self):
        analysis_parser = PydanticOutputParser(pydantic_object=DomainAnalysis)
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a futuristic career analyst..."),
            ("human", "Analyze the career domain: '{domain}'.\n\n{format_instructions}")
        ]).partial(format_instructions=analysis_parser.get_format_instructions())
        self.analysis_chain = analysis_prompt | self.model | analysis_parser

        path_parser = PydanticOutputParser(pydantic_object=LearningPath)
        path_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert curriculum developer... Your task is to create a personalized learning path... strictly following the user's preferred learning style..."),
            ("human", "Create a learning path for the '{domain}' domain, focusing on these skills: {key_skills}. The user's preferred learning style is '{learning_style}'.\n\n{format_instructions}")
        ]).partial(format_instructions=path_parser.get_format_instructions())
        self.learning_path_chain = path_prompt | self.model | path_parser

    # The agent's core logic methods remain the same
    def get_domain_analysis(self, domain: str) -> DomainAnalysis:
        return self.analysis_chain.invoke({"domain": domain})

    def get_learning_path(self, domain: str, skills: List[str], style: str) -> LearningPath:
        return self.learning_path_chain.invoke({
            "domain": domain,
            "key_skills": ", ".join(skills),
            "learning_style": style
        })

# --- 3. Streamlit UI and Application Logic ---

# Use st.cache_resource to initialize the agent only once
@st.cache_resource
def load_agent():
    """Loads the CareerCounselorAgent, handling API key checks."""
    if "GOOGLE_API_KEY" not in st.secrets or "YOUTUBE_API_KEY" not in st.secrets:
        st.error("🔴 CRITICAL: GOOGLE_API_KEY and YOUTUBE_API_KEY must be set in Streamlit secrets.")
        st.stop()
    
    return CareerCounselorAgent(
        google_api_key=st.secrets["GOOGLE_API_KEY"],
        youtube_api_key=st.secrets["YOUTUBE_API_KEY"]
    )

# --- Main App Interface ---

st.set_page_config(page_title="Future-Forward Career Planner", page_icon="🚀", layout="wide")
st.title("🚀 Future-Forward Career Planner")
st.markdown("Enter a career domain to get a 5-10 year forecast and a personalized learning path generated by AI.")

# Load the agent
agent = load_agent()

# Create two columns for a cleaner layout
col1, col2 = st.columns(2)

with col1:
    target_domain = st.text_input(
        "Enter a career domain you're interested in:",
        placeholder="e.g., AI in Healthcare, Renewable Energy"
    )

with col2:
    user_learning_style = st.selectbox(
        "Choose your preferred learning style:",
        ("visual", "reading", "practical"),
        format_func=lambda x: f"{x.capitalize()} (e.g., {'Videos' if x == 'visual' else ('Articles' if x == 'reading' else 'Projects')})"
    )

# The "Generate" button
if st.button("✨ Generate My Path", type="primary", use_container_width=True):
    if not target_domain:
        st.warning("Please enter a career domain.")
    else:
        try:
            # --- Step 1: Perform Domain Analysis ---
            with st.spinner(f"🧠 Analyzing the future of '{target_domain}'..."):
                analysis_result = agent.get_domain_analysis(target_domain)

            if not analysis_result.emerging_roles:
                st.warning("No emerging roles were identified for this domain. Cannot generate a learning path.")
            else:
                # --- Step 2: Generate and Process the Learning Path ---
                skills_to_learn = analysis_result.emerging_roles[0].required_skills
                with st.spinner(f"📚 Generating a '{user_learning_style}-only' learning path..."):
                    learning_path_result = agent.get_learning_path(target_domain, skills_to_learn, user_learning_style)

                with st.spinner("🛠️ Finding the best online resources for you..."):
                    for step in learning_path_result.path:
                        if step.type == "video":
                            step.content = agent._search_youtube_video(step.content)
                        elif step.type == "reading":
                            step.content = agent._search_for_article(step.content)
                
                # --- Final Display of Results ---
                st.success("Your personalized career plan is ready!")

                st.subheader("1. Domain Analysis", divider="rainbow")
                st.json(analysis_result.model_dump())

                st.subheader("2. Personalized Learning Path", divider="rainbow")
                st.json(learning_path_result.model_dump())

        except ValidationError:
            st.error("🔴 Validation Error: The AI's response did not match the required format. This can happen with very niche domains. Please try a different one.")
        except Exception as e:
            st.error(f"🔴 An unexpected error occurred: {e}")
