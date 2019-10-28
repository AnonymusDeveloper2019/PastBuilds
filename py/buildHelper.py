import json
import os
import re
from utils import DefaultProcessManager, GitManager, DockerManager

NO_BUILD_MESSAGE="BuildAnalycer: No build system detected"

DOCKER_IMAGE = "java-maven:8"

BUILD_SYSTEMS=[
    { "build_system": "Maven", "build_file": "pom.xml", "build_command": lambda build_file : "mvn clean install -Dmaven.test.skip=true"},
    { "build_system": "Gradle", "build_file": "gradlew", "build_command": lambda build_file : "%s build -x test"%build_file},
    { "build_system": "Ant", "build_file": "build.xml", "build_command": lambda build_file : "ant compile -f %s"%build_file}
]

class BuildHelper():

    def __init__(self, pm):
        self.pm = pm

    def getBuildConfigs(self, previous_build=None):

        """
            Return a config file like this: 
            {
                "build_system": " Maven | Ant | Gradle ",
                "docker_image": " java-maven:8 ",
                "build_command": "<bash_script>",
                "build_file": "<build_file_path>"
            }
        """

        build_configs = []

        # GETTING BUILD SYSTEMS

        self.pm.log("Getting build system")
        
        for bs in BUILD_SYSTEMS:

            depth = 1
            while(depth < 3):
                # CHECK EVERY BUILD SYSTEM (IF EXIST)
                exist, buildfile = self.searchBuildFile(depth, bs["build_file"])
                if exist:
                    build_config = {
                        "build_system": bs["build_system"],
                        "docker_image": DOCKER_IMAGE,
                        "build_command": bs["build_command"](buildfile),
                        "build_file": buildfile,
                        "works": False
                    }
                    build_configs = build_configs + [build_config]
                    break
                depth+=1

        if len(build_configs) == 0:
            # NO BUILD SYSTEM DETECTED
            build_config = {
                "build_system": "NOT_FOUND",
                "docker_image": "-",
                "build_command": "echo '%s' && exit 1"%NO_BUILD_MESSAGE,
                "build_file": "-",
                "works": False
            }
            return [build_config]
        else:
            return build_configs

    def executeBuildSystem(self, project, build_config, log_file):

        if build_config['build_system'] == "NOT_FOUND":
            # Write failed log
            with open(log_file, "w+") as out: out.write(NO_BUILD_MESSAGE)
            return -1
        else:
            self.applyFixes(build_config['build_system'])
            exit_code, _ = DockerManager.execute(build_config["docker_image"], project, build_config["build_command"], log_file)
            return exit_code
    
    def searchBuildFile(self, depth, file_name):
        _, result = self.pm.execute('find . -maxdepth %d -name "%s"'%(depth, file_name), returnOutput=True)
        if result != "":
            result = result.split('\n')
            result.remove("")
            result.sort(key=len)
            buildfile = result[0]
            return True, buildfile
        else:
            return False, ""
    
    def applyFixes(self, build_system):

        if build_system == "Gradle":
            self.applyGradleFixes()

    
    def applyGradleFixes(self):
        # Exclude task
        exclude_task="""
            for filename in $(find . \( -iname "build.gradle" \)); do
                if   [ -f "${filename}" ]in
                then 
                    echo '
                    if (project.hasProperty("tasks")){tasks.withType(Test) {enabled = false}}' >> $filename
                    echo '
                    if (project.hasProperty("tasks")){tasks.withType(Javadoc) {enabled = false}}' >> $filename
                fi
            done
        """
        self.pm.execute(exclude_task)
        self.pm.log("FIX FOR GRADLE BUILD APPLIED: SKIP TEST AND JAVADOC TASK")

# JUST FOR TEST
if __name__ == "__main__":
    config = {
        "project": "Closure",
        "init_commit": "49e9565f"
    }
    os.chdir("projects/%s" % config['project'])
    fb = BuildHelper(config)
    bsc = fb.analyzeBuildSystem()
    print(bsc)

    
    
    