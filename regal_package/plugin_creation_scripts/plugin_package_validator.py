import os
import json
import base64
import shutil
import tarfile
import re
import sys
import importlib.util
from plugin_package_constants import Constants as PluginPackageConstants


class TestCases:
    def __init__(self, base_path):
        self.base_path = base_path
        self.config = {
            "testSuites": []
        }
        
    def get_test_suites_info(self):
        test_suites = []
        
        for suite_name in os.listdir(self.base_path):
            suite_path = os.path.join(self.base_path, suite_name)
            if suite_name != "__pycache__" and os.path.isdir(suite_path):
                test_cases = [tc for tc in os.listdir(suite_path) if os.path.isdir(os.path.join(suite_path, tc)) and tc != "__pycache__" and (len(os.listdir(os.path.join(suite_path, tc)))> 0)]
                #print("The length", len(os.listdir(os.path.join(suite_path, tc))))
                init_path = os.path.join(suite_path, '__init__.py')
                description = ""
                if os.path.exists(init_path):
                    spec = importlib.util.spec_from_file_location("module.name", init_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules["module.name"] = module
                    spec.loader.exec_module(module)
                    
                    description = ', '.join(getattr(module, 'description', []))
                if not len(test_cases):
                    continue
                test_suites.append({
                    "description": description,
                    "testCasesCount": len(test_cases),
                    "testSuiteName": suite_name,
                    "testCasesName": test_cases
                })
        
        return test_suites
    
    def get_sample_testcases_description(self):
        description = ""
        init_path = os.path.join(self.base_path, '__init__.py')
        if os.path.exists(init_path):
            spec = importlib.util.spec_from_file_location("module.name", init_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["module.name"] = module
            spec.loader.exec_module(module)
            
            description = getattr(module, 'description', "")
        return description

    def create_tc_config(self):
        test_suites = self.get_test_suites_info()
        description = self.get_sample_testcases_description()
        self.config["testSuites"] = test_suites
        self.config["description"] = description
        with open(os.path.join(self.base_path, PluginPackageConstants.TEST_CASE_CONFIG), "w") as f:
            json.dump(self.config, f, indent=2)

        print(f"{PluginPackageConstants.TEST_CASE_CONFIG} has been created.")

    def get_tc_config(self):
        return self.config
    
    
class PluginPackageValidator:
    def __init__(self, base_path):
        self.base_path = base_path
        self.test_cases = None

    def validate(self):
        try:
            self.validate_max_files()
            self.initialize_test_cases()
            self.validate_solution_stack_details()
            self.validate_topology_details()
            self.validate_infra_profile_details()
            self.validate_test_plan_details()
        except Exception as exc:
            print(str(exc))
            exit(1)
            
    def validate_max_files(self):
        for directory in [PluginPackageConstants.TOPOLOGY, PluginPackageConstants.SOLUTION_STACK, 
                          PluginPackageConstants.INFRAPROFILE, PluginPackageConstants.TEST_PLAN]:
            res, message = self.contains_only_one_file(directory)
            if not res:
                raise ValueError(message)
        
        res, message = self.contains_only_one_folder(PluginPackageConstants.TEST_CASES)
        if not res:
            raise ValueError(message)

    def contains_only_one_file(self, name):
        directory = self.get_path(name)
        if not os.path.isdir(directory):
            return True, f"{name} does not exist."

        contents = os.listdir(directory)
        if len(contents) == 0:
            return False, f"{name} is empty."
        elif len(contents) == 1 and os.path.isfile(os.path.join(directory, contents[0])):
            return True, f"{name} contains only one file."
        return False, f"More than one file is present in {name}."

    def contains_only_one_folder(self, name):
        directory = self.get_path(name)
        if not os.path.exists(directory):
            return True, f"{name} does not exist."

        if not os.path.isdir(directory):
            return False, f"{name} is not a directory."

        contents = [item for item in os.listdir(directory) if item != "__pycache__" and os.path.isdir(os.path.join(directory, item))]

        if len(contents) == 0:
            return True, f"{name} is empty."

        if len(contents) > 1:
            return False, f"{name} contains more than one item."

        if not os.path.isdir(os.path.join(directory, contents[0])):
            return False, f"The item in {name} is not a folder."

        return True, f"{name} contains only one folder: {contents[0]}"

    def get_path(self, name):
        return os.path.join(self.base_path, name)

    def initialize_test_cases(self):
        tc_path = self.get_path(PluginPackageConstants.TEST_CASES)
        if not os.path.exists(tc_path):
            print("Test case dir is not there ")
            return
        self.test_cases = TestCases(self.get_path(PluginPackageConstants.TEST_CASES))
        self.test_cases.create_tc_config()
    
    

        
    def validate_solution_stack_details(self):
        """Method to validate plugin solution stack

        Args:
        """
        solution_stack_file_path = self.get_path(PluginPackageConstants.SOLUTION_STACK)
        if os.path.isdir(solution_stack_file_path):
            for filename in os.listdir(solution_stack_file_path):
                solution_stack_content = self.get_file_content(filename, solution_stack_file_path)
                if not all(field in solution_stack_content for field in PluginPackageConstants.SOLUTION_STACK_REQUIRED_FIELDS):
                    raise ValueError(f"Invalid Solution stack file: {filename}. solutionStackName and solutionStackVersion is required")
                
                optional_fields = ["os", "platform", "applications"]
                if not any(field in solution_stack_content for field in optional_fields):
                    raise ValueError(f"Invalid Solution stack file: {filename}. At least one of os, platform, or applications is required for solution stack")
        
    def validate_topology_details(self):
        """Method to validate plugin topology

        Args:
        """
        topology_file_path = self.get_path(PluginPackageConstants.TOPOLOGY)
        if not os.path.isdir(topology_file_path):
            topology_image_file_path = self.get_path(PluginPackageConstants.TOPOLOGY_IMAGES)
            if os.path.isdir(topology_image_file_path):
                raise ValueError(f"Error: Can not create topology image without topology")
            
        if os.path.isdir(topology_file_path):
            for filename in os.listdir(topology_file_path):
                topology_content = self.get_file_content(filename, topology_file_path)
                
                if not all(field in topology_content for field in PluginPackageConstants.TOPOLOGY_REQUIRED_FIELDS):
                    raise ValueError(f"Invalid Topology file: {filename}. topologyName, topologyType, description and nodes are required")
                
                required_nested_fields = {"cpu": ["cpus"], "os": ["osName"]}
                for node in topology_content["nodes"]:
                    if not all(field in node for field in PluginPackageConstants.TOPOLOGY_NODE_REQUIRED_FIELDS):
                        raise ValueError(f"Invalid Topology file: {filename}. nodeName, nodeType, deploymentOrder, cpu, os, and ram are required for topology node")
                    
                    for parent, child_fields in required_nested_fields.items():
                        if not all(child in node[parent] for child in child_fields):
                            raise ValueError(f"Invalid Topology file: {filename}. {', '.join(child_fields)} are required in {parent} for topology node")
                
    def validate_infra_profile_details(self):
        """Method to validate plugin infra profile

        Args:
        """
        infra_profile_file_path = self.get_path(PluginPackageConstants.INFRAPROFILE)
        if os.path.isdir(infra_profile_file_path):
            is_exist = self.check_if_topology_and_solution_stack_exist()
            if not is_exist:
                raise ValueError(f"Error: Solution Stack or Topology is missing")
            for filename in os.listdir(infra_profile_file_path):
                infra_profile_content = self.get_file_content(filename, infra_profile_file_path)
                if infra_profile_content:
                    if not all(field in infra_profile_content for field in PluginPackageConstants.INFRAPROFILE_REQUIRED_FIELDS):
                        raise ValueError(f"Invalid Infra Profile file: {filename}. infraProfileName, tagName, topologyName, solutionStackName and solutionStackVersion is required")  
                    
                    self.check_topology_and_solution_stack_compatibility(infra_profile_content)
                    
                    if "infraTestCases" in infra_profile_content:
                        test_suite_dict = self.get_test_suites_and_testcases()
                        for infra_test_suite, infra_test_cases in infra_profile_content["infraTestCases"].items():
                            test_cases = test_suite_dict.get(infra_test_suite)
                            if not test_cases:
                                raise ValueError(f"Invalid Infra Profile file: {filename}. test suite {infra_test_suite} is not present")
                            if not set(infra_test_cases).issubset(set(test_cases)):       
                                raise ValueError(f"Invalid Infra Profile file: {filename}. test cases {infra_test_cases} are not matching")
    
    def get_test_suites_and_testcases(self):
        """Method to get plugin testsuites and testcases 

        Args:
        """
        test_cases_file_path = self.get_path(PluginPackageConstants.TEST_CASES)
        filename = "tc_config.json"
        test_suite_dict = {}
        if os.path.isdir(test_cases_file_path):
            test_cases_content = self.get_file_content(filename, test_cases_file_path)
            if test_cases_content and "testSuites" in test_cases_content:
                for test_suite in test_cases_content["testSuites"]:
                    test_suite_dict[test_suite["testSuiteName"]] = test_suite["testCasesName"]
                 
        return test_suite_dict
    
    def check_topology_and_solution_stack_compatibility(self, infra_profile_content):
        """Method to check topology and solution stack compatibility for infra profile

        Args:
            infra_profile_content (str): infra profile content
        """
        topology_file_path = self.get_path(PluginPackageConstants.TOPOLOGY)
        infra_topology_content = ""
        infra_solution_stack_content = ""
        if not os.path.isdir(topology_file_path):
            raise ValueError(f"Error: Compatibility check failed. Reason: Topology is missing")
        
        is_topology_name_matching = False
        for filename in os.listdir(topology_file_path):
            topology_content = self.get_file_content(filename, topology_file_path)
            if topology_content and topology_content["topologyName"] == infra_profile_content["topologyName"]:
                is_topology_name_matching = True
                infra_topology_content = topology_content
                
        if not is_topology_name_matching:
            raise ValueError(f"Invalid Infra Profile file. Topology {infra_profile_content['topologyName']} is not present")
            
        solution_stack_file_path = self.get_path(PluginPackageConstants.SOLUTION_STACK)
        if not os.path.isdir(solution_stack_file_path):
            raise ValueError(f"Error: Compatibility check failed. Reason: Solution Stack is missing")
        
        is_solution_stack_matching = False
        for filename in os.listdir(solution_stack_file_path):
            solution_stack_content = self.get_file_content(filename, solution_stack_file_path)
            if solution_stack_content and solution_stack_content["solutionStackName"] == infra_profile_content["solutionStackName"] and \
                solution_stack_content["solutionStackVersion"] == infra_profile_content["solutionStackVersion"]:
                is_solution_stack_matching = True
                infra_solution_stack_content = solution_stack_content
                 
        if not is_solution_stack_matching:
            raise ValueError(f"Invalid Infra Profile file. Solution Stack {infra_profile_content['solutionStackName']} with version {infra_profile_content['solutionStackVersion']} is not present")
        
        for node in infra_topology_content["nodes"]:
            topology_os = node.get("os")
            solution_stack_os = infra_solution_stack_content.get("os")
            if solution_stack_os and solution_stack_os.get(topology_os["osName"], None):
                if topology_os.get("osVersion"):
                    if solution_stack_os[topology_os["osName"]] != topology_os["osVersion"]:
                        raise ValueError(f"Invalid Infra Profile file. OS {topology_os['osName']} - {topology_os['osVersion']} not present in solution stack {infra_solution_stack_content['solutionStackName']} - {infra_solution_stack_content['solutionStackVersion']}.")
            else:
                raise ValueError(f"Invalid Infra Profile file. OS {topology_os['osName']} not present in solution stack {infra_solution_stack_content['solutionStackName']} - {infra_solution_stack_content['solutionStackVersion']}.")
            
            topology_platform = topology_os.get("platform")
            if topology_platform:
                if topology_platform["platformName"] != "default_platform":
                    solution_stack_platform = infra_solution_stack_content.get("platform")
                    if solution_stack_platform and solution_stack_platform.get(topology_platform["platformName"]):
                        if topology_platform.get("platformVersion"):
                            if solution_stack_platform[topology_platform["platformName"]] != topology_platform["platformVersion"]:
                                raise ValueError(f"Invalid Infra Profile file. Platform {topology_os['platformName']} - {topology_os['platformVersion']} not present in solution stack {infra_solution_stack_content['solutionStackName']} - {infra_solution_stack_content['solutionStackVersion']}.")
                    else:
                        raise ValueError(f"Invalid Infra Profile file. Platform {topology_platform['platformName']} not present in solution stack {infra_solution_stack_content['solutionStackName']} - {infra_solution_stack_content['solutionStackVersion']}.")
                
                topology_applications = topology_platform.get("applications")
                if topology_applications:
                    solution_stack_applications = infra_solution_stack_content.get("applications",)
                    if not solution_stack_applications:
                        raise ValueError(f"Invalid Infra Profile file. applications not present in solution stack {infra_solution_stack_content['solutionStackName']} - {infra_solution_stack_content['solutionStackVersion']}.")
                    
                    for topology_application in topology_applications:                                
                        if solution_stack_applications.get(topology_application["appName"]):
                            if topology_application.get("appVersion"):
                                if solution_stack_applications[topology_application["appName"]] != topology_application["appVersion"]:    
                                    raise ValueError(f"Invalid Infra Profile file. Application {topology_application['appName']} - {topology_application['appVersion']} not present in solution stack {infra_solution_stack_content['solutionStackName']} - {infra_solution_stack_content['solutionStackVersion']}.")
                        else:
                            raise ValueError(f"Invalid Infra Profile file. Application {topology_application['appName']} not present in solution stack {infra_solution_stack_content['solutionStackName']} - {infra_solution_stack_content['solutionStackVersion']}.")

                
    def check_if_topology_and_solution_stack_exist(self):
        """Method to check topology and solution stack exist

        Args:
        """
        topology_file_path = self.get_path(PluginPackageConstants.TOPOLOGY)
        if not os.path.isdir(topology_file_path):
            return False
        solution_stack_file_path = self.get_path(PluginPackageConstants.SOLUTION_STACK)
        if not os.path.isdir(solution_stack_file_path):
            return False
        return True
    
    def validate_test_plan_details(self):
        """Method to validate plugin infra profile

        Args:
        """
        test_plan_file_path = self.get_path(PluginPackageConstants.TEST_PLAN)
        if os.path.isdir(test_plan_file_path):
            for filename in os.listdir(test_plan_file_path):
                test_plan_content = self.get_file_content(filename, test_plan_file_path)
                if not all(field in test_plan_content for field in PluginPackageConstants.TEST_PLAN_REQUIRED_FIELDS):
                    raise ValueError(f"Invalid Test Plan file: {filename}. testPlanName and testPlanTestCases are required")          
                
                test_suite_dict = self.get_test_suites_and_testcases()
                for test_suite, testcases in test_plan_content["testPlanTestCases"].items():
                    test_cases = test_suite_dict.get(test_suite)
                    if not test_cases:
                        raise ValueError(f"Invalid Test Plan file: {filename}. test suite is not present")
                    if not set(testcases).issubset(set(test_cases)):       
                        raise ValueError(f"Invalid Test Plan file: {filename}. test cases are not matching")
    
    def get_file_content(self, filename, file_path):
        """Method to get solution stack content

        Args:
            filename (str): file name
            file_path (str): file path
        """
        if filename.endswith('.json'):
            file_path = os.path.join(file_path, filename)
            try:
                with open(file_path, 'r') as file:
                    file_data = json.load(file)
                    return file_data
            except json.JSONDecodeError:
                raise ValueError(f"Error: {filename} is not a valid JSON file.") 
            except IOError:
                raise ValueError(f"Error: Could not read file {filename}")
            except Exception:
                raise ValueError(f"Error: Could not read file {filename}")
        else:
            raise ValueError(f"Error: {filename} is not a JSON file.")
        
    def get_image_file_content(self, filename, file_path):
        """Method to get solution stack content

        Args:
            filename (str): file name
            file_path (str): file path
        """
        try:
            if self.is_image_by_extension(filename):
                file_path = os.path.join(file_path, filename)
                with open(file_path, 'rb') as file:
                    file_content = file.read()
                encoded_content = base64.b64encode(file_content).decode('utf-8')
                return encoded_content
            else:
                raise ValueError(f"Error: {filename} is not supported")
        except Exception:
            raise ValueError(f"Error: Could not read file {filename}")

