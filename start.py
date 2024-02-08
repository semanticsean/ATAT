import os
import subprocess
import openai
from tools import update_team  # Ensure this import path is correct based on your project structure

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_user_for_input(prompt):
    return input(prompt + "\n")

def run_update_team(directory, transformation_prompt, num_agents_additional):
    # Directly call the updated 'update_team' function with all necessary arguments
    update_team.update_team(directory, transformation_prompt, num_agents_additional)

def run_render_agents(fictionalize_option):
    # Call render_agents.py with the fictionalize option
    subprocess.call(['python', 'tools/render_agents.py', fictionalize_option])

def update_content():
    # Call update_content.py script
    subprocess.call(['python', 'tools/update_content.py'])

def main():
    print("Starting the agent orchestration process...")

    # Asking user for inputs
    directory = ask_user_for_input("Enter the directory of agent files (default '../agents/new_agent_files')") or "../agents/new_agent_files"
    transformation_prompt = ask_user_for_input("Enter your transformation prompt (e.g., 'make all agents work at an ad agency in London')")
    num_agents_additional = int(ask_user_for_input("How many additional agents to create?"))

    # Update team based on user input
    run_update_team(directory, transformation_prompt, num_agents_additional)

    # Ask if agents should be fictionalized and run render_agents with the option
    fictionalize_option = ask_user_for_input("Do you want to fictionalize agents? (yes/no)") == "yes"
    fictionalize_option_str = "fictionalize" if fictionalize_option else "nofictionalize"
    run_render_agents(fictionalize_option_str)

    # Update website content and banners
    update_content()

    print("All processes completed successfully.")

if __name__ == "__main__":
    main()
