import subprocess
import logging
import os
import traceback
import shutil
import sys
import json

class AutomateDummyAppCreation:
    def __init__(self, clone_path, dummy_version, plugin_version):
        self.clone_path = clone_path
        self.dummy_version = dummy_version
        self.plugin_version = plugin_version
        
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("automate_packet_capture_app_creation.log"),  # Log to file
                logging.StreamHandler()  # Log to console
            ]
        )

    def build_and_package_dummy(self):
        """Builds dummy using PyInstaller, moves the executable, and creates a tarball."""
        dummy_path = os.path.abspath(os.path.join(os.getcwd(), "..", "dummy"))
        dist_path = os.path.join(dummy_path, "dist")
        build_path = os.path.abspath(os.path.join(os.getcwd(), "build"))
        final_dest = os.path.join(build_path, "dummy", "dummy")
        tarball_name = f"dummy-{self.dummy_version}.tar.gz"
        tarball_path = os.path.join(build_path, tarball_name)

        if not os.path.exists(dummy_path):
            logging.error(f"Directory {dummy_path} does not exist.")
            return
        
        try:
            # Step 1: Build the executable using PyInstaller
            logging.info(f"Navigating to {dummy_path} and running PyInstaller...")
            subprocess.run("pyinstaller --onefile dummy.py", shell=True, check=True, cwd=dummy_path)
            
            # Step 2: Ensure the destination folder structure exists
            if os.path.exists(build_path):
                shutil.rmtree(build_path)
            os.makedirs(final_dest, exist_ok=True)

            # Step 3: Move the executable to the final destination
            executable_dummy = os.path.join(dist_path, "dummy")  # Output from PyInstaller
            shutil.move(executable_dummy, final_dest)
            logging.info(f"Moved executable to {final_dest}")

            # Step 4: Create the tarball
            subprocess.run(f"tar -czvf {tarball_name} dummy", shell=True, check=True, cwd=build_path)
            logging.info(f"Created tarball: {tarball_path}")

        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {e}")
        except Exception as e:
            logging.error(f"Error occurred: {e}")


    def run_command(self, command, cwd=None):
        """Runs a shell command and logs output."""
        try:
            logging.info(f"Running command: {command}")
            result = subprocess.run(command, shell=True, check=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            logging.info(f"Output: {result.stdout}")
            logging.info(f"Error: {result.stderr}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {e}")
            logging.error(f"Output: {e.stdout}")
            logging.error(f"Error: {e.stderr}")
            raise

    def update_meta_json(self):
        """Updates version and settings['plugins']['version'] in meta.json."""
        meta_json_path = os.path.join(self.clone_path, "dummy_plugin", "meta.json")
        try:
            with open(meta_json_path, "r") as file:
                meta_data = json.load(file)
            meta_data["version"] = self.plugin_version
            for plugin in meta_data.get("settings", {}).get("plugins", []):
                plugin["version"] = self.dummy_version
            with open(meta_json_path, "w") as file:
                json.dump(meta_data, file, indent=4)
            logging.info(f"Updated meta.json with plugin version {self.plugin_version} and repo app version {self.dummy_version}")
        except Exception as e:
            logging.error(f"Failed to update meta.json: {e}")
            raise

    def invoke_plugin_package_mgr(self):
        """Invokes plugin_package_mgr.py with the given plugin_version."""
        self.run_command(f"python3 plugin_creation_scripts/plugin_package_mgr.py {self.plugin_version}")

    def update_create_application_json(self):
        """Updates create_application.json with the new file paths and versions."""
        create_app_json_path = os.path.join("plugin_creation_scripts/operations/create_application.json")
        try:
            with open(create_app_json_path, "r") as file:
                app_data = json.load(file)
            app_data["pluginPackageRefDetails"][0]["file_path"] = f"../dummy_plugin@{self.plugin_version}.rp"
            app_data["appPackageRefDetails"]["version"] = self.dummy_version
            app_data["appPackageRefDetails"]["file_path"] = f"../dummy-{self.dummy_version}.tar.gz"
            app_data["version"] = self.dummy_version
            with open(create_app_json_path, "w") as file:
                json.dump(app_data, file, indent=4)
            logging.info(f"Updated create_application.json with plugin version {self.plugin_version} and dummy app version {self.dummy_version}")
        except Exception as e:
            logging.error(f"Failed to update create_application.json: {e}")
            raise

    def move_to_build_folder(self):
        """Moves plugin and repo app to build folder"""
        if os.path.exists("../build"):
            shutil.rmtree("../build")
        os.makedirs("../build")
        shutil.move(f"../dummy_plugin@{self.plugin_version}.rp", "../build")
        shutil.move(f"../regal_package/build/dummy-{self.dummy_version}.tar.gz", "../build")
        shutil.copytree(f"../regal_package/plugin_creation_scripts", "../build/plugin_creation_scripts")
        logging.info("Moved repo app and plugin to build folder")


if __name__ == "__main__":
    """"""
    with open("regal_mp.json", "r") as file:
        meta_data  = json.load(file)
        dummy_version = meta_data['applicationVersion']
        plugin_version = meta_data['pluginVersion']

    app_creation_mgr = AutomateDummyAppCreation(
        clone_path="..",
        dummy_version=dummy_version,
        plugin_version=plugin_version
    )
    try:
        ## app_creation_mgr.clone_and_checkout()
        app_creation_mgr.build_and_package_dummy()
        app_creation_mgr.update_meta_json()
        app_creation_mgr.invoke_plugin_package_mgr()
        app_creation_mgr.update_create_application_json()
        app_creation_mgr.move_to_build_folder()
        ## app_creation_mgr.invoke_cloud_mp_cli_create_application()
        logging.info("Script completed successfully.")
    except Exception as e:
        logging.error(f"Script failed: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
