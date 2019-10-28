import subprocess
import re
import os
import sys

DELIMITER="|=|"

# PROCESS

class ExecutorManager():

    def execute(self, command, output): raise NotImplementedError

class ProcessManager(ExecutorManager):

    def __init__(self, output, log_name="PROCESS MANAGER"):
        self.outfile = output
        self.log_name = log_name

    def execute(self, command, output=None, returnOutput=False):
        
        if returnOutput:
            with open('/tmp/run', 'w+') as out:
                exit_code, _ = self.execute(command, output=out)
            with open('/tmp/run', 'r+') as out:
                text = out.read()
            self.execute("rm /tmp/run")
            return exit_code, text
        else:
            if output is None:
                output=self.outfile
            exit_code = subprocess.call(command, shell=True, stdout=output, stderr=output)
            return exit_code, None

    def log(self, message, output=None):
        if output is None:
            output=self.outfile
        subprocess.call("echo [ %s ] %s"%(self.log_name, message), shell=True, stdout=output, stderr=output)

    def close(self):
        if self.outfile is not None:
            self.outfile.close()

DefaultProcessManager = ProcessManager(open(os.devnull, 'w'), "DEFAULT PROCESS MANAGER")

# GIT

class GitManager:

    def __init__(self, executor_manager, base_commit):
        self.executor_manager = executor_manager
        self.base_commit = base_commit
        self.executor_manager.execute("git checkout -f %s" % base_commit)

    def change_commit(self,commit_hash):
        with open(os.devnull) as out:
            self.executor_manager.execute("git clean -fdx", out)
        self.executor_manager.execute("git checkout -f %s" % commit_hash)

    def getAllCommits(self):
        _, out = self.executor_manager.execute('git log %s --pretty=format:"%%h%s%%ad%s%%s" --date=iso8601'%(self.base_commit, DELIMITER, DELIMITER), returnOutput=True)
        return out.strip().split('\n')

# DOCKER

class DockerManager():

    containers = set()

    @staticmethod
    def container_exist(container_id):
        return DefaultProcessManager.execute("docker inspect -f {{.State.Running}} %s"%container_id) == "true"

    @staticmethod
    def execute(docker_image, project, command, output, pm=DefaultProcessManager):
        """Executes 'command' in a Docker container created by 'docker_image'.
            If container does not exist, then create one and executes 'command'
            
            Keyword arguments:
            
                docker_image -- An existing Docker image. If not is available locally, it will be downladed
                
                project      -- Project folder name which container uses as work-directory
                
                command      -- Bash command which will be execute in the container
                
                output       -- File path to store docker logs
                
                pm           -- Process manager which gona executes (and gets the outputs) the Docker command
        """
        container_id = "aux-container-%s-%s"% (re.sub('[:/]', '_', docker_image),project)
        
        if container_id not in DockerManager.containers:
            # NOT EXISTS -> CREATE
            workdir = "/home/bugs/projects/%s" % project
            pm.execute("docker run --rm --name %s --volumes-from $HOSTNAME -d -w %s %s tail -f /dev/null"%(container_id,workdir,docker_image))
            DockerManager.containers.add(container_id)
        
        with open(output, "w+") as out:
            return pm.execute("docker exec %s %s"%(container_id, command), out)

    @staticmethod
    def shutdownContainers(pm=DefaultProcessManager):
        for container_id in DockerManager.containers:
            pm.execute("docker stop %s"%container_id)
            pm.execute("docker rm %s"%container_id)
            


if __name__ == "__main__":
    DockerManager.execute("maes95/java-maven:8", "Lang", "bash", "log")
    