#start.py 
import os
import subprocess
import json
import argparse
from tools import update_team

def load_configuration(config_file='start-config.json'):
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        config = {}

    # Set default values if not present in the config
    config.setdefault('run_update_team', True)
    config.setdefault('run_render_agents', True)
    config.setdefault('run_update_content', True)
    config.setdefault('directory', 'agents/new_agent_files')
    config.setdefault('transformation_prompt', 'Add your global transformation prompt here.')
    config.setdefault('cover_photo_instructions', 'Design your cover photo here.')
    config.setdefault('num_agents_additional', 0)
    config.setdefault('fictionalize_option', 'no')
    config.setdefault('clear_json_confirm', 'no')
    config.setdefault('clear_pics_confirm', 'no')
    config.setdefault('social_image_url', 'https://semantic-life.com/static/atat-glyph.png')
    config.setdefault('logo_url', 'https://semantic-life.com/static/logo.png')

    return config

def run_update_team(directory, transformation_prompt, num_agents_additional):
    update_team.update_team(directory, transformation_prompt, num_agents_additional)

def run_render_agents(fictionalize_option, clear_json, clear_pics, new_agent_files_content):
    version_flag = '--version B' if fictionalize_option else '--version A'
    clear_json_arg = '--clear-json' if clear_json else ''
    clear_pics_arg = '--clear-pics' if clear_pics else ''

    command = f'python tools/render_agents.py {version_flag} {clear_json_arg} {clear_pics_arg} --new-agent-files "{new_agent_files_content}"'
    subprocess.run(command, shell=True, check=True)

def update_content():
    config = load_configuration()
    social_image_url = config.get('social_image_url', 'default_social_image_url')
    logo_url = config.get('logo_url', 'default_logo_url')

    # Pass social_image_url and logo_url to update_content.py via command line arguments
    command = f'python tools/update_content.py --social_image_url "{social_image_url}" --logo_url "{logo_url}"'
    subprocess.run(command, shell=True, check=True)

def clear_agents_json(config):
    if config.get('clear_json_confirm', 'no') == 'yes':
        agents_json_path = os.path.join('agents', 'agents.json')
        with open(agents_json_path, 'w') as file:
            json.dump([], file)
        print("agents.json cleared.")

def handle_removed_agents(config):
    directory = config.get('directory', 'agents/new_agent_files')
    new_agent_files_content = config.get('new_agent_files_content', {})

    # Remove files that are not present in the form
    for file in list(new_agent_files_content.keys()):
        if file not in new_agent_files_content:
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Removed {file} as it was not present in the form.")
                # Remove the file from the new_agent_files_content dictionary
                del new_agent_files_content[file]

    # Update the new_agent_files_content dictionary in the config object
    config['new_agent_files_content'] = new_agent_files_content

    # Log the number of remaining agent files
    num_remaining_files = len(new_agent_files_content)
    print(f"After form submission, {num_remaining_files} agent(s) to process.")

def main():
    config = load_configuration()
    print("Starting processes defined in start-config.json...")

    clear_agents_json(config)
    handle_removed_agents(config)

    # Check whether to run specific operations
    if config.get('run_update_team', False):
        directory = config.get('directory', 'agents/new_agent_files')
        transformation_prompt = config['transformation_prompt']
        num_agents_additional = int(config['num_agents_additional'])  # Convert to integer
        run_update_team(directory, transformation_prompt, num_agents_additional)

    if config.get('run_render_agents', False):
        fictionalize_option = config['fictionalize_option'] == "yes"
        clear_json_confirm = config['clear_json_confirm'] == "yes"
        clear_pics_confirm = config['clear_pics_confirm'] == "yes"
        new_agent_files_content = json.dumps(config.get('new_agent_files_content', {}))
        run_render_agents(fictionalize_option, clear_json_confirm, clear_pics_confirm, new_agent_files_content)

    if config.get('run_update_content', False):
        update_content()

    print("All processes completed successfully.")