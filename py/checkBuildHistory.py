# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import datetime
import time
import csv
import json
from time import gmtime, strftime
from utils import bcolors, printc, ProcessManager, GitManager, escape_ansi, NoValidCommitException, DefaultProcessManager

class BuildChecker():

    HEADERS = ["id", "commit", "build", "exec_time", "comment", "fix"]

    def __init__(self, project, init_commit, last_commit, experiment, base_report=None, fix="NO"):

        self.project = project
        self.experiment = int(experiment)
        self.base_report = base_report
        self.fix = fix
        
        self.init_commit = init_commit
        self.last_commit = last_commit
        self.path = '%s/analysis/%s/experiment_%s/'%(os.getcwd(), self.project, self.experiment)
        self.logs_path = "%s/logs/"%(self.path)
        self.general_logs_path = "%s/general_logs/"%(self.path)

        self.build_script_path = "%s/configFiles/BuildFiles/build-%s.sh"%(os.getcwd(), self.project)

        self.out_report = "%s/report_experiment_%d.csv"%(self.path,self.experiment)
        if self.base_report is None or os.path.isfile(self.out_report): self.base_report = self.out_report

        if not os.path.isdir(self.path):
            os.makedirs(self.path)
            if not os.path.isfile(self.build_script_path):
                with open(self.build_script_path, "w+") as _file:
                    _file.write("exit 1")
                DefaultProcessManager.call("chmod +x %s"%self.build_script_path)
                print("WRITE A BUILD SCRIPT FOR PROJECT AT %s"%self.build_script_path)  
                exit()  

        if not os.path.isdir(self.logs_path):
            os.makedirs(self.logs_path)
        if not os.path.isdir(self.general_logs_path):
            os.makedirs(self.general_logs_path)
    
        self.pm = ProcessManager(open(self.general_logs_path+"general-"+strftime("%d%b%Y_%X", gmtime())+".log", 'w+'), "BUILD CHECKER")
        self.gm = GitManager(self.pm, self.init_commit)

        # MOVE TO PROJECT
        os.chdir("projects/%s" % self.project)
        self.gm.change_commit(self.init_commit)
        if not os.path.isfile(self.out_report):
            self.createCSVFile()

        # READ LAST REPORT
        with open(self.base_report) as csvfile:
            reader = csv.DictReader(csvfile)
            csvDict = dict()
            for row in reader:
                csvDict[row['commit']] = row
            # SORT ITEMS BY ID (DON'T NEED IT IN PYTHON 3.6)
            self.csvItems = sorted(csvDict.items(), key=lambda tup: int(tup[1]['id']) )

    def checkBuild(self, n=100):

        self.pm.log("CHECK BUILD FOR EXPERIMENT %d" % self.experiment)

        count = 0
        total = n
        for c_hash, commit in self.csvItems:

            count = count + 1

            commit['fix'] = json.loads(commit['fix'].replace("\'", "\""))

            reBuild = self.fix is not None and commit['build'] ==  "FAIL"
            alreadyCheckedByFix = 'lastFix' in commit['fix'] and commit['fix']['lastFix'] == self.fix

            if (commit['build'] == "NO" or reBuild) and not alreadyCheckedByFix:

                # NO BUILD CHECKED OR REBUILD

                self.buildProject(c_hash, commit, reBuild)

                n-=1
                if n == 0: break
            
            else:

                # BUILD CHECKED
                
                if commit['build'] == "SUCCESS":
                    self.pm.log("%s commit already checked: SUCCESS" % c_hash)
                if commit['build'] == "FAIL":
                    self.pm.log("%s commit already checked: FAIL" % c_hash)
            
            print("Builds checked : "+str(count)+"/"+str(total), end="\r")
            
            if c_hash == self.last_commit: break


    def buildProject(self, c_hash, commit, reBuild):

        if reBuild:
            self.pm.log("%s commit gona be re-checked" % c_hash)
        else:
            self.pm.log("%s commit gona be checked" % c_hash)

        self.gm.change_commit(c_hash)
        log_file = self.logs_path+str(commit['id'])+"-"+c_hash+".log"
        with open(log_file, "w+") as log:
            start = round(time.time())
            returncode = self.pm.call("bash %s"%self.build_script_path, log)
            commit['exec_time'] = round(time.time()) - start
            
        if returncode == 0:
            # SUCCESS BUILD
            self.pm.log("%s commit build success" % c_hash)

            # CHANGE IN BUILD FIX COMMIT BUILD
            if reBuild and commit['build'] == "FAIL":
                self.pm.log("%s commit was fixed by %s" % (c_hash, self.fix))
                commit['fix']['fixFail'] = self.fix

            commit['build'] = "SUCCESS"
            self.pm.call("rm %s"%log_file)
        else:
            # BUILD FAIL
            self.pm.log("%s commit build fail" % c_hash)

            # CHANGE IN BUILD BREAKS COMMIT BUILD
            if reBuild and commit['build'] == "SUCCESS":
                self.pm.log("%s commit was broken by %s" % (c_hash, self.fix))
                commit['fix']['breaksSuccess'] = self.fix

            commit['build'] = "FAIL"
        
        commit['fix']['lastFix'] = self.fix
        self.updateFile()
            

    def createCSVFile(self):
        with open(self.out_report, 'w+') as csvfile: 
            writer = csv.DictWriter(csvfile, fieldnames = self.HEADERS) 
            commits = []
            n=0
            for commit in self.gm.getAllCommits():
                commits.append({
                    "id": n,
                    "commit": commit.split(" ", 1)[0],
                    "build": "NO",
                    "exec_time": 0,
                    "comment": commit.split(" ", 1)[1],
                    "fix": {}
                })
                n+=1
            writer.writeheader()
            writer.writerows(commits)

    def updateFile(self):
        with open(self.out_report, 'w+') as csvfile: 
            writer = csv.DictWriter(csvfile, fieldnames = self.HEADERS) 
            writer.writeheader()
            for _, commit in self.csvItems:
                writer.writerow(commit)
        

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Use: python py/checkBuildHistory.py <config> <?fix>")
        exit()

    config = json.load(open(sys.argv[1]))

    if len(sys.argv) > 2:
        # FIX HASH PRESENT
        absolute_path = config['absolute_path_to_base_report']
        if config['absolute_path_to_base_report'] == "": absolute_path = None
        bcheck = BuildChecker(config['project'], config['init_commit'], config['last_commit'], config['experiment'], absolute_path, sys.argv[2])
    else:
        bcheck = BuildChecker(config['project'], config['init_commit'], config['last_commit'], config['experiment'])
    
    bcheck.checkBuild(int(config['number_of_builds']))
    bcheck.updateFile()

