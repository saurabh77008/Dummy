import os
import json
import shutil
import tarfile
import re
import sys
import importlib.util
from plugin_package_validator import PluginPackageValidator

class PluginManager:
    def __init__(self, base_path, dest_path):
        self.base_path = base_path
        self.dest_path = dest_path
        self.meta_path = os.path.join(self.base_path, "meta.json")
        self.meta_data = None
        self.plugin_resource_validator = PluginPackageValidator(base_path)
        self.playbook_content = """
---
  - hosts: "{{host}}"
    gather_facts: false
    roles:
      #- {role: set-rps, tags: ['rps'] }
    """

    def validate_meta_json(self):
        # Validate meta.json file
        if not os.path.exists(self.meta_path):
            raise FileNotFoundError(f"meta.json not found at {self.meta_path}")

        with open(self.meta_path, 'r') as meta_file:
            self.meta_data = json.load(meta_file)

        # Validate fields in meta.json
        required_fields = ["pluginName", "version", "type", "settings"]
        for field in required_fields:
            if field not in self.meta_data:
                raise ValueError(f"Field '{field}' not found in meta.json")

        #validate pluginName
        pluginName = self.meta_data["pluginName"]
        if "@" in pluginName:
            raise ValueError("Plugin name cannot contain '@' character.")
    
        # Validate version format
        version = self.meta_data["version"]
        pattern = re.compile(r"^\d+(\.\d+)*((a|b|rc)\d+)?(\.post\d+)?(\.dev\d+)?$")
        if not pattern.match(version):
            raise ValueError(f"Invalid version format: {version}. Must follow PEP 440.")

        # Validate settings["plugins"]
        plugins = self.meta_data["settings"].get("plugins", [])

        # Track seen combinations of plugin name and type
        seen_combinations = set()

        if not plugins:
            raise ValueError("At least one set of data under 'plugins' key is required in meta.json")

        for plugin in plugins:
            required_plugin_fields = ["name", "version", "className"]
            for field in required_plugin_fields:
                if field not in plugin:
                    raise ValueError(f"Field '{field}' not found in plugin settings")

            # Check for duplicate plugin name and type combinations
            plugin_combination = (plugin["name"], plugin.get("type", ""))
            if plugin_combination in seen_combinations:
                raise ValueError(f"Duplicate plugin name '{plugin['name']}' and type '{plugin.get('type', '')}' found.")
            seen_combinations.add(plugin_combination)

    def validate_dependencies(self):
        dependencies = self.meta_data.get("dependencies", [])

        seen_dependencies = set()
        unique_dependencies = set()

        for dep in dependencies:
            dep_name = dep.get("name")
            dep_type = dep.get("type")

            if dep_name is None or dep_type is None:
                raise ValueError("Dependency 'name' and 'type' must be specified and not null.")

            dep_key = (dep_name, dep_type)

            if dep_key in unique_dependencies:
                raise ValueError(f"Warning: Duplicate dependency '{dep_name}' with type '{dep_type}' found in plugin '{self.meta_data.get('pluginName')}'.")
            else:
                unique_dependencies.add(dep_key)

            if dep_key in seen_dependencies:
                raise ValueError(f"Warning: Duplicate dependency '{dep_name}' with type '{dep_type}' found.")
            else:
                seen_dependencies.add(dep_key)

            if dep.get("minVersion") is not None or dep.get("maxVersion") is not None:
                print(f"Validating version constraints for dependency '{dep_name}': "
                      f"minVersion={dep.get('minVersion')}, maxVersion={dep.get('maxVersion')}")

    # def validate_class_names(self):
    #     seen_class_names = set()
    #     plugins = self.meta_data["settings"].get("plugins", [])

    #     for plugin in plugins:
    #         class_name = plugin["className"]
    #         python_file_path = os.path.join(self.base_path, *class_name.split('.')) + ".py"
    #         print(f"Checking for {class_name}.py at {python_file_path}")
    #         print(f"Exists: {os.path.exists(python_file_path)}")  # Add this line

    #         if not os.path.exists(python_file_path):
    #             raise FileNotFoundError(f"Python file {class_name}.py not found in {self.base_path}")

    #         # Check for duplicate class names
    #         if class_name in seen_class_names:
    #             raise ValueError(f"Duplicate class name '{class_name}' found in meta.json.")
    #         seen_class_names.add(class_name)
    
    def ansible_structure_validation(self, plugin_dir):
        
        ansible_dir = os.path.join(plugin_dir, "ansible")
        if not os.path.exists(ansible_dir):
            os.makedirs(ansible_dir)
        playbooks_dir = os.path.join(ansible_dir, "playbooks")
        if not os.path.exists(playbooks_dir):
            os.makedirs(playbooks_dir)
        commands_file_path = os.path.join(playbooks_dir, "commands.yml")
        if not os.path.exists(commands_file_path):
            with open(commands_file_path, 'w') as commands_file:
                commands_file.write(self.playbook_content)
        roles_dir = os.path.join(playbooks_dir, "roles")
        if not os.path.exists(roles_dir):
            os.makedirs(roles_dir)
        

    def create_plugin_structure(self):
        pluginName = self.meta_data["pluginName"]
        version = self.meta_data["version"]
        abs_dest_path = self.dest_path
        # if plugin name dir is already there in the self.dest path then log the message "change the destination path, same dir exist with the plugin name dir"
        plugin_dir = os.path.join(self.dest_path, pluginName)
        if os.path.exists(plugin_dir) and os.path.isdir(plugin_dir):
            shutil.rmtree(plugin_dir)
        plugin_dir = os.path.join(self.dest_path, pluginName, version)
        os.makedirs(plugin_dir, exist_ok=True)
        
        self.ansible_structure_validation(plugin_dir)


        # Copy plugin files to the new structure
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                src_path = os.path.join(root, file)
                dest_rel_path = os.path.relpath(src_path, self.base_path)
                dest_path = os.path.join(plugin_dir, dest_rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_path, dest_path)

        # Create meta.json in the new structure
