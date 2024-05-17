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
    version_flag = '--version' if fictionalize_option else ''
    clear_json_arg = '--clear-json' if clear_json else ''
    clear_pics_arg = '--clear-pics' if clear_pics else ''

    command = ['python', 'tools/render_agents.py']
    if version_flag:
        command.append(version_flag)
        command.append('B')
    if clear_json_arg:
        command.append(clear_json_arg)
    if clear_pics_arg:
        command.append(clear_pics_arg)

    command.append('--new-agent-files')
    command.append(json.dumps(new_agent_files_content))

    subprocess.run(command, check=True)

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


def handle_removed_agents(config, upload_folder, selected_agent_files, new_agent_files_content):
    directory = upload_folder

    # Remove files that are not selected by the user
    for file in os.listdir(directory):
        if file.endswith('.txt') and file not in selected_agent_files:
            file_path = os.path.join(directory, file)
            os.remove(file_path)
            print(f"Removed {file} as it was not selected by the user.")

    # Update the selected agent files based on the form data
    for file in selected_agent_files:
        if file in new_agent_files_content:
            content = new_agent_files_content[file]
            file_path = os.path.join(directory, file)
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Updated {file} based on the form data.")

    # Log the number of selected agent files
    num_selected_files = len(selected_agent_files)
    print(f"After form submission, {num_selected_files} agent(s) selected for processing.")

def main(config, upload_folder, selected_agent_files, new_agent_files_content):
    config = load_configuration()
    print("Starting processes defined in start-config.json...")

    clear_agents_json(config)

    # Get the content of the selected agent files
    selected_agent_files_content = {file: new_agent_files_content[file] for file in selected_agent_files if file in new_agent_files_content}
    print(f"Selected Agent Files: {selected_agent_files}")
    print(f"Selected Agent Files Content: {selected_agent_files_content}")

    handle_removed_agents(config, upload_folder, selected_agent_files, new_agent_files_content)

    # Check whether to run specific operations
    if config.get('run_update_team', False):
        directory = config.get('directory', 'agents/new_agent_files')
        transformation_prompt = config['transformation_prompt']
        num_agents_additional = int(config['num_agents_additional'])
        run_update_team(directory, transformation_prompt, num_agents_additional)

    if config.get('run_render_agents', False):
        fictionalize_option = config['fictionalize_option'] == "yes"
        clear_json_confirm = config['clear_json_confirm'] == "yes"
        clear_pics_confirm = config['clear_pics_confirm'] == "yes"
        new_agent_files_content = json.dumps(selected_agent_files_content)
        run_render_agents(fictionalize_option, clear_json_confirm, clear_pics_confirm, new_agent_files_content)

    if config.get('run_update_content', False):
        update_content()

    print("All processes completed successfully.")