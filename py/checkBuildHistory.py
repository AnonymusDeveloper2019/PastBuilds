# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import datetime
import time
import csv
import json
import pickle
import json
from time import gmtime, strftime
from buildHelper import BuildHelper
from utils import ProcessManager, GitManager, DefaultProcessManager, DockerManager, DELIMITER

class BuildChecker():

    HEADERS = ["id", "commit", "build", "exec_time", "date", "comment"]

    def __init__(self, config_file_path, test=False):

        with open(config_file_path) as config_file:
            self.config = json.load(config_file)
        self.config['experiment'] = int(self.config['experiment'])
        self.firstTime = False
        self.test = test
        self.config['init_commit'] = self.config['init_commit'][0:8]
        
        # PATHS
        self.root = os.getcwd()
        self.path = '%s/analysis/%s/experiment_%s/'%(self.root, self.config['project'], self.config['experiment'])
        self.build_files_path = "%s/build_files/"%(self.path)
        self.logs_path = "%s/logs/"%(self.path)
        self.general_logs_path = "%s/general_logs/"%(self.path)
        self.out_report = "%s/report_experiment_%d.csv"%(self.path,self.config['experiment'])

        if not os.path.isdir(self.path):
            # FIRST EXECUTION
            self.firstTime = True
            os.makedirs(self.logs_path)
            os.makedirs(self.general_logs_path)
            os.makedirs(self.build_files_path)
        
        self.pm = ProcessManager(open(self.general_logs_path+"general-"+strftime("%d%b%Y_%X", gmtime())+".log", 'w+'), "BUILD CHECKER")
        self.gm = GitManager(self.pm, self.config['init_commit'])
        
        if self.firstTime:
            # FIRST EXECUTION
            self.createCSVFile()

        # READ LAST REPORT
        with open(self.out_report) as csvfile:
            reader = csv.DictReader(csvfile)
            self.csvDict = dict()
            for row in reader:
                self.csvDict[row['commit']] = row
            # SORT ITEMS BY ID (DON'T NEED IT IN PYTHON 3.6)
            self.csvItems = sorted(self.csvDict.items(), key=lambda tup: int(tup[1]['id']) )
            # Set number of builds to total builds 
            if self.config['number_of_builds'] == "All":
                self.config['number_of_builds'] = len(self.csvItems)

        # MOVE TO PROJECT
        os.chdir("projects/%s" % self.config['project'])
       

    def checkBuild(self):

        self.pm.log("CHECK BUILD FOR EXPERIMENT %d" % self.config['experiment'])
        n = self.config['number_of_builds']
        count = 0
        total = n
        build_config = self.config.get('build_config')
        for c_hash, commit in self.csvItems:

            count = count + 1

            if (commit['build'] == "NO"):

                # NO BUILD CHECKED

                build_config = self.buildProject(c_hash, commit, build_config)

                # SAVE BUILD FILE

                self.saveBuildFile(commit, c_hash, build_config)

                n-=1
                if n == 0: break
            
            else:

                # BUILD CHECKED
                
                if commit['build'] == "SUCCESS":
                    self.pm.log("%s commit already checked: SUCCESS" % c_hash)
                if commit['build'] == "FAIL":
                    self.pm.log("%s commit already checked: FAIL" % c_hash)
            
            if not self.test:
                print("Builds checked : "+str(count)+"/"+str(total), end="\r")

    def finish(self, msg):
        # RESTORE STATE AND CLOSE FILES
        self.pm.log(msg)
        #DockerManager.shutdownContainers()
        os.chdir(self.root)
        self.pm.execute("chmod -R ugo+rw %s/analysis/"%self.root)
        self.pm.close()

    def buildProject(self, c_hash, commit, build_config, i = 1):

        self.pm.log("%s commit gona be checked" % c_hash)

        fb = BuildHelper(self.pm)

        # GO TO  COMMIT 
        self.gm.change_commit(c_hash)

        # PATH WHERE LOG WILL BE STORE
        log_file_template = self.logs_path+str(commit['id'])+"-"+c_hash+"-attempt-%d.log"

        build_configs = fb.getBuildConfigs(build_config)

        for idx, bc in enumerate(build_configs):

            exit_code = fb.executeBuildSystem(self.config["project"], bc, log_file_template%(idx+1))

            if exit_code == 0:
                # SUCCESS
                self.pm.log("%s commit build success" % c_hash)
                commit['build'] = "SUCCESS"
                bc = bc.copy()
                bc["builds_checked"] = build_configs
                self.updateFile()
                return bc
        
        # NO BUILD WORKS 
        self.pm.log("%s commit build fail" % c_hash)
        commit['build'] = "FAIL"
        # RETURN FIRST BUILD CONFIG DETECTED, RETURN ALL BUILDS AS A PARAM
        bc = build_configs[0].copy()
        bc["builds_checked"] = build_configs
        self.updateFile()
        return bc    
            

    def saveBuildFile(self, commit, c_hash, build_config):
        filename = str(commit['id'])+"-"+c_hash+"-build.json"
        with open(self.build_files_path+filename,'w+') as json_file:
            data = {
                "commit": c_hash,
                "build_system": build_config["build_system"],
                "docker_image": build_config["docker_image"],
                "build_command": build_config["build_command"],
                "build_file": build_config["build_file"],
                "builds_checked": build_config["builds_checked"],
                "works": commit['build'] == "SUCCESS"
            }
            json.dump(data, json_file, indent=4)

            

    def createCSVFile(self):
        # GO PROJECT FOLDER
        os.chdir("projects/%s" % self.config['project'])
        with open(self.out_report, 'w+') as csvfile: 
            writer = csv.DictWriter(csvfile, fieldnames = self.HEADERS) 
            commits = []
            n=0
            for commit in self.gm.getAllCommits():
                commit_hash, date, comment = commit.split(DELIMITER)
                commits.append({
                    "id": n,
                    "commit": commit_hash[0:8],
                    "build": "NO",
                    "exec_time": 0,
                    "date": date,
                    "comment": comment
                })
                n+=1
            writer.writeheader()
            writer.writerows(commits)
        # GO BACK
        os.chdir(self.root)

    def updateFile(self):
        with open(self.out_report, 'w+') as csvfile: 
            writer = csv.DictWriter(csvfile, fieldnames = self.HEADERS) 
            writer.writeheader()
            for _, commit in self.csvItems:
                writer.writerow(commit)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Use: python py/checkBuildHistory.py <config_file_path>")
        exit()

    bcheck = BuildChecker(sys.argv[1])

    try:
        bcheck.checkBuild()
    except KeyboardInterrupt as e:
        bcheck.finish("FINISHED EXPERIMENT WITH KeyboardInterrupt")
    except Exception as e:
        bcheck.pm.log("Exception: %s"%e)
        bcheck.finish("FINISHED EXPERIMENT WITH AN EXCEPTION")
    else:
        bcheck.finish("FINISHED EXPERIMENT SUCCESSFULLY")