#        meta_data = {
#            "pluginName": pluginName,
#            "version": version,
#            "type": "custom",
#            "settings": {
#                "plugins": []
#            }
#        }
#
#        meta_path = os.path.join(plugin_dir, "meta.json")
#        with open(meta_path, 'w') as meta_file:
#            json.dump(meta_data, meta_file, indent=2)

        # Create tar.gz file
        tar_file_name = f"{pluginName}@{version}.tar.gz"
        tar_file_path = os.path.join(abs_dest_path, tar_file_name)

        plugin_path = self.dest_path + "/" + pluginName
        with tarfile.open(tar_file_path, 'w:gz') as tar:
            tar.add(plugin_path, arcname=pluginName)

        # Rename tar.gz file to .rp
        rp_file_path = os.path.join(abs_dest_path, f"{pluginName}@{version}.rp")
        print("rp_file_path:" + rp_file_path)
        os.rename(tar_file_path, rp_file_path)
        # move plugin outside, to log-collector-product
        _plugin_path = os.path.join("..", f"{pluginName}@{version}.rp")
        if os.path.exists(_plugin_path):
            os.remove(_plugin_path)
        shutil.move(rp_file_path, os.path.join(os.getcwd(), ".."))
        # shutil.rmtree(plugin_dir)

    def validate_dest_path(self):

        if not os.path.exists(self.dest_path):
            print(f"Destination path {self.dest_path} does not exist.")
            exit()

    def validate_base_path(self):
        if not os.path.exists(self.base_path):
            print(f"Base path {self.base_path} does not exist.")
            exit()

    def run_plugin_manager(self):
        self.validate_base_path()
        self.validate_dest_path()
        self.validate_meta_json()
        self.validate_dependencies()
        #self.validate_class_names()
        self.plugin_resource_validator.validate()
        self.create_plugin_structure()


if __name__ == "__main__":
    base_path = "../dummy_plugin"
    dest_path = "../dummy_plugin"

    
    plugin_manager = PluginManager(base_path, dest_path)
    plugin_manager.run_plugin_manager()

