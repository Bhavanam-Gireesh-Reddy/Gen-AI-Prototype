import os
from dotenv import load_dotenv
from typing import List

# LangChain & Pydantic Imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field, ValidationError

# Imports for Search Tools
from googleapiclient.discovery import build
from googlesearch import search

# --- 1. Define Data Schemas (Pydantic Models) ---

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


# --- 2. The Career Counselor Agent ---

class CareerCounselorAgent:
    """An AI agent that provides career analysis and learning paths using external tools."""

    def __init__(self):
        """Initializes the agent, AI model, processing chains, and search tools."""
        print("🤖 Initializing Career Counselor Agent...")
        
        load_dotenv()
        if "GOOGLE_API_KEY" not in os.environ or "YOUTUBE_API_KEY" not in os.environ:
            raise ValueError("🔴 CRITICAL: GOOGLE_API_KEY and YOUTUBE_API_KEY must be set in a .env file.")

        self.model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
        self.youtube_service = build('youtube', 'v3', developerKey=os.environ["YOUTUBE_API_KEY"])
        
        self._create_chains()
        print("✅ Agent is ready.")

    def _search_youtube_video(self, query: str) -> str:
        """Searches YouTube for a video and returns the top result's URL."""
        try:
            search_response = self.youtube_service.search().list(
                q=f"{query} tutorial",
                part='snippet',
                maxResults=1,
                type='video',
                videoDefinition='high'
            ).execute()
            
            if search_response.get("items"):
                video_id = search_response['items'][0]['id']['videoId']
                return f"https://www.youtube.com/watch?v={video_id}"
            return "No relevant video found."
        except Exception as e:
            print(f"   ⚠️ YouTube API Error: {e}")
            return "Could not fetch video link due to an API error."

    def _search_for_article(self, query: str) -> str:
        """Performs a Google search and returns the top result URL."""
        try:
            search_results = search(f"{query} article tutorial", num_results=1, lang="en")
            top_result = next(search_results, "No relevant article found.")
            return top_result
        except Exception as e:
            print(f"   ⚠️ Web Search Error: {e}")
            return "Could not fetch article link due to a search error."

    def _create_chains(self):
        """Builds the LangChain Expression Language (LCEL) chains."""
        analysis_parser = PydanticOutputParser(pydantic_object=DomainAnalysis)
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a futuristic career analyst... Respond with the requested JSON object..."),
            ("human", "Analyze the career domain: '{domain}'.\n\n{format_instructions}")
        ]).partial(format_instructions=analysis_parser.get_format_instructions())
        self.analysis_chain = analysis_prompt | self.model | analysis_parser

        path_parser = PydanticOutputParser(pydantic_object=LearningPath)
        path_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                (
                    "You are an expert curriculum developer... Your task is to create a personalized learning path... strictly following the user's preferred learning style. "
                    "- If the learning_style is 'visual', you MUST generate a path containing ONLY steps with the type 'video'. "
                    "- If the learning_style is 'reading', you MUST generate a path containing ONLY steps with the type 'reading'. "
                    "- If the learning_style is 'practical', you MUST generate a path containing ONLY steps with the type 'project'. "
                    "Do not mix types..."
                ),
            ),
            ("human", "Create a learning path for the '{domain}' domain, focusing on these skills: {key_skills}. The user's preferred learning style is '{learning_style}'.\n\n{format_instructions}")
        ]).partial(format_instructions=path_parser.get_format_instructions())
        
        self.learning_path_chain = path_prompt | self.model | path_parser

    def get_domain_analysis(self, domain: str) -> DomainAnalysis:
        print(f"\n🧠 Analyzing the future of '{domain}'...")
        return self.analysis_chain.invoke({"domain": domain})

    def get_learning_path(self, domain: str, skills: List[str], style: str) -> LearningPath:
        print(f"\n📚 Generating a '{style}-only' learning path structure...")
        return self.learning_path_chain.invoke({
            "domain": domain,
            "key_skills": ", ".join(skills),
            "learning_style": style
        })

    def run(self):
        """Main execution loop for the agent to interact with the user."""
        print("\n" + "="*50)
        print("🚀 Welcome to the Future-Forward Career Planner 🚀")
        print("="*50)

        target_domain = input("\nEnter a career domain you're interested in (e.g., AI in Healthcare): \n> ")
        
        print("\nWhat is your preferred learning style? (The path will ONLY contain this type)")
        print("  1. Visual (Video tutorials)")
        print("  2. Reading (Articles and guides)")
        print("  3. Practical (Project-based tasks)")
        
        style_map = {"1": "visual", "2": "reading", "3": "practical"}
        while (style_choice := input("Choose a number (1-3): \n> ")) not in style_map:
            print("Invalid choice. Please enter a number from 1 to 3.")
        user_learning_style = style_map[style_choice]

        try:
            # --- Step 1: Perform Domain Analysis ---
            analysis_result = self.get_domain_analysis(target_domain)

            if not analysis_result.emerging_roles:
                 print("\n⚠️ No emerging roles were identified. Cannot generate a learning path.")
                 return

            # --- Step 2: Generate and Process the Learning Path ---
            skills_to_learn = analysis_result.emerging_roles[0].required_skills
            print(f"\n🎯 Identified key skills: {skills_to_learn}")
            
            learning_path_result = self.get_learning_path(target_domain, skills_to_learn, user_learning_style)
            
            print("\n🛠️ Finding the best online resources for you...")
            for step in learning_path_result.path:
                if step.type == "video":
                    print(f"   -> Searching for a video about: '{step.content}'")
                    step.content = self._search_youtube_video(step.content)
                elif step.type == "reading":
                    print(f"   -> Searching for an article about: '{step.content}'")
                    step.content = self._search_for_article(step.content)

            # --- MODIFICATION: Final, separated printing of the two outputs ---
            print("\n\n" + "="*25 + " RESULTS " + "="*25)

            # Output 1: Domain Analysis
            print("\n\n--- 1. DOMAIN ANALYSIS ---")
            print(analysis_result.model_dump_json(indent=2))

            # Output 2: Learning Path
            print("\n\n--- 2. PERSONALIZED LEARNING PATH ---")
            print(learning_path_result.model_dump_json(indent=2))
            
            print("\n" + "="*59)


        except ValidationError:
            print("\n🔴 Validation Error: The AI's response did not match the required format. This can happen with very niche domains. Please try a different one.")
        except Exception as e:
            print(f"\n🔴 An unexpected error occurred: {e}")


# --- 3. Run the Agent ---
if __name__ == "__main__":
    agent = CareerCounselorAgent()
    agent.run()
