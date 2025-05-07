import sys
import cmd
import requests
import json
import time
import os
import re

class MyCLI(cmd.Cmd):
    has_inline_args = False
    SUPPORTED_OPERATION = [
        'add_vertical', 'add_category', 'upload_plugin_package', 'upload_app_package', 'upload_security_tool_package',
        'create_application', 'upload_test_module_package', 'create_module', 'toggle_application',
        'toggle_module', 'delete_vertical', 'delete_category', 'delete_plugin_package',
        'delete_app_package', 'delete_test_module_package', 'delete_security_tool_package', 'delete_application', 'delete_module',
        'get_verticals', 'get_categories', 'get_plugin_packages', 'get_app_packages',
        'get_test_module_packages', 'get_security_tool_packages', 'get_applications', 'get_modules', 'delete_module_set',
        'manage_application'
    ]
    url = None
    packageName = None
    packageType = None
    appName = None
    toolName = None
    version = None
    verticalName = None
    categoryName = None
    scrFilePath = None
    categoryid = None
    verticalid = None
    applicationid = None
    description = None
    description = None
    moduleName = None
    testModulePackageId = None
    operation_data = {}
    module_data = {}
    file_path = None
    vertical_id = None
    function_name = None
    uploadPackageType = None

    def __init__(self):
        super().__init__()
        MASTER_NODE_IP = os.getenv("MASTER_NODE_IP", "node01")
        self.regal_api_server_url = f"http://{MASTER_NODE_IP}:30606"

    def get_access_keys(self):
        headers = {'Content-type': 'application/json','Accept':'application/json'}
        return headers

    def get_regal_api_access_keys(self):
        data = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password",
            "client_id": "regal-gui",
            "scope": "openid"
        }

        headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
        try:
            MASTER_NODE_IP = os.getenv("MASTER_NODE_IP", "node01")
            url_str = f"{self.regal_api_server_url}/auth/realms/regal/protocol/openid-connect/token"

            json_data = requests.post(url_str, headers=headers, data=data).json()
            access_token = json_data["access_token"]
        except Exception as ex:
            print(ex)
            print("Failed to fetch access token! Is keycloak url up?")
            exit()

        headers = {'Content-type': 'application/json','Accept': 'application/json', 
                        'Authorization': f'Bearer {access_token}'}
        return headers

    def fetch_config(self):
        json_file_path = 'regal_mp.json'
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        self.username = data.get('username', 'admin')
        self.password = data.get('password', 'admin')

        # marketplace_config = '/opt/regal/config/config.json'
        # with open(marketplace_config, 'r') as file:
        #     marketplace_config_data = json.load(file)
        marketplace_config_data = {}
        marketplace_ip = marketplace_config_data.get('CloudMpIp', '10.0.0.1')
        marketplace_port = marketplace_config_data.get('CloudMpApiPort', '5028')
        self.url = f'http://{marketplace_ip}:{marketplace_port}'
        self.scrFilePath = data['scrFilePath']

    def     fetch_data(self, inline_argument):
        """
            fetches the data
        """
        self.has_inline_args = True
        # print(f"Fetching data from {inline_argument}.json file")
        filename = f"operations/{inline_argument}.json"

        try:
            with open(filename, 'r') as file:
                data = json.load(file)
                # print(f"Fetched data: {data}")
                self.operation_data = data
            return data
        except FileNotFoundError:
            print(f"Error: {filename} not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: {filename} is not a valid JSON file.")
            sys.exit(1)
    
    def upload_plugin_package(self):
        """
        Uploads the plugin package to the cloud marketplace.

        Returns:
            None
        """
        
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMarketPlace/upload/pluginPackage'
        data = {
            "packageName": str(self.packageName)
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            print('Upload plugin is in progress, please wait! The pluginPackage ID is \t' + response.json().get('pluginPackageId'))
            
            return response.json().get('pluginPackageId')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to upload plugin package! Error: {err} " + response.text)
            else:
                print(f"Failed to upload plugin package! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()
    
    def get_status_of_plugin_package(self, pluginPackageId):
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/upload/pluginPackage/{pluginPackageId}'
        data = {}

        try:
            response = requests.get(url, headers=headers, json=data)
            response.raise_for_status()
            status = response.json().get('jobStatus')
            return_url = response.json().get('url')
            return status, return_url 
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to get plugin package details! Error: {err} " + response.text)
            else:
                print(f"Failed to get plugin package details! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
               print(f"An error occurred: {e} " + response.text)
            else:
               print(f"An error occurred: {e} ")
            exit()
            
    def upload_package_in_cloud_mp(self, resp_url, selected_file):
        """
        Uploads a package in a job using the specified return URL.

        Args:
            returnurl (str): The return URL for the job.

        Returns:
            None
        """

        
        url = f"{resp_url}"

        payload = {}
        # path = os.path.join(self.scrFilePath, "ss7perftool@1.0.0.rp")
        # selected_file = self.select_listed_files_with_extension(".rp")
        package_info = selected_file.rsplit('/', 1)[-1]
        files=[
            ('file',(str(package_info) ,open(str(selected_file),'rb'),'application/octet-stream'))
        ]
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload, files=files)

        print("Uploading package to Cloud MP, please wait!")
                
    def upload_app_package(self):
            """
            Uploads the application package to the cloud marketplace.

            Returns:
                None

            Raises:
                requests.exceptions.HTTPError: If there is an HTTP error during the upload.
                Exception: If any other error occurs during the upload.
            """
            headers = self.get_access_keys()
            if headers is None:
               return

            url = f'{self.url}/cloudMarketPlace/upload/appPackage'
            data = {
                "packageName": self.packageName,
                "packageType": self.packageType,
                "appName": self.appName,
                "version": self.version
            }

            try:
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                print('Upload app package is in progress, please wait! The app package ID is \t'+ response.json().get('appPackageId'))
                return response.json().get('appPackageId')
            except requests.exceptions.HTTPError as err:
                if response is not None:
                    print(f"Failed to upload app package! Error: {err} " + response.text)
                else:
                    print(f"Failed to upload app package! Error: {err} " )
                exit()
            except Exception as e:
                if response is not None:
                    print(f"An error occurred: {e} " + response.text)
                else:
                    print(f"An error occurred: {e} ")
                exit()
                
    def get_status_of_app_package(self, appPackageId):
        """
        Retrieves the status and return URL of an application package.

        Args:
            appPackageId (str): The ID of the application package.

        Returns:
            tuple: A tuple containing the status and return URL of the application package.

        Raises:
            requests.exceptions.HTTPError: If there is an HTTP error while making the request.
            Exception: If any other error occurs.

        """
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/upload/appPackage/{appPackageId}'
        data = {}

        try:
            response = requests.get(url, headers=headers, json=data)
            response.raise_for_status()
            status = response.json().get('jobStatus')
            return_url = response.json().get('url')
            return status, return_url 
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to get app package details! Error: {err} " + response.text)
            else:
                print(f"Failed to get app package details! Error: {err} " )
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()      
    
    def upload_app_package_in_cloud_mp(self, resp_url, selected_file):
        """
        Uploads an application package in a job using the specified response URL.

        Args:
            resp_url (str): The response URL to upload the application package to.

        Returns:
            None
        """


        url = f"{resp_url}"
        payload = {}
        # path = os.path.join(self.scrFilePath, "mme-hss-2.0.0.tgz")
        # selected_file = self.select_listed_files_with_extension(".tgz")
        package_info = selected_file.rsplit('/', 1)[-1]
        files=[
            ('file',(str(package_info), open(str(selected_file),'rb'),'application/octet-stream'))
        ]
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload, files=files)

        print("Uploading package to Cloud MP, please wait!")       
                
    def create_application(self, plugin_ids):
        """
            Uploads the application package to the cloud marketplace.

            Returns:
                None

            Raises:
                requests.exceptions.HTTPError: If there is an HTTP error during the upload.
                Exception: If any other error occurs during the upload.
            """
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMarketPlace/createApplication'
        data = {
            "applicationName": self.appName,
            "description": self.description,
            "version": self.version,
            "plugins": plugin_ids,
            "appPackageId": self.appPackageId,
            "verticalId": self.verticalid,
            "categoryId": self.categoryid
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            application_id = response.json().get('applicationId')
            print('The application ID is ' + application_id)

            start_time = time.time()
            end_time = start_time + 60 
            print("Application creation in progress, please wait!")
            while time.time() < end_time:
                applications = self.validate_create_application()
                if applications and application_id in applications:
                    operation_state = applications[application_id]["operationState"]
                    if operation_state == "success":
                        print('Application created successfully! The application ID is \t' + application_id)
                        return application_id
                    elif operation_state == "inProgress":
                        time.sleep(2)  
                        continue
                    else:
                        print("Failed to create application! Please check the status of the application")
                        return None
                else:
                    print("Failed to create application! Please check the status of the application")
                    return None

            print("Application creation took more time than expected! Please check the status of the application")
            return None
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to create application! Error: {err} " + response.text)
            else:
                print(f"Failed to create application! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def manage_application(self, application_id, action, upgrade_application_version=None):
        """
            manage the application package to the cloud marketplace.

            Returns:
                None

            Raises:
                requests.exceptions.HTTPError: If there is an HTTP error during the upload.
                Exception: If any other error occurs during the upload.
            """
        headers = self.get_regal_api_access_keys()
        if headers is None:
            return

        url = f'{self.regal_api_server_url}/api/localMarketPlace/apps/{application_id}/action/{action}'
        data = {
            "scope": "all"
        }
        if action == "update":
            data["updateVersion"] = upgrade_application_version

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            print('The application ID is ' + application_id)

            start_time = time.time()
            end_time = start_time + 600 
            print(f"Application {action}ation in progress, please wait!")
            while time.time() < end_time:
                applications = self.validate_manage_application()
                if applications and application_id in applications:
                    operation_state = applications[application_id]["operationState"]
                    if operation_state == "INSTALLED" or operation_state == "NOT_INSTALLED":
                        print(f'Application {action}ed successfully!')
                        return application_id
                    elif operation_state == "DOWNLOADING" or operation_state == "INSTALLING" or operation_state == "UNINSTALLING" or operation_state == "UPDATING":
                        time.sleep(2)  
                        continue
                    else:
                        if action == "update":
                            print(f"Please check the status of the application")
                            return None  
                        print(f"Failed to {action} application! Please check the status of the application")
                        return None
                else:
                    print(f"Failed to {action} application! Please check the status of the application")
                    return None

            print(f"Application {action}ation took more time than expected! Please check the status of the application")
            return None
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to {action} application! Error: {err} " + response.text)
            else:
                print(f"Failed to {action} application! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def manage_upgrade_application(self, old_application_id, application_name, base_version, upgrade_version):
        """
            manage the application package to the cloud marketplace.

            Returns:
                None

            Raises:
                requests.exceptions.HTTPError: If there is an HTTP error during the upload.
                Exception: If any other error occurs during the upload.
            """
        headers = self.get_regal_api_access_keys()
        action = "update"
        if headers is None:
            return

        url = f'{self.regal_api_server_url}/api/localMarketPlace/apps/{old_application_id}/action/{action}'
        data = {
            "scope": "all"
        }
        data["updateVersion"] = upgrade_version
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            print('The base application ID is ' + old_application_id)

            start_time = time.time()
            end_time = start_time + 600 
            print(f"Application {action}ation in progress, please wait!")
            while time.time() < end_time:
                applications = self.validate_manage_application()
                for app_id, app_info in applications.items():
                    app_name = app_info.get("applicationName")
                    app_version = app_info.get("version")
                    app_status = app_info.get("operationState")
                    failed_status = app_info.get("failedStatus")
                    if app_name == application_name and app_version == base_version:
                        if failed_status:
                            print(f"Failed to {action} application! Please check the status of the application")
                            print(f"Failed status: {failed_status}")
                            return 
                        print(f'Application upgrade is in progress, please wait!')
                    elif app_name == application_name and app_version == upgrade_version: 
                        if failed_status:
                            print(f"Failed to {action} application! Please check the status of the application")
                            print(f"Failed status: {failed_status}")
                            return 
                        elif app_status == "INSTALLED":
                            print(f'Application upgrade is completed successfully!')
                            return app_id
                        print(f'Application upgrade is in progress, please wait!')
      
                time.sleep(2)
                continue
            print(f"Application {action}ation took more time than expected! Please check the status of the application")
            return None
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to {action} application! Error: {err} " + response.text)
            else:
                print(f"Failed to {action} application! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def add_vertical(self):
        
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/vertical/add'
        data = {
            "verticalName": self.verticalName
            }
        # print(f"vertical_data: {data}")
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            print('Added vertical successfully! the vertical ID is \t'+ response.json().get('verticalId'))
            return response.json().get('verticalId')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to add vertical! Error: {err} " + response.text)
            else:
                print(f"Failed to add vertical! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()
    
    def add_category(self):
        
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/category/add'
        data = {
            "categoryName": self.categoryName,
            "verticalRefId": self.verticalid
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            print('Added category successfully! The category ID is \t' + response.json().get('categoryId'))
            return response.json().get('categoryId')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to add category! Error: {err} " + response.text)
            else:
                print(f"Failed to add category! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()
    
    def delete_category(self, categoryId):
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/category/delete/{categoryId}'
        data = {}

        try:
            response = requests.delete(url, headers=headers, json=data)
            response.raise_for_status()
            print('Deleted category successfully! \n')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to delete category! Error: {err} " + response.text)
            else:
                print(f"Failed to delete category! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()
    
    def delete_vertical(self, verticalid):
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/vertical/delete/{verticalid}'
        data = {}

        try:
            response = requests.delete(url, headers=headers, json=data)
            response.raise_for_status()
            print('Deleted vertical successfully! \n')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to delete vertical! Error: {err} " + response.text)
            else:
                print(f"Failed to delete vertical! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()
    
    def enable_disable_application(self, applicationid, enable_status):
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/apps/{str(applicationid)}/status/{str(enable_status)}'
        data = {}

        try:
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            if enable_status == 'enable':
               print('Enabled application successfully! \n')
            elif enable_status == 'disable':
                print('Disabled application successfully! \n')   
        except requests.exceptions.HTTPError as err:
            if response is not None:
                if enable_status == 'enable':
                    print(f"Failed to enable application. Error: {err} " + response.text)
                elif enable_status == 'disable':
                    print(f"Failed to disable application. Error: {err} " + response.text)
            else:
                if enable_status == 'enable':
                    print(f"Failed to enable application. Error: {err} ")
                elif enable_status == 'disable':
                    print(f"Failed to disable application. Error: {err} ")
            exit()   
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()


    def upload_test_module(self):
        """
        Uploads the plugin package to the cloud marketplace.

        Returns:
            None
        """
        
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/upload/testModulePackage'
        data = {
            "packageName": self.packageName
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            print('Upload test module package is in progress, please wait! The test module package ID: \t' + response.json().get('testModulePackageId'))
            return response.json().get('testModulePackageId')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to upload test module package! Error: {err} " + response.text)
            else:
                print(f"Failed to upload test module package! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()
    
    def upload_package_test_module_to_cloud_mp(self, resp_url, selected_file):
        
        url = f"{resp_url}"

        payload = {}
        # selected_file = self.select_listed_files_with_extension(".rtm")
        package_info = selected_file.rsplit('/', 1)[-1]
        files=[
            ('file',(str(package_info) ,open(str(selected_file),'rb'),'application/octet-stream'))
        ]
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload, files=files)

        print("Uploading test module package to Cloud MP, please wait!")
        
    def create_module(self, all_test_modules, all_application_ids):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMarketPlace/createModule'
        data = {
           "moduleName": self.moduleName,
           "version": self.version,
           "applications": all_application_ids,
           "testModules": all_test_modules,
           "description": self.description,
           "verticalId": self.verticalid
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            module_id = response.json().get('moduleId')
            print('The module ID is ' + module_id)

            
            start_time = time.time()
            end_time = start_time + 60  
            print("Module creation in progress, please wait!")
            while time.time() < end_time:
                modules = self.validate_create_module()
                if modules and module_id in modules:
                    operation_state = modules[module_id]["operationState"]
                    if operation_state == "success":
                        print('Module created successfully! The module ID is \t' + module_id)
                        return module_id
                    elif operation_state == "inProgress":
                        
                        time.sleep(2)
                        continue
                    else:
                        print("Failed to create module! Please check the status of the module")
                        return None
                else:
                    print("Module not found in the database.")
                    return None

            print("Module creation took more time than expected! Please check the status of the module")
            return None
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to create module! Error: {err} " + response.text)
            else:
                print(f"Failed to create module! Error: {err} " )
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()
        
    
    def get_status_of_test_module(self, packageId):
        """
        Get the status of the test module package.

        Returns:
            None
        """
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/upload/testModulePackage/{packageId}'
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status() 
            status = response.json().get('jobStatus')
            return_url = response.json().get('url')
            return status, return_url
        
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to get status of the test module package! Error: {err} " + response.text)
            else:
                print(f"Failed to get status of the test module package! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()             

    def select_listed_files_with_extension(self, extension):
        if not self.has_inline_args:
            files = []
            for file in os.listdir(self.scrFilePath):
                full_path = os.path.join(self.scrFilePath, file)
                if os.path.isfile(full_path) and file.endswith(extension):
                    files.append(full_path)

            if files:
                if extension == '':
                    print("All files in the directory:")
                else:
                    print("Files with " + extension + " extension in the directory:")
                
                for i, file in enumerate(files):
                    print(f"{i+1}. {file}")

                selection = input("Please select a file (enter number): ")
                try:
                    selection_index = int(selection) - 1
                    if 0 <= selection_index < len(files):
                        selected_file = files[selection_index]
                        return selected_file
                    else:
                        print("Invalid selection! \n")
                        exit()
                except ValueError:
                    print("Invalid input! Please enter a number. \n")
                    exit()
            else:
                print("No files with " + extension + " extension found in the directory. \n")
                exit() 
        else:
            if not self.file_path:
                print("File path can not be None")
                sys.exit(1)
                
            if not os.path.exists(self.file_path):
                print("File doesn't exist.")
                sys.exit(1)

            if extension != '' and not self.file_path.endswith(extension):
                print("Invalid File.")
                sys.exit(1)

            return self.file_path

    
    def delete_application(self, applicationid):
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/application/{applicationid}'
        data = {}

        try:
            response = requests.delete(url, headers=headers, json=data)
            response.raise_for_status()
            print('Deleted application successfully! \n')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to delete application! Error: {err} " + response.text)
            else:
                print(f"Failed to delete application! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def enable_disable_module(self, moduleId, enable_status):
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/modules/{moduleId}/status/{enable_status}'
        data = {}
        try:
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            if enable_status == 'enable':
               print('Enabled module successfully! \n')
            elif enable_status == 'disable':
                print('Disabled module successfully! \n')  
        except requests.exceptions.HTTPError as err:
            if response is not None:
                if enable_status == 'enable':
                    print(f"Failed to enable module. Error: {err} " + response.text)
                elif enable_status == 'disable':
                    print(f"Failed to disable module. Error: {err} " + response.text)
            else:
                if enable_status == 'enable':
                    print(f"Failed to enable module. Error: {err} ")
                elif enable_status == 'disable':
                    print(f"Failed to disable module. Error: {err} ")
            exit() 
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit() 

    def delete_test_module_package(self, testModulePackageId):
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/testModulePackage/{testModulePackageId}'
        data = {}
        try:
            response = requests.delete(url, headers=headers, json=data)
            response.raise_for_status()
            print('Deleted test module package successfully! \n')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to delete test module package! Error: {err} " + response.text)
            else:
                print(f"Failed to delete test module package! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def delete_security_tool(self, securityToolPackageId):
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/securityToolPackage/{securityToolPackageId}'
        data = {}
        try:
            response = requests.delete(url, headers=headers, json=data)
            response.raise_for_status()
            print('Deleted security tool package successfully! \n')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to delete security tool package! Error: {err} " + response.text)
            else:
                print(f"Failed to delete security tool package! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()            

    def delete_module(self, moduleId):
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/module/{moduleId}'
        data = {}
        try:
            response = requests.delete(url, headers=headers, json=data)
            response.raise_for_status()
            print('Deleted module successfully! \n')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to delete module! Error: {err} " + response.text)
            else:
                print(f"Failed to delete module! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()                        
    
    def delete_app_package(self, appPackageId):
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMPApiServer/appPackage/{appPackageId}'
        data = {}

        try:
            response = requests.delete(url, headers=headers, json=data)
            response.raise_for_status()
            print('Deleted app package successfully! \n')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to delete app package! Error: {err} " + response.text)
            else:
                print(f"Failed to delete app package! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def delete_plugin_package(self, pluginPackageId):
        headers = self.get_access_keys()
        if headers is None:
           return

        url = f'{self.url}/cloudMarketPlace/pluginPackage/{pluginPackageId}'
        data = {}

        try:
            response = requests.delete(url, headers=headers, json=data)
            response.raise_for_status()
            print('Deleted plugin package successfully! \n')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to delete plugin package! Error: {err} " + response.text)
            else:
                print(f"Failed to delete plugin package! Error: {err} ")     
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()    

    def get_category(self):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMPApiServer/getCategoryDataTable'
        page = 1
        size = 7
        total_records = float('inf')
        categories = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                # category_names.extend([item["categoryName"] for item in json_data["data"]])

                categories.update({item["id"]: item["categoryName"] for item in json_data["data"]})

                page += 1

            print("Category names :")
            i = 1
            for category_id, category_name in categories.items():
                print(f"{i}. {category_name} ")
                i+=1
            
            return categories
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the categories! Error: {err} " + response.text)
            else:
                print(f"Error fetching the categories! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit() 

    def get_vertical(self):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMPApiServer/getVerticalDataTable'
        page = 1
        size = 7
        total_records = float('inf')
        verticals = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                verticals.update({item["id"]: item["verticalName"] for item in json_data["data"]})

                page += 1

            print("Vertical names :")
            i = 1
            for vertical_id, vertical_name in verticals.items():
                print(f"{i}. {vertical_name} ")
                i += 1

            return verticals

        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the verticals! Error: {err} " + response.text)
            else:
                print(f"Error fetching the verticals! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def get_app_package(self):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMPApiServer/getRepoAppUploadMetaData'
        page = 1
        size = 7
        total_records = float('inf')
        apps = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                apps.update({item["id"]: {"appName": item.get("appName"), "version": item.get("version", None)} for item in json_data["data"]})

                page += 1

            print("App package names:")
            i = 1
            for app_id, app_info in apps.items():
                print(f"{i}. {app_info['appName']} - {app_info['version']}")
                i += 1

            return apps

        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the app packages! Error: {err} " + response.text)
            else:
                print(f"Error fetching the app packages! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def validate_manage_application(self):
        headers = self.get_regal_api_access_keys()
        if headers is None:
            return

        url = f'{self.regal_api_server_url}/api/localMarketPlace/apps/dataTable'
        page = 1
        size = 7
        total_records = float('inf')
        applications = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                applications.update({item["appId"]: {"applicationName": item.get("appName"), 
                                                     "version": item.get("appVersion", None), 
                                                     "operationState": item.get("status", None),
                                                     "failureReason": item.get("failureReason")} for item in json_data["data"]})

                page += 1

            return applications

        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the applications! Error: {err} " + response.text)
            else:
                print(f"Error fetching the applications! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def validate_create_application(self):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMPApiServer/getAppsGroupMetaData'
        page = 1
        size = 7
        total_records = float('inf')
        applications = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                applications.update({item["id"]: {"id": item["id"], "applicationName": item.get("applicationName"), "version": item.get("version", None), "operationState": item.get("operationState", None)} for item in json_data["data"]})

                page += 1

            return applications

        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the applications! Error: {err} " + response.text)
            else:
                print(f"Error fetching the applications! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def get_applications(self):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMPApiServer/getAppsGroupMetaData'
        page = 1
        size = 7
        total_records = float('inf')
        applications = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                applications.update({item["id"]: {"applicationName": item.get("applicationName"), "version": item.get("version", None)} for item in json_data["data"]})

                page += 1

            print("Application names:")
            i = 1
            for application_id, application_info in applications.items():
                print(f"{i}. {application_info['applicationName']} - {application_info['version']}")
                i += 1
    
            return applications

        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the applications! Error: {err} " + response.text)
            else:
                print(f"Error fetching the applications! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def get_local_applications(self):
        headers = self.get_regal_api_access_keys()
        if headers is None:
            return

        url = f'{self.regal_api_server_url}/api/localMarketPlace/apps/dataTable'
        page = 1
        size = 7
        total_records = float('inf')
        applications = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                applications.update({item["appId"]: 
                    {"applicationName": item.get("appName"), 
                     "version": item.get("appVersion", None),
                     "status": item.get("status", None),
                     "isBaseVersion":  item.get("isBaseVersion", None),
                     "updateVersion": item.get("updateVersion", None)} for item in json_data["data"]})

                page += 1

            # print("Application names:")
            i = 1
            for application_id, application_info in applications.items():
                print(f"{i}. {application_info['applicationName']} - {application_info['version']}")
                i += 1
    
            return applications

        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the applications! Error: {err} " + response.text)
            else:
                print(f"Error fetching the applications! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def get_test_modules(self):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMPApiServer/getTestModuleUploadMetaData'
        page = 1
        size = 7
        total_records = float('inf')
        test_modules = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                test_modules.update({item["id"]: {"testModuleName": item.get("testModuleName"), "version": item.get("version", None)} for item in json_data["data"]})
                
                page += 1

            print("Test module names :")
            i = 1
            for test_module_id, test_module_info in test_modules.items():
                print(f"{i}. {test_module_info['testModuleName']} - {test_module_info['version']}")
                i += 1

            return test_modules

        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the test modules. Error: {err} " + response.text)
            else:
                print(f"Error fetching the test modules. Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def get_modules(self):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMPApiServer/getModulesGroupMetaData'
        page = 1
        size = 7
        total_records = float('inf')
        modules = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                modules.update({item["id"]: {"moduleName": item.get("moduleName"), "version": item.get("version", None)} for item in json_data["data"]})

                page += 1

            print("Module names :")
            i = 1
            for module_id, module_info in modules.items():
                print(f"{i}. {module_info['moduleName']} - {module_info['version']}")
                i += 1  

            return modules
        
        

        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the modules. Error: {err} " + response.text)
            else:
                print(f"Error fetching the modules. Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def validate_create_module(self):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMPApiServer/getModulesGroupMetaData'
        page = 1
        size = 7
        total_records = float('inf')
        modules = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                modules.update({item["id"]: {"moduleId": item.get("id"),"moduleName": item.get("moduleName"), "operationState": item.get("operationState", None)} for item in json_data["data"]})

                page += 1

            # print("Module names :")
            # i = 1
            # for module_id, module_info in modules.items():
            #     print(f"{i}. {module_info['moduleName']} - {module_info['version']}")
            #     i += 1  

            return modules
        
        

        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the modules. Error: {err} " + response.text)
            else:
                print(f"Error fetching the modules. Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def get_data(self, data_type, return_dict=False):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMPApiServer/get{data_type}DataTable'
        page = 1
        size = 7
        total_records = float('inf')
        names = []
        ids_to_names = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                names.extend([item[f"{data_type.lower()}Name"] for item in json_data["data"]])
                if return_dict:
                    ids_to_names.update({item["id"]: item[f"{data_type.lower()}Name"] for item in json_data["data"]})

                page += 1

            print(f"{data_type} names:")
            for i, name in enumerate(names):
                print(f"{i+1}. {name}")

            return ids_to_names if return_dict else names

        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the {data_type.lower()}s. Error: {err} " + response.text) 
            else:
                print(f"Error fetching the {data_type.lower()}s. Error: {err} ") 
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def get_security_tool(self):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMPApiServer/getSecurityToolUploadMetaData'
        page = 1
        size = 7
        total_records = float('inf')

        tools = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                tools.update({item["id"]: {"toolName": item.get("toolName"), "version": item.get("version", None)} for item in json_data["data"]})

                page += 1

            print("Security tool package names: ")
            i = 1
            for _, tool_info in tools.items():
                print(f"{i}. {tool_info['toolName']} - {tool_info['version']}")
                i += 1
            
            return tools

        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the security tool packages! Error: {err} " + response.text)
            else:
                print(f"Error fetching the security tool packages! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()    

    def get_plugin_package(self):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMPApiServer/getPluginUploadMetaData'
        page = 1
        size = 7
        total_records = float('inf')

        plugins = {}

        try:
            while (page - 1) * size < total_records:
                data = {
                    "filterMap": {},
                    "sortMap": {},
                    "page": page,
                    "size": size
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                json_data = response.json()

                if page == 1:
                    total_records = json_data.get("totalRecords", 0)

                plugins.update({item["id"]: {"pluginName": item.get("pluginName"), "version": item.get("version", None)} for item in json_data["data"]})

                page += 1

            print("Plugin package names :")
            i = 1
            for plugin_id, plugin_info in plugins.items():
                print(f"{i}. {plugin_info['pluginName']} - {plugin_info['version']}")
                i += 1
            
            return plugins

        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Error fetching the plugins! Error: {err} " + response.text)
            else:
                print(f"Error fetching the plugins! Error: {err} ")
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()    

    def get_status_of_package(self, packageId):
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMarketPlace/upload/package/{self.uploadPackageType}/{packageId}'
        data = {}

        max_retries = 6  # 1 minute / 10 seconds = 6 attempts
        retry_delay = 10  # seconds
        attempts = 0

        while attempts < max_retries:
            try:
                response = requests.get(url, headers=headers, json=data)
                response.raise_for_status()
                status = response.json().get('jobStatus')
                return_url = response.json().get('url')
                return status, return_url
            except requests.exceptions.HTTPError as err:
                attempts += 1
                if attempts >= max_retries:
                    if response is not None:
                        print(f"Failed to get package details after {max_retries} attempts! Error: {err} {response.text}")
                    else:
                        print(f"Failed to get package details after {max_retries} attempts! Error: {err}")
                    exit()
                else:
                    time.sleep(retry_delay)
            except Exception as e:
                attempts += 1
                if attempts >= max_retries:
                    if response is not None:
                        print(f"An error occurred after {max_retries} attempts: {e} {response.text}")
                    else:
                        print(f"An error occurred after {max_retries} attempts: {e}")
                    exit()
                else:
                    time.sleep(retry_delay)

    def upload_packages(self):
        """
        Uploads any package to the cloud marketplace.

        Returns:
            - packageName
            - packageId
            - packageType

        Raises:
            requests.exceptions.HTTPError: If there is an HTTP error during the upload.
            Exception: If any other error occurs during the upload.
        """
        headers = self.get_access_keys()
        if headers is None:
            return

        url = f'{self.url}/cloudMarketPlace/upload/package'
        data = {
            "packageName": self.packageName,
            "uploadPackageType": self.uploadPackageType
        }

        if self.uploadPackageType == 'repoApp':
            data.update({
                "packageType": self.packageType,
                "appName": self.appName,
                "version": self.version
            })

        if self.uploadPackageType == 'vulnScanTool':
            data.update({
                "packageType": self.packageType,
                "toolName": self.toolName,
                "version": self.version,
                "description" : self.description,
                "verticalId": self.verticalid,
                "categoryId": self.categoryid
            })

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            print('Upload package is in progress, please wait! The package ID is \t'+ response.json().get('packageId'))
            return response.json().get('packageId')
        except requests.exceptions.HTTPError as err:
            if response is not None:
                print(f"Failed to upload package! Error: {err} " + response.text)
            else:
                print(f"Failed to upload package! Error: {err} " )
            exit()
        except Exception as e:
            if response is not None:
                print(f"An error occurred: {e} " + response.text)
            else:
                print(f"An error occurred: {e} ")
            exit()

    def _upload_packages(self):        
        while True:
            if self.has_inline_args == False: 
                print('Please select the upload package type (enter number): ')
                option = input('\nEnter 1 to upload a plugin package \nEnter 2 to upload an app package \nEnter 3 to upload a test module package \nEnter 4 to upload a security tool package \nEnter 5 to terminate the operation \n\n>>> ')

            else: 
                if self.function_name == 'upload_plugin_package':
                    option = '1'
                elif self.function_name == 'upload_app_package':
                    option = '2'
                elif self.function_name == 'upload_test_module_package':
                    option = '3'
                elif self.function_name == 'upload_security_tool_package':
                    option = '4'
                else:
                    print('Selected option 5 to terminate upload package operation.')
                    option = '5'
           
            if option == '1':
                self.uploadPackageType = 'plugin'

                if self.has_inline_args and self.file_path is None:
                    self.file_path = self.operation_data.get("file_path", None)
                
                selected_file = self.select_listed_files_with_extension(".rp")
        
                file_name = selected_file.split("/")[-1]
                self.packageName = str(file_name)
                print(f"The plugin package name is {self.packageName}")

                packageId = self.upload_packages()

                status, resp_url  = self.get_status_of_package(packageId)
                print("Getting status of plugin package, please wait!")
                plugin_state_iter = 0
                while (status != "COMPLETED"):
                    time.sleep(2)
                    status, resp_url = self.get_status_of_package(packageId)
                    plugin_state_iter += 1
                    if status == "COMPLETED" or status == "ACTIVE" or status == "RUNNING" or status == "SUCCESSFUL":
                        break
                    if status == "FAILED":
                        print('Plugin package upload failed! Please check the status of the plugin package.')
                        break
                    if plugin_state_iter == 60:
                        print('Plugin package upload took more time than expected! Please check the status of the plugin package.')
                        break
                status, resp_url = self.get_status_of_package(packageId)
                print("Uploading plugin package, please wait!")

                self.upload_package_in_cloud_mp(resp_url, selected_file)
                status, resp_url  = self.get_status_of_package(packageId)
                plugin_state_iter = 0
                while (status != "COMPLETED"):
                    time.sleep(2)
                    status, resp_url = self.get_status_of_package(packageId)
                    plugin_state_iter += 1
                    if status == "COMPLETED" or status == "SUCCESSFUL":
                        print('Uploaded plugin package successfully! \n')
                        break
                    if status == "FAILED":
                        print('Plugin package upload failed! Please check the status of the plugin package. \n')
                        break
                    if plugin_state_iter == 60:
                        print('Plugin package upload took more time than expected! Please check the status of the plugin package. \n')
                        break
                
                time.sleep(30)
                return packageId

            elif option == '2':
                self.uploadPackageType = 'repoApp'  

                if self.has_inline_args and self.file_path is None:
                    self.file_path = self.operation_data.get("file_path", None)

                selected_file = self.select_listed_files_with_extension("")
        
                file_name = selected_file.split("/")[-1]
                self.packageName = str(file_name)
                print(f"The app package name is {self.packageName}")
                valid_package_types = ['OS', 'Apps', 'Platform']

                if not self.has_inline_args:
                    self.packageType = input('Enter the app package type: ')
                else:
                    if not self.packageType:
                        self.packageType = self.operation_data.get("packageType", None)

                if self.packageType not in valid_package_types:
                    print('Invalid Package Type! Please choose from:', ', '.join(valid_package_types))
                    return
                
                if not self.has_inline_args:
                    self.appName = input('Enter the app name: ')
                    self.version = input('Enter the version: ')
                else:
                    if not self.appName:
                        self.appName = self.operation_data.get("appName", None)
                    if not self.version:
                        self.version = self.operation_data.get("version", None)

                if not self.appName:
                    print("App Name can not be none.")
                    sys.exit(1)
                
                if not self.version:
                    print("App Version can not be none.")
                    sys.exit(1)

                packageId = self.upload_packages()

                status, resp_url  = self.get_status_of_package(packageId)
                print("Getting status of app package, please wait!")
                app_state_iter = 0
                while (status != "COMPLETED"):
                    time.sleep(2)
                    status, resp_url = self.get_status_of_package(packageId)
                    app_state_iter += 1
                    if status == "COMPLETED" or status == "ACTIVE" or status == "RUNNING" or status == "SUCCESSFUL":
                        break
                    if status == "FAILED":
                        print('App package upload failed! Please check the status of the app package.')
                        break
                    if app_state_iter == 60:
                        print('App package upload took more time than expected! Please check the status of the app package.')
                        break
                status, resp_url = self.get_status_of_package(packageId)
                print("Uploading app package, please wait!")

                self.upload_package_in_cloud_mp(resp_url, selected_file)
                status, resp_url  = self.get_status_of_package(packageId)
                app_state_iter = 0
                while (status != "COMPLETED"):
                    time.sleep(2)
                    status, resp_url = self.get_status_of_package(packageId)
                    app_state_iter += 1
                    if status == "COMPLETED" or status == "SUCCESSFUL":
                        print('Uploaded app package successfully! \n')
                        break
                    if status == "FAILED":
                        print('App package upload failed! Please check the status of the app package. \n')
                        break
                    if app_state_iter == 60:
                        print('App package upload took more time than expected! Please check the status of the app package. \n')
                        break
                
                time.sleep(30)
                return packageId
            
            elif option == '3':
                if self.has_inline_args and self.file_path is None:
                    self.file_path = self.operation_data.get("file_path", None)

                self.uploadPackageType = 'testModule'

                selected_file = self.select_listed_files_with_extension(".rtm")
        
                file_name = selected_file.split("/")[-1]
                self.packageName = str(file_name)
                print(f"The test module package name is {self.packageName}")

                packageId = self.upload_packages()

                status, resp_url  = self.get_status_of_package(packageId)
                print("Getting status of test module package, please wait!")
                test_module_state_iter = 0
                while (status != "COMPLETED"):
                    time.sleep(2)
                    status, resp_url = self.get_status_of_package(packageId)
                    test_module_state_iter += 1
                    if status == "COMPLETED" or status == "ACTIVE" or status == "RUNNING" or status == "SUCCESSFUL":
                        break
                    if status == "FAILED":
                        print('Test module package upload failed! Please check the status of the test module package.')
                        break
                    if test_module_state_iter == 60:
                        print('Test module package upload took more time than expected! Please check the status of the test module package.')
                        break
                status, resp_url = self.get_status_of_package(packageId)
                print("Uploading test module package, please wait!")

                self.upload_package_in_cloud_mp(resp_url, selected_file)
                status, resp_url  = self.get_status_of_package(packageId)
                test_module_state_iter = 0
                while (status != "COMPLETED"):
                    time.sleep(2)
                    status, resp_url = self.get_status_of_package(packageId)
                    test_module_state_iter += 1
                    if status == "COMPLETED" or status == "SUCCESSFUL":
                        print('Uploaded test module package successfully! \n')
                        break
                    if status == "FAILED":
                        print('Test module package upload failed! Please check the status of the test module package. \n')
                        break
                    if test_module_state_iter == 60:
                        print('Test module package upload took more time than expected! Please check the status of the test module package. \n')
                        break
                
                time.sleep(30)
                return packageId
            
            elif option == '4':
                self.uploadPackageType = 'vulnScanTool'  

                if self.has_inline_args and self.file_path is None:
                    self.file_path = self.operation_data.get("file_path", None)

                selected_file = self.select_listed_files_with_extension(".tar.gz")
        
                file_name = selected_file.split("/")[-1]
                self.packageName = str(file_name)
                print(f"The security tool package name is {self.packageName}")
                
                valid_package_types = ['SAST', 'DAST', 'SCA']

                if not self.has_inline_args:
                    self.packageType = input('Enter the security tool package type: ')
                else:
                    if not self.packageType:
                        self.packageType = self.operation_data.get("packageType", None)

                if self.packageType not in valid_package_types:
                    print('Invalid security tool package type! Please choose from:', ', '.join(valid_package_types))
                    return
                
                if not self.has_inline_args:
                    self.toolName = input('Enter the security tool name: ')
                    self.version = input('Enter the version: ')
                    self.description = input('Enter the description: ')
                else:
                    if not self.toolName:
                        self.toolName = self.operation_data.get("toolName", None)
                    if not self.version:
                        self.version = self.operation_data.get("version", None)
                    if not self.description:
                        self.description = self.operation_data.get("toolDescription", None)

                if not self.toolName:
                    print("Security tool name can not be None.")
                    sys.exit(1)
                
                if not self.version:
                    print("Security tool version can not be None.")
                    sys.exit(1)

                if not self.description:
                    print("Security tool description can not be None.")
                    sys.exit(1)

                if not self.has_inline_args:
                    while True:
                        option = input('Press enter 1 to select a vertical or enter 2 to create vertical or enter 3 to terminate operation: \n')
                        if option == '1':
                            verticals = self.get_vertical()
                            if len(verticals) == 0:
                                print('No verticals available. Please enter 2 to create vertical or enter 3 to terminate operation.')
                                continue
                            selection = input("Please select a vertical (enter number): ")
                            try:
                                selection_index = int(selection) - 1
                                if 0 <= selection_index < len(verticals):
                                    vertical_id = list(verticals.keys())[selection_index]   
                                    self.verticalid = vertical_id
                                    break
                                else:
                                    print("Invalid selection!\n")
                            except ValueError:
                                print("Invalid input! Please enter a number.\n")
                                    
                        elif option == '2':
                            verticalid = self._add_vertical()
                            self.verticalid = verticalid
                            break
                        elif option == '3':
                            exit()
                        else:
                            print('Invalid input. Please try again.')
                else:
                    self.verticalid = self._fetch_vertical_id()

                if not self.has_inline_args:
                    while True:
                        option = input('Press enter 1 to select category or enter 2 to create category or enter 3 to terminate operation: \n')
                        if option == '1':
                            categories = self.get_category()
                            if len(categories) == 0:
                                print('No categories available. Please enter 2 to create category or enter 3 to terminate operation.')
                                continue
                            selection = input("Please select a category (enter number): ")
                            try:
                                selection_index = int(selection) - 1
                                if 0 <= selection_index < len(categories):
                                    category_id = list(categories.keys())[selection_index]   
                                    self.categoryid = category_id
                                    break
                                else:
                                    print("Invalid selection!\n")
                            except ValueError:
                                print("Invalid input! Please enter a number.\n")

                        elif option == '2':
                            categoryid = self._add_category()
                            self.categoryid = categoryid
                            break
                        elif option == '3':
                            exit()
                        else:
                            print('Invalid input. Please try again.')
                else:
                    self.categoryid = self._fetch_category_id()

                packageId = self.upload_packages()

                status, resp_url  = self.get_status_of_package(packageId)
                print("Getting status of security tool package, please wait!")
                tool_state_iter = 0
                while (status != "COMPLETED"):
                    time.sleep(2)
                    status, resp_url = self.get_status_of_package(packageId)
                    tool_state_iter += 1
                    if status == "COMPLETED" or status == "ACTIVE" or status == "RUNNING" or status == "SUCCESSFUL":
                        break
                    if status == "FAILED":
                        print('Security tool package upload failed! Please check the status of the security tool package.')
                        break
                    if tool_state_iter == 60:
                        print('Security tool package upload took more time than expected! Please check the status of the security tool package.')
                        break
                status, resp_url = self.get_status_of_package(packageId)
                print("Uploading security tool package, please wait!")

                self.upload_package_in_cloud_mp(resp_url, selected_file)
                status, resp_url  = self.get_status_of_package(packageId)
                tool_state_iter = 0
                while (status != "COMPLETED"):
                    time.sleep(2)
                    status, resp_url = self.get_status_of_package(packageId)
                    tool_state_iter += 1
                    if status == "COMPLETED" or status == "SUCCESSFUL":
                        print('Uploaded security tool package successfully! \n')
                        break
                    if status == "FAILED":
                        print('Security tool package upload failed! Please check the status of the Security tool package. \n')
                        break
                    if tool_state_iter == 60:
                        print('Security tool package upload took more time than expected! Please check the status of the security tool package. \n')
                        break
                
                time.sleep(30)
                return packageId

            elif option == '5':
                exit()
            else:
                print('Invalid input! Please try again.')   
    
    def _upload_plugin_package(self):
        if self.has_inline_args and self.file_path is None:
            self.file_path = self.operation_data.get("file_path", None)

        selected_file = self.select_listed_files_with_extension(".rp")
        
        file_name = selected_file.split("/")[-1]
        self.packageName = str(file_name)
        print(f"The plugin package name is {self.packageName}")

        pluginPackageId = self.upload_plugin_package()
        status, resp_url  = self.get_status_of_plugin_package(pluginPackageId)
        print("Getting status of plugin package, please wait!")
        plugin_state_iter = 0
        while (status != "COMPLETED"):
            time.sleep(2)
            status, resp_url = self.get_status_of_plugin_package(pluginPackageId)
            plugin_state_iter += 1
            if status == "COMPLETED" or status == "ACTIVE" or status == "RUNNING" or status == "SUCCESSFUL":
                break
            if status == "FAILED":
                print('Plugin package upload failed! Please check the status of the plugin package.')
                break
            if plugin_state_iter == 60:
                print('Plugin package upload took more time than expected! Please check the status of the plugin package.')
                break
        status, resp_url = self.get_status_of_plugin_package(pluginPackageId)
        
        self.upload_package_in_cloud_mp(resp_url, selected_file)
        status, resp_url  = self.get_status_of_plugin_package(pluginPackageId)
        plugin_state_iter = 0
        while (status != "COMPLETED"):
            time.sleep(2)
            status, resp_url = self.get_status_of_plugin_package(pluginPackageId)
            plugin_state_iter += 1
            if status == "COMPLETED" or status == "SUCCESSFUL":
                print('Uploaded plugin package successfully! \n')
                break
            if status == "FAILED":
                print('Plugin package upload failed! Please check the status of the plugin package. \n')
                break
            if plugin_state_iter == 60:
                print('Plugin package upload took more time than expected! Please check the status of the plugin package.\n')
                break
        
        time.sleep(20)
        return pluginPackageId   
        
    def _upload_app_package(self):
        # self.packageName = input('Enter the app package name: ')
        if self.has_inline_args and self.file_path is None:
            self.file_path = self.operation_data.get("file_path", None)

        selected_file = self.select_listed_files_with_extension("")
        
        file_name = selected_file.split("/")[-1]
        self.packageName = str(file_name)
        print(f"The app package name is {self.packageName}")
        valid_package_types = ['OS', 'Apps', 'Platform']

        if not self.has_inline_args:
            self.packageType = input('Enter the app package type: ')
        else:
            if not self.packageType:
                self.packageType = self.operation_data.get("packageType", None)

        if self.packageType not in valid_package_types:
            print('Invalid Package Type! Please choose from:', ', '.join(valid_package_types))
            return
        
        if not self.has_inline_args:
            self.appName = input('Enter the app name: ')
            self.version = input('Enter the version: ')
        else:
            if not self.appName:
                self.appName = self.operation_data.get("appName", None)
            if not self.version:
                self.version = self.operation_data.get("version", None)

        if not self.appName:
            print("App Name can not be none.")
            sys.exit(1)
        
        if not self.version:
            print("App Version can not be none.")
            sys.exit(1)

        appPackageId = self.upload_app_package()
        status, resp_url  = self.get_status_of_app_package(appPackageId)
        print("Getting status of app package, please wait!")
        app_state_iter = 0
        while (status != "COMPLETED"):
            time.sleep(2)
            status, resp_url = self.get_status_of_app_package(appPackageId)
            app_state_iter += 1
            if status == "COMPLETED" or status == "ACTIVE" or status == "RUNNING" or status == "SUCCESSFUL":
                break
            if status == "FAILED":
                print('App package upload failed! Please check the status of the app package.')
                break
            if app_state_iter == 60:
                print('App package upload took more time than expected! Please check the status of the app package.')
                break
        status, resp_url = self.get_status_of_app_package(appPackageId)
        print("Uploading app package, please wait!")

        self.upload_app_package_in_cloud_mp(resp_url, selected_file)
        status, resp_url  = self.get_status_of_app_package(appPackageId)
        app_state_iter = 0
        while (status != "COMPLETED"):
            time.sleep(2)
            status, resp_url = self.get_status_of_app_package(appPackageId)
            app_state_iter += 1
            if status == "COMPLETED" or status == "SUCCESSFUL":
                print('Uploaded app package successfully! \n')
                break
            if status == "FAILED":
                print('App package upload failed! Please check the status of the app package. \n')
                break
            if app_state_iter == 60:
                print('App package upload took more time than expected! Please check the status of the app package. \n')
                break
        
        time.sleep(20)
        return appPackageId
    
    def _create_application(self):
        if not self.has_inline_args:
            while True:
                option = input('Press enter 1 to select a vertical or enter 2 to create vertical or enter 3 to terminate operation: \n')
                if option == '1':
                    verticals = self.get_vertical()
                    if len(verticals) == 0:
                        print('No verticals available. Please enter 2 to create vertical or enter 3 to terminate operation.')
                        continue
                    selection = input("Please select a vertical (enter number): ")
                    try:
                        selection_index = int(selection) - 1
                        if 0 <= selection_index < len(verticals):
                            vertical_id = list(verticals.keys())[selection_index]   
                            self.verticalid = vertical_id
                            break
                        else:
                            print("Invalid selection!\n")
                    except ValueError:
                        print("Invalid input! Please enter a number.\n")
                            
                elif option == '2':
                    verticalid = self._add_vertical()
                    self.verticalid = verticalid
                    break
                elif option == '3':
                    exit()
                else:
                    print('Invalid input. Please try again.')
        else:
            self.verticalid = self._fetch_vertical_id()
        
        if not self.has_inline_args:
            while True:
                option = input('Press enter 1 to select category or enter 2 to create category or enter 3 to terminate operation: \n')
                if option == '1':
                    categories = self.get_category()
                    if len(categories) == 0:
                        print('No categories available. Please enter 2 to create category or enter 3 to terminate operation.')
                        continue
                    selection = input("Please select a category (enter number): ")
                    try:
                        selection_index = int(selection) - 1
                        if 0 <= selection_index < len(categories):
                            category_id = list(categories.keys())[selection_index]   
                            self.categoryid = category_id
                            break
                        else:
                            print("Invalid selection!\n")
                    except ValueError:
                        print("Invalid input! Please enter a number.\n")

                elif option == '2':
                    categoryid = self._add_category()
                    self.categoryid = categoryid
                    break
                elif option == '3':
                    exit()
                else:
                    print('Invalid input. Please try again.')
        else:
            self.categoryid = self._fetch_category_id()

        if not self.has_inline_args:
            all_plugin_ids = []
            while True: 
                option = input('Press enter 1 to select a plugin package or enter 2 to upload plugin or enter 3 to terminate operation. Press Enter to proceed. \n')
                if option == '1':
                    plugins = self.get_plugin_package()
                    if len(plugins) == 0:
                        print('No plugin packages available. Please enter 2 to upload plugin or enter 3 to terminate operation.')
                        continue
                    selection = input("Please select a plugin (enter number): ")
                    try:
                        selection_index = int(selection) - 1
                        if 0 <= selection_index < len(plugins):
                            plugin_package_id = list(plugins.keys())[selection_index]   
                            self.pluginPackageId = plugin_package_id
                            all_plugin_ids.append(self.pluginPackageId)
                        else:
                            print("Invalid selection! \n")
                    except ValueError:
                        print("Invalid input! Please enter a number. \n")
                elif option == '2':
                    pluginid = self._upload_packages()
                    self.pluginPackageId = pluginid
                    all_plugin_ids.append(self.pluginPackageId)
                elif option == '3':
                    exit()    
                elif option == '':
                    break 
                else:
                    print('Invalid input. Please try again.')       
        else:
            all_plugin_ids = self._fetch_all_plugin_id()
        
        if not self.has_inline_args:
            while True:
                option = input('Press enter 1 to select app package or enter 2 to upload app package or enter 3 to terminate operation: \n')
                if option == '1':
                    app_packages = self.get_app_package()
                    if len(app_packages) == 0:
                        print('No app packages available. Please enter 2 to upload app package or enter 3 to terminate operation.')
                        continue
                    selection = input("Please select a app package (enter number): ")
                    try:
                        selection_index = int(selection) - 1
                        if 0 <= selection_index < len(app_packages):
                            app_package_id = list(app_packages.keys())[selection_index]   
                            self.appPackageId = app_package_id
                            break
                        else:
                            print("Invalid selection!\n")
                    except ValueError:
                        print("Invalid input! Please enter a number.\n")
                elif option == '2':
                    appPackageId = self._upload_packages()
                    self.appPackageId = appPackageId
                    break
                elif option == '3':
                    exit()
                else:
                    print('Invalid input. Please try again.')
        else:
            self.appPackageId = self._fetch_app_package_id()
        
        if not self.has_inline_args:
            self.appName = input('Enter the application name: ')
            self.version = input('Enter the version: ')  
            self.description = input('Enter the description: ')
        else:
            self.appName = self.operation_data.get("applicationName", None)
            if not self.appName:
                print(f"Application name can not be None")
                sys.exit(1)
            
            self.version = self.operation_data.get("version", None)
            if not self.version:
                print(f"Application version can not be None")
                sys.exit(1)
            
            self.description = self.operation_data.get("description", None)
            if not self.description:
                print(f"Application description can not be None")
                sys.exit(1)

        application_exists = self._check_local_application_exists(self.appName, self.version)
        if application_exists:
            print("Application with same version already exists. skipping")

        applicationid = self.create_application(all_plugin_ids)
        time.sleep(20)
        return applicationid

    def _manage_application(self):
        if not self.has_inline_args:
            applications = self.get_local_applications()
            if len(applications) == 0:
                    print('No applications available. \n')
                    return
            selection = input("Please select an application (enter number): ")

            try:
                selection_index = int(selection) - 1
                if 0 <= selection_index < len(applications):
                    application_id = list(applications.keys())[selection_index]   
                    self.applicationid = application_id
                    self.action = input('Select the action (enter 1 to install or enter 2 to uninstall): ')
                    if self.action == '1':
                        self.action = 'install'
                    elif self.action == '2':
                        self.action = 'uninstall'
                    else:
                        print('Invalid input. Please try again.')
                        return   

                    self.manage_application(self.applicationid, self.action) 
                else:
                    print("Invalid selection! \n")
                    return
            except ValueError:
                print("Invalid input! Please enter a number. \n")
                return
        else:
            application_name = self.operation_data.get("applicationName", None)
            if not application_name:
                print(f"Application Name: {application_name} is invalid.")
                sys.exit(1)

            application_version = self.operation_data.get("applicationVersion", None)
            if not application_version:
                print(f"Application Version: {application_version} is invalid.")
                sys.exit(1)
                
            self.applicationid, self.action, old_version = self._get_app_id_and_action(application_name, application_version)
            print(f"Application ID: {self.applicationid} and Action: {self.action}")
            if not self.applicationid:
                print(f"Application {application_name} does not exist.")
                sys.exit(1)

            if self.action == "skip":
                print("Application is already installed. Skipping...")
                sys.exit(1)

            if not self.action or self.action not in ["install", "uninstall", "update"]:
                print(f"Action '{self.action}' is invalid.")
                sys.exit(1)
            if self.action == "update":
                self.manage_upgrade_application(self.applicationid, application_name, old_version, application_version)
            else:
                self.manage_application(self.applicationid, self.action, application_version)

    def _add_vertical(self):
        if not self.has_inline_args:
            self.verticalName = input('Enter the vertical name: ')
        else:
            if not self.verticalName:
                self.verticalName = self.operation_data.get("verticalName", None)
        verticalid = self.add_vertical()
        return verticalid
    
    def _fetch_category_id(self):
        self.categoryName = self.operation_data.get('categoryRefDetails', {}).get('categoryName', None)
        if not self.categoryName:
            print(f"Category Name should not be None.")
            sys.exit(1)

        if self.operation_data.get('categoryRefDetails', {}).get('useExisting', False):
            categories = self.get_category()

            found = False
            for id, value in categories.items():
                if value == self.categoryName:
                    found = True
                    return id

            if not found:
                categoryId = self._add_category()
                return categoryId
        else:
            categoryId = self._add_category()
            return categoryId
        
        return None

    def _get_existing_plugin_id(self, plugin_name): #discuss with Rashmi regarding version
        plugins = self.get_plugin_package()

        for plugin_id, plugin_info in plugins.items():
            if plugin_info['pluginName'] == plugin_name:
                return plugin_id
        
        return None
    
    def _get_existing_test_module_id(self, test_module_name): #discuss with Rashmi regarding version
        test_modules = self.get_test_modules()

        for test_module_id, test_module_info in test_modules.items():
            if test_module_info['testModuleName'] == test_module_name:
                return test_module_id

        return None
    
    def _get_existing_security_tool_id(self, tool_name): #discuss with Rashmi regarding version
        tools = self.get_security_tool()

        for tool_id, tool_info in tools.items():
            if tool_info['pluginName'] == tool_name:
                return tool_id
        
        return None

    def _get_existing_application_id(self, application_name):
        applications = self.get_applications()

        for application_id, application_info in applications.items():
            if application_info['applicationName'] == application_name:
                return application_id

        return None

    def _get_existing_local_application_id(self, application_name):
        timeout = 600 # wait till 10mins
        interval = 5 # wait for 5sec intervals
        start_time = time.time()
        while time.time() - start_time < timeout:
            applications = self.get_local_applications()
            for application_id, application_info in applications.items():
                if application_info['applicationName'] == application_name:
                    return application_id  # Return immediately if found
            time.sleep(interval)  # Wait before checking again
        return None  # Return None if not found within the timeout

    def _check_local_application_exists(self, application_name, application_version):
        applications = self.get_local_applications()
        for application_id, application_info in applications.items():
            if application_info['applicationName'] == application_name and application_info['version'] == application_version:
                return application_id  # Return immediately if found
        return None
    

    def _get_app_id_and_action(self, application_name, application_version):
        timeout = 600 # wait till 10mins
        interval = 15 # wait for 15sec intervals
        start_time = time.time()
        while time.time() - start_time < timeout:
            applications = self.get_local_applications()
            for application_id, application_info in applications.items():
                print(application_info)
                if application_info['applicationName'] == application_name and application_info['version'] == application_version \
                    and application_info["status"] == "NOT_INSTALLED":
                    return application_id, "install", None
                elif application_info['applicationName'] == application_name  \
                    and application_info["status"] == "UPDATE_AVAILABLE" and application_info["updateVersion"] == application_version:
                    return application_id, "update", application_info['version']
                elif application_info['applicationName'] == application_name  \
                    and application_info["status"] == "INSTALLED" and application_info["version"] == application_version:
                    return application_id, "skip", None
            time.sleep(interval)  # Wait before checking again
        return None, None, None # Return None if not found within the timeout

    def _get_existing_module_id(self, module_name):
        modules = self.get_modules()

        for module_id, module_info in modules.items():
            if module_info['moduleName'] == module_name:
                return module_id

        return None

    def _fetch_all_test_module_id(self):
        all_test_module_ids = []
        test_module_details = self.module_data.get('testModuleRefDetails', [])

        for detail in test_module_details:
            use_existing = detail.get('useExisting', False)
            test_module_name = detail.get('testModuleName', None)
            self.file_path = detail.get('file_path', None)

            if use_existing:
                test_module_id = self._get_existing_test_module_id(test_module_name)
                if not test_module_id:
                    print(f"Test Module {test_module_name} does not exists.")
                    sys.exit(1)
            else:
                test_module_id = self._upload_test_module()

            all_test_module_ids.append(test_module_id)
        
        return all_test_module_ids

    def _fetch_all_application_id(self):
        all_application_ids = []
        application_details = self.module_data.get('applicatonRefDetails', [])

        for detail in application_details:
            use_existing = detail.get('useExisting', False)
            application_name = detail.get('applicationName', None)

            if use_existing:
                application_id = self._get_existing_application_id(application_name)
                if not application_id:
                    print(f"Application {application_name} does not exists.")
                    sys.exit(1)
            else:
                self.operation_data = detail
                application_id = self._create_application()

            all_application_ids.append(application_id)
        
        return all_application_ids

    def _fetch_all_plugin_id(self):
        all_plugin_ids = []
        plugin_details = self.operation_data.get('pluginPackageRefDetails', [])

        for detail in plugin_details:
            use_existing = detail.get('useExisting', False)
            plugin_name = detail.get('pluginPackageName', None)
            self.file_path = detail.get('file_path', None)

            if use_existing:
                plugin_id = self._get_existing_plugin_id(plugin_name)
                if not plugin_id:
                    print(f"Plugin Package {plugin_name} does not exists.")
                    sys.exit(1)
            else:
                self.function_name = "upload_plugin_package"
                # plugin_id = self._upload_plugin_package()
                plugin_id = self._upload_packages()

            all_plugin_ids.append(plugin_id)
        
        return all_plugin_ids

    def _fetch_vertical_id(self):
        self.verticalName = self.operation_data.get('verticalRefDetails', {}).get('verticalName', None)
        if not self.verticalName:
            print(f"Vertical Name should not be None.")
            sys.exit(1)

        if self.operation_data.get('verticalRefDetails', {}).get('useExisting', False):
            verticals = self.get_vertical()

            found = False
            for id, value in verticals.items():
                if value == self.verticalName:
                    found = True
                    return id

            if not found:
                if not self.vertical_id:
                    self.vertical_id = self._add_vertical()

                return self.vertical_id
        else:
            if not self.vertical_id:
                self.vertical_id = self._add_vertical()

            return self.vertical_id
        
        return None

    def _fetch_app_package_id(self):
        self.appName = self.operation_data.get('appPackageRefDetails', {}).get('appName', None)
        if not self.appName:
            print(f"App Name should not be None.")
            sys.exit(1)

        self.version = self.operation_data.get('appPackageRefDetails', {}).get('version', None)
        self.packageType = self.operation_data.get('appPackageRefDetails', {}).get('packageType', None)

        if self.operation_data.get('appPackageRefDetails', {}).get('useExisting', False):
            if not self.version:
                print(f"App package version can not be None.")
                sys.exit(1)

            app_packages = self.get_app_package()

            found = False
            for app_package_id, app_package_info in app_packages.items():
                if app_package_info['appName'] == self.appName and app_package_info['version'] == self.version:
                    return app_package_id

            if not found:
                print(f"App Package {self.appName} does not exists.")
                sys.exit(1)
        else:
            self.file_path = self.operation_data.get('appPackageRefDetails', {}).get('file_path', None)

            if not os.path.exists(self.file_path):
                print("File doesn't exist.")
                sys.exit(1)

            file_name = self.file_path.split("/")[-1]
            self.packageName = str(file_name)
            self.packageType = self.operation_data.get('appPackageRefDetails', {}).get('packageType', None)
            # app_package_id = self._upload_app_package()
            self.function_name = "upload_app_package"
            app_package_id = self._upload_packages()
            return app_package_id
        
        return None
    
    def _add_category(self):
        if not self.has_inline_args:
            self.categoryName = input('Enter the category name: ')

            while True:
                option = input('Press enter 1 to select a reference vertical or enter 2 to create vertical or enter 3 to terminate operation: \n')
                if option == '1':
                    verticals = self.get_vertical()
                    if len(verticals) == 0:
                        print('No verticals available. Please enter 2 to create vertical or enter 3 to terminate operation.')
                        continue
                    selection = input("Please select a vertical (enter number): ")
                    try:
                        selection_index = int(selection) - 1
                        if 0 <= selection_index < len(verticals):
                            vertical_id = list(verticals.keys())[selection_index]   
                            self.verticalid = vertical_id
                            categoryid = self.add_category()
                            return categoryid
                        else:
                            print("Invalid selection!\n")
                    except ValueError:
                        print("Invalid input! Please enter a number.\n")
                            
                elif option == '2':
                    verticalid = self._add_vertical()
                    self.verticalid = verticalid
                    categoryid = self.add_category()
                    break
                elif option == '3':
                    exit()
                else:
                    print('Invalid input. Please try again.')
        else:
            if not self.categoryName:
                self.categoryName = self.operation_data.get("categoryName", None)

            if not self.categoryName:
                print(f"Category Name should not be None.")
                sys.exit(1)

            self.verticalid = self._fetch_vertical_id()
            categoryid = self.add_category()
            return categoryid
            

    def _delete_category(self):
        categories = self.get_category()
        if not self.has_inline_args:
            if len(categories) == 0:
                    print('No categories available. \n')
                    return
            selection = input("Please select a category (enter number): ")

            try:
                selection_index = int(selection) - 1
                if 0 <= selection_index < len(categories):
                    category_id = list(categories.keys())[selection_index]   
                    self.categoryid = category_id
                    self.delete_category(self.categoryid) 
                else:
                    print("Invalid selection! \n")
                    return
            except ValueError:
                print("Invalid input! Please enter a number. \n")
                return
        else:
            category_details = self.operation_data.get("categoryDetails", [])

            for category in category_details:
                self.categoryName = category.get('categoryName', None)
                if not self.categoryName:
                    print(f"Category Name should not be None.")
                    continue

                found = False
                for id, value in categories.items():
                    if value == self.categoryName:
                        found = True
                        self.categoryid = id

                if not found:
                    print(f"Category {self.categoryName} does not exists.")
                    continue

                self.delete_category(self.categoryid)
    
    def _delete_vertical(self):
        if not self.has_inline_args:
            verticals = self.get_vertical()
            if len(verticals) == 0:
                    print('No verticals available. \n')
                    return
            selection = input("Please select a vertical (enter number): ")

            try:
                selection_index = int(selection) - 1
                if 0 <= selection_index < len(verticals):
                    vertical_id = list(verticals.keys())[selection_index]   
                    self.verticalid = vertical_id
                    self.delete_vertical(self.verticalid)  
                else:
                    print("Invalid selection! \n")
                    return
            except ValueError:
                print("Invalid input! Please enter a number. \n")
                return
        else:
            vertical_details = self.operation_data.get("verticalDetails", [])

            for vertical in vertical_details:
                self.verticalName = vertical.get('verticalName', None)
                if not self.verticalName:
                    print(f"Vertical Name should not be None.")
                    continue

                verticals = self.get_vertical()
                found = False
                for id, value in verticals.items():
                    if value == self.verticalName:
                        found = True
                        self.verticalid = id

                if not found:
                    print(f"Vertical {self.verticalName} does not exists.")
                    continue

                self.delete_vertical(self.verticalid)
        
        

    def _delete_application(self): 
        applications = self.get_applications()
        # print(applications)
        if not self.has_inline_args:
            if len(applications) == 0:
                    print('No applications available. \n')
                    return
            selection = input("Please select an application (enter number): ")

            try:
                selection_index = int(selection) - 1
                if 0 <= selection_index < len(applications):
                    application_id = list(applications.keys())[selection_index]   
                    self.applicationid = application_id
                    self.delete_application(self.applicationid)  
                else:
                    print("Invalid selection! \n")
                    return
            except ValueError:
                print("Invalid input! Please enter a number. \n")
                return
        else:
            application_details = self.operation_data.get("applicationDetails", [])

            for application in application_details:
                application_name = application.get("applicationName", None)
                if not application_name:
                    print(f"Application Name can not be None")
                    continue

                found = False
                for id, value in applications.items():
                    if value.get("applicationName", None) == application_name:
                        found = True
                        self.applicationid = id

                if not found:
                    print(f"Application {application_name} does not exists.")
                    continue

                self.delete_application(self.applicationid)

    def _delete_plugin_package(self):
        plugins = self.get_plugin_package()
        if not self.has_inline_args:
            if len(plugins) == 0:
                    print('No plugin packages available. \n')
                    return
            selection = input("Please select a plugin package (enter number): ")

            try:
                selection_index = int(selection) - 1
                if 0 <= selection_index < len(plugins):
                    plugin_package_id = list(plugins.keys())[selection_index]   
                    self.pluginPackageId = plugin_package_id
                    self.delete_plugin_package(self.pluginPackageId)  
                else:
                    print("Invalid selection! \n")
                    return
            except ValueError:
                print("Invalid input! Please enter a number. \n")
                return
        else:
            plugin_details = self.operation_data.get("pluginDetails", [])

            for plugin in plugin_details:
                plugin_name = plugin.get("pluginName", None)
                if not plugin_name:
                    print(f"Plugin Name can not be None")
                    continue

                self.pluginPackageId = self._get_existing_plugin_id(plugin_name)
                if not self.pluginPackageId:
                    print(f"Plugin Package '{plugin_name}' does not exists.")
                    continue

                self.delete_plugin_package(self.pluginPackageId)
    
    def _delete_app_package(self):
        app_packages = self.get_app_package()
        if not self.has_inline_args:
            if len(app_packages) == 0:
                    print('No app packages available. \n')
                    return
            selection = input("Please select an app package (enter number): ")

            try:
                selection_index = int(selection) - 1
                if 0 <= selection_index < len(app_packages):
                    app_package_id = list(app_packages.keys())[selection_index]   
                    self.appPackageId = app_package_id
                    self.delete_app_package(self.appPackageId)  
                else:
                    print("Invalid selection! \n")
                    return
            except ValueError:
                print("Invalid input! Please enter a number. \n")
                return
        else:
            app_package_details = self.operation_data.get("appPackageDetails", [])

            for app_package in app_package_details:
                app_package_name = app_package.get("appPackageName", None)
                if not app_package_name:
                    print(f"App Package Name can not be None")
                    continue

                found = False
                for id, value in app_packages.items():
                    if value.get("appName", None) == app_package_name:
                        found = True
                        self.appPackageId = id

                if not found:
                    print(f"App Package {app_package_name} does not exists.")
                    continue

                self.delete_app_package(self.appPackageId)
                

    def _delete_test_module_package(self):
        test_modules = self.get_test_modules()
        if not self.has_inline_args:
            if len(test_modules) == 0:
                    print('No test modules available. \n')
                    return
            selection = input("Please select a test module (enter number): ")

            try:
                selection_index = int(selection) - 1
                if 0 <= selection_index < len(test_modules):
                    test_module_id = list(test_modules.keys())[selection_index]   
                    self.testModulePackageId = test_module_id
                    self.delete_test_module_package(self.testModulePackageId)  
                else:
                    print("Invalid selection! \n")
                    return
            except ValueError:
                print("Invalid input! Please enter a number. \n")
                return
        else:
            test_module_details = self.operation_data.get("testModuleDetails", [])

            for test_module in test_module_details:
                test_module_name = test_module.get("testModuleName", None)
                if not test_module_name:
                    print(f"Test Module Package Name can not be None")
                    continue

                found = False
                for id, value in test_modules.items():
                    if value.get("testModuleName", None) == test_module_name:
                        found = True
                        self.testModulePackageId = id

                if not found:
                    print(f"Test Module Package {test_module_name} does not exists.")
                    continue

                self.delete_test_module_package(self.testModulePackageId)

    def _delete_security_tool(self):
        tools = self.get_security_tool()
        if not self.has_inline_args:
            if len(tools) == 0:
                    print('No security tools available. \n')
                    return
            selection = input("Please select a security tool (enter number): ")

            try:
                selection_index = int(selection) - 1
                if 0 <= selection_index < len(tools):
                    securityToolId = list(tools.keys())[selection_index]   
                    self.securityToolPackageId = securityToolId
                    self.delete_security_tool(self.securityToolPackageId)  
                else:
                    print("Invalid selection! Please try again. \n")
                    return
            except ValueError:
                print("Invalid input! Please enter a number. \n")
                return
        else:
            tool_details = self.operation_data.get("securityToolDetails", [])

            for tool in tool_details:
                tool_name = tool.get("toolName", None)
                if not tool_name:
                    print(f"Security Tool package name can not be None")
                    continue

                self.securityToolPackageId = self._get_existing_security_tool_id(tool_name)
                if not self.securityToolPackageId:
                    print(f"Security tool '{tool_name}' does not exist.")
                    continue

                self.delete_security_tool(self.securityToolPackageId)  

    def _delete_module(self): 
        modules = self.get_modules()
        # print(modules)
        if not self.has_inline_args:
            if len(modules) == 0:
                    print('No modules available. \n')
                    return
            selection = input("Please select a module (enter number): ")

            try:
                selection_index = int(selection) - 1
                if 0 <= selection_index < len(modules):
                    module_id = list(modules.keys())[selection_index]   
                    self.moduleId = module_id
                    self.delete_module(self.moduleId)  
                else:
                    print("Invalid selection! \n")
                    return
            except ValueError:
                print("Invalid input! Please enter a number. \n")
                return
        else:
            module_details = self.operation_data.get("moduleDetails", [])
            
            for module in module_details:
                module_name = module.get("moduleName", None)
                if not module_name:
                    print(f"Module Name can not be None")
                    continue

                found = False
                for id, value in modules.items():
                    if value.get("moduleName", None) == module_name:
                        found = True
                        self.moduleId = id

                if not found:
                    print(f"Module {module_name} does not exists.")
                    continue

                self.delete_module(self.moduleId)

    def _upload_test_module(self):
        if self.has_inline_args and self.file_path is None:
            self.file_path = self.operation_data.get("file_path", None)

        selected_file = self.select_listed_files_with_extension(".rtm")
        
        file_name = selected_file.split("/")[-1]
        self.packageName = str(file_name)
        print(f"The test module package name is {self.packageName}")
        
        packageId = self.upload_test_module()
        status, resp_url = self.get_status_of_test_module(packageId)
        print("Getting status of test module package, please wait!")
        module_state_iter = 0
        while (status != "COMPLETED"):
            time.sleep(2)
            status, resp_url = self.get_status_of_test_module(packageId)
            module_state_iter += 1
            if status == "COMPLETED" or status == "ACTIVE" or status == "RUNNING" or status == "SUCCESSFUL":
                break
            if status == "FAILED":
                print('Test module package upload failed! Please check the status of the test module.\n')
                break
            if module_state_iter == 60:
                print('Test module package upload failed! Please check the status of the test module package.\n')
                break
        status, resp_url = self.get_status_of_test_module(packageId)
        print('Uploading test module package, please wait!')
        
        self.upload_package_test_module_to_cloud_mp(resp_url, selected_file)
        status, resp_url = self.get_status_of_test_module(packageId)
        module_state_iter = 0
        while (status != "COMPLETED"):
            time.sleep(2)
            status, resp_url = self.get_status_of_test_module(packageId)
            module_state_iter += 1
            if status == "COMPLETED" or status == "SUCCESSFUL":
                print('Uploaded test module package successfully! \n')
                break
            if status == "FAILED":
                print('Test module package upload failed! Please check the status of the test module.\n')
                break
            if module_state_iter == 60:
                print('Test module package upload failed! Please check the status of the test module package.\n')
                break
        
        time.sleep(20)
        return packageId
    
    def _create_module(self):
        if not self.has_inline_args:
            all_test_modules = []
            while True: 
                option = input('Press enter 1 to select a test module or enter 2 to upload test module or enter 3 to terminate operation. Press Enter to proceed. \n')
                if option == '1':
                    test_modules = self.get_test_modules()
                    if len(test_modules) == 0:
                        print('No test modules available. Please enter 2 to upload test module or enter 3 to terminate operation.')
                        continue
                    selection = input("Please select a test module (enter number): ")
                    try:
                        selection_index = int(selection) - 1
                        if 0 <= selection_index < len(test_modules):
                            test_module_id = list(test_modules.keys())[selection_index]   
                            self.testModulePackageId = test_module_id
                            all_test_modules.append(self.testModulePackageId)
                        else:
                            print("Invalid selection!\n")
                    except ValueError:
                        print("Invalid input! Please enter a number.\n")
                elif option == '2':
                    test_module_id = self._upload_packages()
                    self.testModulePackageId = test_module_id
                    all_test_modules.append(self.testModulePackageId)
                elif option == '3':
                    exit()
                elif option == '':
                    break
                else:
                    print('Invalid input. Please try again.')
        else:
            self.module_data = self.operation_data
            all_test_modules = self._fetch_all_test_module_id()

        if not self.has_inline_args:
            self.moduleName = input('Enter the module name: ')
            self.version = input('Enter the version: ')
            self.description = input('Enter the description: ')
        else:
            if not self.moduleName:
                self.moduleName = self.module_data.get("moduleName", None)
            if not self.version:
                self.version = self.module_data.get("version", None)
            if not self.description:
                self.description = self.module_data.get("description", None)

        if not self.has_inline_args:
            all_application_ids = []
            while True: 
                option = input('Press enter 1 if you have application id or enter 2 to create application or enter 3 to terminate operation. Press Enter to proceed. \n')
                if option == '1':
                    application_ids = self.get_applications()
                    if len(application_ids) == 0:
                        print('No applications are available. Please enter 2 to create application or enter 3 to terminate operation.')
                        continue
                    selection = input("Please select an application (enter number): ")
                    try:
                        selection_index = int(selection) - 1
                        if 0 <= selection_index < len(application_ids):
                            application_id = list(application_ids.keys())[selection_index]   
                            self.applicationid = application_id
                            all_application_ids.append(self.applicationid)
                        else:
                            print("Invalid selection!\n")
                    except ValueError:
                        print("Invalid input! Please enter a number.\n")
                elif option == '2':
                    application_id = self._create_application()
                    self.applicationid = application_id
                    all_application_ids.append(self.applicationid)
                elif option == '3':
                    exit()    
                elif option == '':
                    break 
                else:
                    print('Invalid input. Please try again.') 
        else:
            all_application_ids = self._fetch_all_application_id()

        if not self.has_inline_args:
            while True:
                option = input('Press enter 1 to select a vertical or enter 2 to create vertical or enter 3 to terminate operation: \n')
                if option == '1':
                    verticals = self.get_vertical()
                    if len(verticals) == 0:
                        print('No verticals available. Please enter 2 to create vertical or enter 3 to terminate operation.')
                        continue
                    selection = input("Please select a vertical (enter number): ")
                    try:
                        selection_index = int(selection) - 1
                        if 0 <= selection_index < len(verticals):
                            vertical_id = list(verticals.keys())[selection_index]   
                            self.verticalid = vertical_id
                            break
                        else:
                            print("Invalid selection!\n")
                    except ValueError:
                        print("Invalid input! Please enter a number.\n")
                            
                elif option == '2':
                    verticalid = self._add_vertical()
                    self.verticalid = verticalid
                    break
                elif option == '3':
                    exit()
                else:
                    print('Invalid input. Please try again.')
        else:
            self.operation_data = self.module_data
            self.verticalid = self._fetch_vertical_id() 
               
        moduleId = self.create_module(all_test_modules, all_application_ids)
        return moduleId
    
    def _enable_disable_module(self):
        if not self.has_inline_args:
            modules = self.get_modules()
            if len(modules) == 0:
                    print('No modules available. \n')
                    return
            selection = input("Please select a module (enter number): ")

            try:
                selection_index = int(selection) - 1
                if 0 <= selection_index < len(modules):
                    module_id = list(modules.keys())[selection_index]   
                    self.moduleId = module_id
                    self.enable_status = input('Enter the enable status (enter 1 to enable or enter 2 to disable): ')
                    if self.enable_status == '1':
                        self.enable_status = 'enable'
                    elif self.enable_status == '2':
                        self.enable_status = 'disable'
                    else:
                        print('Invalid input. Please try again.')
                        return
                    
                    self.enable_disable_module(self.moduleId, self.enable_status)
                else:
                    print("Invalid selection! \n")
                    return
            except ValueError:
                print("Invalid input! Please enter a number. \n")
                return
        else:
            module_name = self.operation_data.get("moduleName", None)
            if not module_name:
                print(f"Module Name: {module_name} is invalid.")
                sys.exit(1)

            self.moduleId = self._get_existing_module_id(module_name)
            if not self.moduleId:
                print(f"Module {module_name} does not exist.")
                sys.exit(1)

            self.enable_status = self.operation_data.get("status", None)
            if not self.enable_status or self.enable_status not in ["enable", "disable"]:
                print(f"Toogle Status '{self.enable_status}' is invalid.")
                sys.exit(1)

            self.enable_disable_module(self.moduleId, self.enable_status)
        

    def _enable_disable_application(self):
        if not self.has_inline_args:
            applications = self.get_applications()
            if len(applications) == 0:
                    print('No applications available. \n')
                    return
            selection = input("Please select an application (enter number): ")

            try:
                selection_index = int(selection) - 1
                if 0 <= selection_index < len(applications):
                    application_id = list(applications.keys())[selection_index]   
                    self.applicationid = application_id
                    self.enable_status = input('Enter the enable status (enter 1 to enable or enter 2 to disable): ')
                    if self.enable_status == '1':
                        self.enable_status = 'enable'
                    elif self.enable_status == '2':
                        self.enable_status = 'disable'
                    else:
                        print('Invalid input. Please try again.')
                        return   

                    self.enable_disable_application(self.applicationid, self.enable_status) 
                else:
                    print("Invalid selection! \n")
                    return
            except ValueError:
                print("Invalid input! Please enter a number. \n")
                return
        else:
            application_name = self.operation_data.get("applicationName", None)
            if not application_name:
                print(f"Application Name: {application_name} is invalid.")
                sys.exit(1)

            self.applicationid = self._get_existing_application_id(application_name)
            if not self.applicationid:
                print(f"Application {application_name} does not exist.")
                sys.exit(1)

            self.enable_status = self.operation_data.get("status", None)
            if not self.enable_status or self.enable_status not in ["enable", "disable"]:
                print(f"Toogle Status '{self.enable_status}' is invalid.")
                sys.exit(1)

            self.enable_disable_application(self.applicationid, self.enable_status)


    def _delete_module_set(self):
        self._delete_module()
        time.sleep(5)
        self._delete_application()
        time.sleep(5)
        self._delete_test_module_package()
        time.sleep(5)
        self._delete_app_package()
        time.sleep(5)
        self._delete_plugin_package()
        time.sleep(5)
        self._delete_category()
        time.sleep(5)
        self._delete_vertical()
        time.sleep(5)


    def _get_vertical(self):
        self.get_vertical()
    
    def _get_category(self): 
        self.get_category()  

    def _get_app_package(self): 
        self.get_app_package()

    def _get_applications(self): 
        self.get_applications()

    def _get_test_modules(self): 
        self.get_test_modules()

    def _get_modules(self): 
        self.get_modules() 

    def _get_plugin_package(self):
        self.get_plugin_package()  
    
    def _get_security_tool(self):
        self.get_security_tool()

    def call_function(self, function_name):
        self.function_name = function_name

        if self.function_name not in self.SUPPORTED_OPERATION:
            print(f"Error: Operation '{self.function_name}' is not supported.")
            return None

        if self.function_name == 'add_vertical':
            self._add_vertical()

        elif self.function_name == 'add_category':
            self._add_category()

        elif self.function_name == 'upload_plugin_package':
            self._upload_packages()

        elif self.function_name == 'upload_app_package':
            self._upload_packages()

        elif self.function_name == 'upload_test_module_package':
            self._upload_packages()

        elif self.function_name == 'upload_security_tool_package':
            self._upload_packages()

        elif self.function_name == 'create_application':
            self._create_application()

        elif self.function_name == 'manage_application':
            self._manage_application()

        elif self.function_name == 'create_module':
            self._create_module()
            
        elif self.function_name == 'toggle_application':
            self._enable_disable_application()

        elif self.function_name == 'toggle_module':
            self._enable_disable_module()
            
        elif self.function_name == 'delete_vertical':
            self._delete_vertical()

        elif self.function_name == 'delete_category':
            self._delete_category()

        elif self.function_name == 'delete_plugin_package':
            self._delete_plugin_package()

        elif self.function_name == 'delete_app_package':
            self._delete_app_package()

        elif self.function_name == 'delete_test_module_package':
            self._delete_test_module_package()

        elif self.function_name == 'delete_security_tool_package':
            self._delete_security_tool()
            
        elif self.function_name == 'delete_application':
            self._delete_application()    
                
        elif self.function_name == 'delete_module':
            self._delete_module()

        elif self.function_name == 'get_verticals':
            self._get_vertical()

        elif self.function_name == 'get_categories':
            self._get_category()

        elif self.function_name == 'get_plugin_packages':
            self._get_plugin_package()

        elif self.function_name == 'get_app_packages':
            self._get_app_package()

        elif self.function_name == 'get_test_module_packages':
            self._get_test_modules()

        elif self.function_name == 'get_security_tool_packages':
            self._get_security_tool()

        elif self.function_name == 'get_applications':
            self._get_applications()

        elif self.function_name == 'get_modules':
            self._get_modules()

        elif self.function_name == 'delete_module_set':
            self._delete_module_set()

        else:
            print('Invalid input! Please try again.')

    def cmdloop(self):
        print('\nWelcome to the Cloud Market Place!')
        while True:
            inputs = input('\nEnter 1 to add a vertical \nEnter 2 to add a category \nEnter 3 to upload a package \nEnter 4 to create an application \nEnter 5 to create a module \nEnter 6 to enable/disable an application \nEnter 7 to enable/disable a module \nEnter 8 to delete a vertical \nEnter 9 to delete a category \nEnter 10 to delete a plugin package \nEnter 11 to delete an app package \nEnter 12 to delete a test module package \nEnter 13 to delete a security tool package \nEnter 14 to delete an application \nEnter 15 to delete a module \nEnter 16 to get the verticals \nEnter 17 to get the categories \nEnter 18 to get the plugin packages \nEnter 19 to get the app packages \nEnter 20 to get the test module packages \nEnter 21 to get the security tool packages \nEnter 22 to get applications \nEnter 23 to get modules \nEnter 24 to manage application  \nEnter exit to stop cli \n\n>>> ')

            if inputs == '1':
                self._add_vertical()

            elif inputs == '2':
                self._add_category()
                
            elif inputs == '3':
                self._upload_packages()
                
            elif inputs == '4':
                self._create_application()

            elif inputs == '5':
                self._create_module()
                
            elif inputs == '6':
                self._enable_disable_application()

            elif inputs == '7':
                self._enable_disable_module()
                
            elif inputs == '8':
                self._delete_vertical()

            elif inputs == '9':
                self._delete_category()

            elif inputs == '10':
                self._delete_plugin_package()

            elif inputs == '11':
                self._delete_app_package()

            elif inputs == '12':
                self._delete_test_module_package()

            elif inputs == '13':
                self._delete_security_tool()
                
            elif inputs == '14':
                self._delete_application()    
                   
            elif inputs == '15':
                self._delete_module()

            elif inputs == '16':
                self._get_vertical()

            elif inputs == '17':
                self._get_category()

            elif inputs == '18':
                self._get_plugin_package()

            elif inputs == '19':
                self._get_app_package()

            elif inputs == '20':
                self._get_test_modules()

            elif inputs == '21':
                self._get_security_tool()

            elif inputs == '22':
                self._get_applications()

            elif inputs == '23':
                self._get_modules()

            elif inputs == '24':
                self._manage_application()

            elif inputs == 'exit':
                sys.exit(1)

            else:
                print('Invalid input! Please try again.')        

if __name__ == '__main__':
    mycli = MyCLI()
    mycli.fetch_config()
    if len(sys.argv) < 2:
        mycli.cmdloop()
    else:
        inline_argument = sys.argv[1]
        if inline_argument not in MyCLI.SUPPORTED_OPERATION:
            print(f"Error: Operation '{inline_argument}' is not supported! Please try again.")
            sys.exit(1)

        mycli.fetch_data(inline_argument)
        mycli.call_function(inline_argument)
