# Plugin for regal agents to be integrated in marketplace.
import os
import traceback
import time
import re
from datetime import timedelta

# regal libraries
from Regal.apps.appbase import AppBase
from regal_lib.corelib.constants import Constants
import regal_lib.corelib.custom_exception as exception
from regal_lib.corelib.common_utility import Utility


class InstallFailed(Exception):
    def __init__(self, inst, error_msg):
        Exception.__init__(self)
        self._inst = inst
        self._error_msg = error_msg

    def __str__(self):
        return f"Failed to install {self._inst} : {self._error_msg}"

class UninstallFailed(Exception):
    def __init__(self, inst, error_msg):
        Exception.__init__(self)
        self._inst = inst
        self._error_msg = error_msg

    def __str__(self): 
        return f"Failed to uninstall {self._inst} : {self._error_msg}"



class DummyPlugin(AppBase):
    
    def __init__(self, service_store_obj, name, version):
        super().__init__(service_store_obj, name, version)
        self.service_store_obj = service_store_obj
        self._log = self.service_store_obj.get_log_mgr_obj().get_logger(self.__class__.__name__)
        self.app_found_version = None
        self._internal_name = None
        self._internal_version = None
        self._update_app_details()
        self.AGENT_DIR_NAME = "Regal"

    def _update_app_details(self):
        self._internal_name = self._name
        self._internal_version = self._version
   
    def _update_persistant_data(self, infra_ref, key, value):
        self.update_persist_data(infra_ref, key, value, self._sw_type)
    
    def get_configuration_from_topology(self, key):
        """
        Method to fetch the configuration from topology

        Returns:
            str: value of the key
        """
        return self.get_node().get_node_info().get("configurations", {}).get(key)

    # def validate_pcap_agents_config(self, pcap_agents):
    #     self._log.debug(">")
    #     required_keys = {"app_name", "path", "pcap_save_path", "port", "service_name"}
    #     seen_values = {"app_name": set(), "port": set(), "service_name": set(), "path": set(), "pcap_save_path": set()}

    #     for idx, agent in enumerate(pcap_agents):
    #         # Check if all required keys are present
    #         if not required_keys.issubset(agent.keys()):
    #             missing_keys = required_keys - agent.keys()
    #             err_mg =  f"Error: Missing keys {missing_keys} in agent at index {idx}"
    #             raise Exception(err_mg)

    #         if not isinstance(agent["port"], int):
    #             err_msg =  f"Error: Port value '{agent['port']}' is not an integer in agent at index {idx}"
    #             raise Exception(err_msg)

    #         # Check for duplicate values
    #         for key in seen_values.keys():
    #             value = agent[key]
    #             if value in seen_values[key]:
    #                 err_msg =  f"Error: Duplicate value '{value}' found for key '{key}' in agent at index {idx}"
    #                 self._log.debug("<")
    #                 raise Exception(err_msg)
    #             seen_values[key].add(value)

    #     self._log.debug("<")

    def transform_config(self, config):
        self._log.debug(">")
        if isinstance(config, list):
            self._log.debug("<")
            return config
        elif not isinstance(config, dict):
            self._log.debug("<")
            raise ValueError("Input configuration is not a dictionary and not list")
        
        self._log.info(f"Transforming dict config : {config}"
                        f" to list of dictionaries")
        agent_list = []
        for app_name, value in config.items():        
            agent = {
                    "app_name": app_name,
                    "path": value.get("path"),
                    "pcap_save_path": value.get("pcap_save_path"),
                    "port": int(value.get("port")) if value.get("port") else None,
                    "service_name": value.get("service_name"),
                    "pcap_log_file_size": int(value.get("pcap_log_file_size", 100)),
                }
            agent_list.append(agent)
        self._log.debug(f"Transformed config: {agent_list}")  
        self._log.debug("<")    
        return agent_list

    def app_match(self, hosts):
        try:
            self._log.debug(">")
            node_ip = self.get_node().get_management_ip()
            self._log.debug(f"Executing app_match for app: {self._name} and repo: {self.get_repo_path()} on node: {node_ip}")
            self.service_store_obj.get_login_session_mgr_obj().create_session(self.get_node(), 1, "app_match_session")
            
            infra_ref = self.service_store_obj.get_current_infra_profile().get_db_infra_profile_obj()
            self._update_persistant_data(infra_ref, "app_found_version", None)

            agent_config = self.get_configuration_from_topology("pcap-agent")
            if agent_config is None:
                self._log.debug("<")
                raise Exception("pcap-agent application configuration not found in the topology configuration")
            
            agent_config = self.transform_config(agent_config)
            self.validate_pcap_agents_config(agent_config)
            validation_count = 0

            # Iterate through agent configurations
            for app_config in agent_config:
                path = app_config['path']
                service_name = app_config['service_name']

                if not self._is_pcap_agent_present(path):
                    self._log.debug("<")
                    return False

                pcap_agent_version = self._get_pcap_agent_version(path)
                if not pcap_agent_version or pcap_agent_version != self._version:
                    self._log.debug(f"pcap-agent version mismatch: {pcap_agent_version} != {self._version}")
                    return False

                if not self._validate_and_restart_service(service_name, path, hosts):
                    self._log.debug("<")
                    return False

                validation_count += 1

            self._log.info(f"Validation count for pcap-agent: {validation_count}")
            self._log.debug("<")
            return validation_count == len(agent_config)

        except exception.ExecuteShellFailed as ex:
            self._log.error(f"App_match failed, error: {str(ex)}")
            self._log.error(f"App_match failed, traceback: {traceback.format_exc()}")
            self._log.debug("<")
            return False
        finally:
            self.service_store_obj.get_login_session_mgr_obj().close_session("app_match_session", 1)

    # Helper methods
    def _is_pcap_agent_present(self, path):
        cmd = f"ls {path}/ 2> /dev/null | grep pcap-agent | grep -v tar.gz | wc -l"
        result = self.service_store_obj.get_login_session_mgr_obj().execute_cmd_and_get_output(cmd, 'app_match_session', time_out=Constants.PEXPECT_TIMER)
        return int(result.strip()) > 0

    def _get_pcap_agent_version(self, path):
        version_cmd = f"grep PCAP_AGENT_VERSION {path}/pcap-agent/pcap_agent/config.json | cut -d'\"' -f4"
        version = self.service_store_obj.get_login_session_mgr_obj().execute_cmd_and_get_output(
            version_cmd, 'app_match_session', time_out=Constants.PEXPECT_TIMER).strip()
        self._update_persistant_data(self.service_store_obj.get_current_infra_profile().get_db_infra_profile_obj(),
                                      "app_found_version", version)
        return version

    def _validate_and_restart_service(self, service_name, path, hosts):
        self._log.debug(">")
        status_cmd = f"systemctl status {service_name}.service 2> /dev/null | grep Active"
        self._log.info(f"pcap-status check cmd: {status_cmd}")

        pcap_service_status = self.service_store_obj.get_login_session_mgr_obj().execute_cmd_and_get_output(
            status_cmd, 'app_match_session', time_out=Constants.PEXPECT_TIMER
        )

        self._log.debug(f"pcap-service-status: {pcap_service_status}")
        if "pcap-agent" in path and 'running' in pcap_service_status.strip().lower():
            runtime_match = re.search(r';\s*(.*?)\s+ago', pcap_service_status)
            if runtime_match and self.check_running_time(runtime_match):
                restart_cmd = f"systemctl restart {service_name}"
                self.service_store_obj.get_login_session_mgr_obj().execute_cmd_and_get_output(
                    restart_cmd, 'app_match_session', time_out=Constants.PEXPECT_TIMER
                )
                time.sleep(2)
                pcap_service_status = self.service_store_obj.get_login_session_mgr_obj().execute_cmd_and_get_output(
                    status_cmd, 'app_match_session', time_out=Constants.PEXPECT_TIMER
                )
                self._log.debug(f"pcap-service-status_1: {pcap_service_status}")
                if "running" in pcap_service_status.strip().lower():
                    self._log.debug(f"pcap-agent successfully installed on node - {hosts}")
                    return True
            else:
                self._log.debug(f"pcap-agent successfully installed on node - {hosts}")
                return True

        self._log.warning(f"pcap-agent_{self._internal_version} is not installed or not running.")
        return False


    def install_correct_version(self):
        try:
            self._log.debug(">")
            self.product_path = os.path.dirname(os.path.abspath(__file__))
            infra_ref = self.service_store_obj.get_current_infra_profile().get_db_infra_profile_obj()
            node_ip = self.get_node().get_management_ip()
             
            app_found_version = self.get_persist_data(
                        infra_ref, "app_found_version", self._sw_type)


            self.uninstall_version_one()
            if app_found_version is None:
                self._log.info(f"{self._internal_name} is not found, perfoming fresh installation on node: {node_ip}")
                self.install()
                self._log.info("<")
                return True

            elif app_found_version != self._version:
                self._log.debug(f"{self._internal_name}, version found: {app_found_version}: version required: {self._version}. performing uninstallation")
                self.uninstall()
                self.install()
                self._log.debug("<")
                return True

            else:
                self._log.info(f"{self._internal_name} is already installed but version configured is not matching on node - {node_ip}")
                self.uninstall()
                self.install()
                self._log.debug("<")
                return True

        except exception.RegalException as ex:
            self._log.error(f"Correction failed on node {node_ip} - {ex}")
            self._log.error(f"Traceback : {traceback.format_exc()}")
            return False

    def get_pcap_size_and_time_limit(self, app_config, app):
        self._log.debug(">")
        size_limit = self.get_app_config(app_config, "max_pcap_size_limit", app, True)
        time_limit = self.get_app_config(app_config, "max_pcap_time_limit", app, True)
        if not size_limit:
            size_limit = 200
    
        if not time_limit:
            time_limit = 20

        if not isinstance(size_limit, int):
            raise Exception("Invalid input: 'max_pcap_size_limit' should be an integer.")

        if not isinstance(time_limit, int):
            raise Exception("Invalid input: 'max_pcap_time_limit' should be an integer.")

        if time_limit <= 0:
            raise Exception("max_pcap_time_limit must be greater than zero.")

        if size_limit > 500 or size_limit <= 0:
            raise Exception("max_pcap_size_limit must be between 1 and 500.")
        self._log.debug("<")
        return size_limit, time_limit


    def install(self):
        try:
            self._log.debug(">")
            host = self.get_node().get_management_ip()
            self._log.debug(f"Installing {self._name} from repo {self.get_repo_path()} on node {host}")
            agent_config = self.get_configuration_from_topology("pcap-agent")
            agent_config = self.transform_config(agent_config)
            if agent_config is None:
                raise Exception("pcap-agent application configuration not found in the topology configurion")

            for app_config in agent_config:
                port = app_config["port"]
                service_name = app_config["service_name"] 
                path = app_config["path"]
                pcap_save_path = app_config["pcap_save_path"]
                extra_vars = {
                    "host": host,
                    "pcap_agent_tarball_path": self.get_repo_path(),
                    "path" : path,
                    "agent_port": int(port),
                    "service_name": service_name,
                    "agent_version": self._version,
                    "max_pcap_size_limit": "",
                    "max_pcap_time_limit": "",
                    "pcap_save_path": pcap_save_path,
                    "pcap_log_file_size": app_config.get("pcap_log_file_size", 100)      
                }
                
                tags = {"install-pcap-agent"}

                app_info = self.get_app_info()
            

                if app_info and "appPluginInfraMappedId" in app_info and app_info["appPluginInfraMappedId"] is not None:
                    self._node.run_playbook_for_plugin("Application", self._name, extra_vars, tags, inventory_id = None, cred_id = None)
                else:
                    self.get_deployment_mgr_client_obj().run_playbook(self.AGENT_DIR_NAME, extra_vars, tags)

                self._log.info(f"Successfully installed the application {self._name} on node - {host}")

        except Exception as ex:
            self._log.error(f"Installation failed on node {host}, error: {ex}")
            self._log.error(f"Traceback: {traceback.format_exc()}")
            raise InstallFailed("Agent", str(ex))
    
    def uninstall(self):
        try:
            self._log.debug(">")
            host = self.get_node().get_management_ip()
            self._log.debug(f"Uninstalling {self._name} from node {host}")

            try:
                agent_config = self.get_configuration_from_topology("pcap-agent")
                agent_config = self.transform_config(agent_config)
                if agent_config is None:
                    raise Exception("pcap-agent application configuration not found in the topology configuration")

                for app_config in agent_config:
                    port = app_config["port"]
                    service_name = app_config["service_name"]
                    path = app_config["path"]
            
                    extra_vars = {
                        "host": host,
                        "path": path,
                        "service_name": service_name,
                        "agent_port" : int(port)
                    }

                    tags = {"uninstall-pcap-agent"}

                    app_info = self.get_app_info()
            
                    if app_info and "appPluginInfraMappedId" in app_info and app_info["appPluginInfraMappedId"] is not None:
                        self._node.run_playbook_for_plugin("Application", self._name, extra_vars, tags, inventory_id = None, cred_id = None)
                    else:
                        self.get_deployment_mgr_client_obj().run_playbook(self.AGENT_DIR_NAME, extra_vars, tags)

                        self._log.info(f"Successfully uninstalled the applicaiton {self._name} on node {host}")
                        
            except Exception as ex:
                self._log.error(f"Unistallation failed on node {host}, error: {ex}")
                self._log.error(f"Traceback: {traceback.format_exc()}")
                raise UninstallFailed("Pcap-Agent", str(ex))
                
            self._log.debug("<")
        
        except Exception as ex:
            self._log.error(f"Uninstalled failed on node {host} - {ex}")
            self._log.error(f"Traceback: {traceback.format_exc()}")
            raise UninstallFailed("Agent", str(ex))

    def get_repo_path(self, package_name = None):
        self._log.debug(">")
        self._log.debug(f"_name: {self._name}, _version: {self._version}")

        try:
            repo_path = self.service_store_obj.get_repo_mgr_client_obj().get_repo_path(self._name, self._version)
            repo_path = os.path.abspath(repo_path)
            self._log.debug(f"Returning repo path: {repo_path}")
            self._log.debug("<")
            return repo_path
        
        except Exception as ex:
            self._log.error(f"Unable to get the repo path for {self._name}, {self._version}")
            self._log.error(f"Traceback : {traceback.format_exc()}")
            self._log.debug("<")
            raise ex


    def check_running_time(self, runtime_match):
        """
        Check if the service runtime exceeds 1 minute by parsing a runtime string.

        Args:
            runtime_match (re.Match): A regex match object containing the runtime string.
        Returns:
            bool: True if runtime exceeds 1 minute, False otherwise or if parsing fails
        """
        try:
            runtime_str = runtime_match.group(1)
            total_seconds = 0
            hour_match = re.search(r'(\d+)h', runtime_str)
            if hour_match:
                total_seconds += int(hour_match.group(1)) * 3600
            min_match = re.search(r'(\d+)min', runtime_str)
            if min_match:
                total_seconds += int(min_match.group(1)) * 60
            sec_match = re.search(r'(\d+)s', runtime_str)
            if sec_match:
                total_seconds += int(sec_match.group(1))
            
            runtime = timedelta(seconds=total_seconds)
            self._log.debug(f"Service runtime: {runtime}")
            return runtime > timedelta(minutes=1)
        except (AttributeError, ValueError) as e:
            self._log.debug(f"Error parsing runtime string: {e}")
            return False

    def get_app_config(self, config: dict, key: str, app: str, ignore_error=False) -> str:
        """
        Method used get the app_config.
        Agrs: 
            config: (dict): app config
            key: str
            app: str: name of the app
        Returns: 
            value: str: the value of the key. 

        Raises Exception: If key not found in the app config. 
        """
        if key not in config:
            if ignore_error:
                return ""
            raise Exception(f"{key} not in found in {app} config.")

        if config[key] == "":
            if ignore_error:
                return ""
            raise Exception(f"{key} is None in the {app} config.")
        return config[key]

    def handle_empty_agent_config(self) -> dict:
        """
        Method used to handle empty agent config.
        Args: 
            None
        Return:
            agent_config: dict: Agent config with single app.
        """
        return {"app1": {'path': '/opt/regal', 'port': 30063, 'service_name': 'pcap-agent'}}

    def uninstall_version_one(self):
        """
        Method Used to uninstall non executable version

        Args:
            None
        Return:
            None
        """

        try: 
            self.service_store_obj.get_login_session_mgr_obj().create_session(self.get_node(), 1, "uninstall-version-one") 
            check_non_executable_cmd = "ls /opt/regal/pcap-agent/pcap_agent 2> /dev/null | grep pcap_agent.py"
            non_executable_info = self.service_store_obj.get_login_session_mgr_obj().execute_cmd_and_get_output(
                check_non_executable_cmd, 'uninstall-version-one', time_out=Constants.PEXPECT_TIMER)

            if non_executable_info != "":
                self._log.debug("pcap-agent_1.0.0 is installed. moving to uninstallation")
                host = self.get_node().get_management_ip()
                try:
                    extra_vars = {
                        "host": host,
                    }

                    tags = {"uninstall-pcap-agent-version-one"}

                    app_info = self.get_app_info()
            
                    if app_info and "appPluginInfraMappedId" in app_info and app_info["appPluginInfraMappedId"] is not None:
                        self._node.run_playbook_for_plugin("Application", self._name, extra_vars, tags, inventory_id = None, cred_id = None)
                    else:
                        self.get_deployment_mgr_client_obj().run_playbook(self.AGENT_DIR_NAME, extra_vars, tags)

                        self._log.info(f"Successfully uninstalled the applicaiton {self._name}:1.0.0 on node {host}")
                        
                except Exception as ex:
                    self._log.error(f"Unistallation failed on node {host}, error: {ex}")
                    self._log.error(f"Traceback: {traceback.format_exc()}")
                    raise UninstallFailed("Pcap-Agent", str(ex))
            else:
                self._log.debug("pcap-agent version 1.0.0 is not installed. skipping uninstallation.")

        finally:
            self.service_store_obj.get_login_session_mgr_obj().close_session("uninstall-version-one", 1)


