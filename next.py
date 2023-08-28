import json
import shutil


class NextAgent:

  def __init__(self, file_path="tasks.json"):
    self.file_path = file_path

  def load_tasks(self):
    with open(self.file_path, 'r') as file:
      return json.load(file)

  def save_tasks(self, tasks):
    backup_path = f"{self.file_path}.bak"
    shutil.copy(self.file_path, backup_path)
    with open(self.file_path, 'w') as file:
      json.dump(tasks, file)

  def append_object(self, project_name, object_name):
    tasks = self.load_tasks()
    for project in tasks["projects"]:
      if project["name"] == project_name:
        project["objects"].append(object_name)
        self.save_tasks(tasks)
        return True
    return False
