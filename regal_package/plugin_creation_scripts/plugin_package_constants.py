class Constants:
    """This class define all constants used in PluginPackageValidator"""
    TOPOLOGY = "topology"
    TOPOLOGY_IMAGES = "topologyImages"
    SOLUTION_STACK = "solutionStack"
    INFRAPROFILE = "infraProfile"
    TEST_CASES = "testCases"
    TEST_PLAN = "testPlan"
    TEST_SUITES = "testSuites"
    TEST_CASE_CONFIG = "tc_config.json"
    SOLUTION_STACK_REQUIRED_FIELDS = ["solutionStackName", "solutionStackVersion", "os"]
    TOPOLOGY_NODE_REQUIRED_FIELDS = ["nodeName", "nodeType", "deploymentOrder", "cpu", "ram", "os"]
    TOPOLOGY_REQUIRED_FIELDS = ["topologyName", "topologyType", "description", "nodes"]
    INFRAPROFILE_REQUIRED_FIELDS = ["infraProfileName", "tagName", "topologyName", "solutionStackName", "solutionStackVersion"]
    TEST_PLAN_REQUIRED_FIELDS = ["testPlanName", "testPlanTestCases"]

