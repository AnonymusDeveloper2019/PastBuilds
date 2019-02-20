import subprocess
import re
import os

# COLORS

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GREY = '\u001b[38;5;245m'

class Message:
    START = "> STARTING SEARCH REGRESSION IN PROYECT %s. GOING TO FIX COMMIT"
    REACHED_LIMIT_FORWARD = "> PROJECT COMMITS LIMIT REACHED: GO %d COMMITS FORWARD"
    REACHED_LIMIT_BACK="> PROJECT COMMITS LIMIT REACHED: GO %d COMMITS BACK"
    GO_FORWARD = "> GO %d COMMITS FORWARD (%d commits from fix commit)"
    GO_BACK = "> GO %d COMMITS BACK (%d commits from fix commit)"
    FIXED_PASS = "\033[95m%s\033[0m commit \033[92mpass\033[0m the test (FIXED COMMIT)"
    ERROR = "\033[95m%s\033[0m commit \033[91mhad an error\033[0m when test was running, no test report found"
    BUILD_ERROR = "\033[95m%s\033[0m commit \033[91mhad an error\033[0m: Can't build project"
    TEST_ERROR = "\033[95m%s\033[0m commit \033[91mhad an error\033[0m: An error occurred when the test was running"
    FAIL = "\033[95m%s\033[0m commit \033[91mdoesn't pass\033[0m the test"
    SUCCESS = "\033[95m%s\033[0m commit \033[92mpass\033[0m the test"
    ERROR_TO_FAIL_END = "\033[95m%s\033[0m commit contains an error, \033[95m%s\033[0m fail at test, no regression detected"
    SUCCESS_END = "\033[95m%s\033[0m commit \033[92mpass\033[0m the test, \033[95m%s\033[0m commit is a \033[91mregression\033[0m"
def printc(c,s):
        print(c+s+bcolors.ENDC)

def escape_ansi(line):
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)

# PROCESS

class ProcessManager:

    def __init__(self, output, log_name="PROCESS MANAGER"):
        self.outfile = output
        self.log_name = log_name

    def call(self, params, output=None):
        if output is None:
            output=self.outfile
        return subprocess.call(params, shell=True, stdout=output, stderr=output)

    def log(self, message, output=None):
        if output is None:
            output=self.outfile
        subprocess.call("echo [ %s ] %s"%(self.log_name, message), shell=True, stdout=output, stderr=output)

    def runAndGetOutput(self, command):
        text=""
        with open('run', 'w') as out:
            self.call(command, output=out)
        with open('run', 'r') as out:
            text = out.read()
        self.call("rm run")
        return text

DefaultProcessManager = ProcessManager(open(os.devnull, 'w'), "DEFAULT PROCESS MANAGER")

# GIT

class NoValidCommitException(Exception):
        """Raised when output isn't a hash of commit"""
        pass

class GitManager:

    def __init__(self, manager, base_commit):
        self.process_manager = manager
        self.base_commit = base_commit
        self.pos=0

    def get_previous_commit(self,n=1):
        commit = self.process_manager.runAndGetOutput("git show HEAD~%d | head -n 1 |  cut -d' ' -f2" % n)
        # Commit len is 40 characters + \n
        if commit is "" or len(commit) is not 41:
            raise NoValidCommitException
        return commit.strip()

    def get_forward_commit(self, n=1):
        new_n = abs(self.pos+n)
        commit = self.process_manager.runAndGetOutput("git show %s~%d | head -n 1 |  cut -d' ' -f2" % (self.base_commit, new_n) )
        if commit is "":
            print("%d : %d"%(self.pos,n))
            raise NoValidCommitException
        return commit.strip()

    def change_commit(self,commit_hash):
        self.process_manager.call("git checkout -f %s" % commit_hash)
        self.process_manager.call("git clean -fd")

    def go_back(self, n=1):
        commit = self.get_previous_commit(n)
        self.change_commit(commit)
        self.pos-=n
        return commit

    def go_forward(self, n=1):
        commit = self.get_forward_commit(n)
        self.change_commit(commit)
        self.pos+=n
        return commit

    def current_pos(self):
        return self.pos

    def getAllCommits(self):
        out = self.process_manager.runAndGetOutput("git log --oneline").strip()
        return out.split('\n')
        
    
    