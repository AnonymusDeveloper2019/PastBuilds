
# coding: utf-8

import csv
import pandas as pd
import matplotlib.pyplot as plt
import re
import hashlib
import numpy as np
import pickle
from matplotlib import rc
import os
import json

class ProjectAnalysis():

    def __init__(self, project, n):
        self.project= project
        self.path= "../../analysis/%s/experiment_%d"%(self.project, n)
        self.report="%s/report_experiment_%d.csv"%(self.path, n)

        dateparse = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S %z')
        self.data= pd.read_csv(self.report, parse_dates=['date'], date_parser=dateparse)

        self.data['date'] = pd.to_datetime(self.data['date'],utc=True)

        with open(self.report) as csvfile:
            reader = csv.DictReader(csvfile)
            self.csvDict = dict()
            for row in reader:
                self.csvDict[row['commit']] = row
            
    def df(self):
        return self.data

    def stats(self):
        success = self.df()[(self.df()['build'] == 'SUCCESS')]['id'].count()
        fail    = self.df()[(self.df()['build'] == 'FAIL')]['id'].count()
        total   = self.df()['id'].count()
        print("TOTAL: %d"%total)
        print("SUCCESS: %d"%success)
        print("FAIL: %d"%fail)
        print("SUCCESS RATIO: "+str(success*100/total)+"%")
        print("FAIL RATIO: "+str(fail*100/total)+"%")

    def plot_and_save_histogram(self, jump):
        total_commits = len(self.df())+jump
        limit = len(self.df())

        data = self.df()
        fails_list=[]
        success_list=[]
        for _, row in data.iterrows():
            if row['build'] == "SUCCESS":
                success_list.append(len(data)-row['id']-1)
            else:
                fails_list.append(len(data)-row['id']-1)

        bins = np.arange(0,total_commits,jump)

        fig, ax = plt.subplots(figsize=(8, 1))
        _, bins, patches = plt.hist([np.clip(success_list, bins[0], bins[-1]),
                                    np.clip(fails_list, bins[0], bins[-1])],
                                    #normed=1,  # normed is deprecated; replace with density
                                    stacked=True,
                                    #density=True,
                                    bins=bins, color=['#4b8869', '#a82e2e'], 
                                    label=['SUCCESS', 'FAIL']
                                    )
        if jump > 100:
            xlabels = bins[1:].astype(str)
            xlabels[-1] += '+'
            plt.xticks(rotation=45)
            N_labels = len(xlabels)
            plt.xticks(jump * np.arange(N_labels) + jump/2)
            ax.set_xticklabels(xlabels)
        
        #ax.set_xlabel("Commits from beginning of project to last commit")
        
        plt.xticks(rotation=45)

        plt.yticks([])
        #plt.title(title, fontsize=20)
        plt.setp(patches, linewidth=0)
        #plt.legend(loc='upper left', prop={'size': 12})

        fig.tight_layout()
        plt.xlim([0, limit])
        plt.ylim([0, jump])
        plt.tick_params(axis='both', labelsize=14)
        
        plt.savefig(self.path+('%sHist.png'%self.project))
        plt.show()
    
    def plot_and_save_histogram_advance(self,jump):
        total_commits = len(self.df())+jump
        limit = len(self.df())

        data = self.df()

        dev_list=[]
        context_list=[]
        grey_list=[]
        success_list=[]
        for _,row in data.iterrows():
            if row['build'] == "SUCCESS":
                success_list.append(len(data)-int(row['id'])-1)
            else:
                if self.csvDict[row['commit']]['type'] == "DEVELOPER_ERROR":
                    dev_list.append(len(data)-int(row['id'])-1)
                if self.csvDict[row['commit']]['type'] == "CONTEXT_ERROR":
                    context_list.append(len(data)-int(row['id'])-1)
                if self.csvDict[row['commit']]['type'] == "NOT_DETECTED":
                    grey_list.append(len(data)-int(row['id'])-1)

        bins = np.arange(0,total_commits,jump)

        fig, ax = plt.subplots(figsize=(16, 2))
        _, bins, patches = plt.hist([   np.clip(success_list, bins[0], bins[-1]),
                                        np.clip(dev_list, bins[0], bins[-1]),
                                        np.clip(context_list, bins[0], bins[-1]),
                                        np.clip(grey_list, bins[0], bins[-1])],
                                        #normed=1,  # normed is deprecated; replace with density
                                        stacked=True,
                                        #density=True,
                                        bins=bins,  color=['#4b8869', '#a82e2e', '#f2711c', '#909090'], 
                                        label=['SUCCESS', 'DEVELOPER_ERROR', 'CONTEXT_ERROR', 'NOT_DETECTED']
                                    )
        if jump > 100:
            xlabels = bins[1:].astype(str)
            xlabels[-1] += '+'
            plt.xticks(rotation=45)
            N_labels = len(xlabels)
            plt.xticks(jump * np.arange(N_labels) + jump/2)
            ax.set_xticklabels(xlabels)
        
        #ax.set_xlabel("Commits from beginning of project to last commit")
        
        plt.xticks(rotation=45)

        plt.yticks([])
        #plt.title(title, fontsize=20)
        plt.setp(patches, linewidth=0)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.02),
          fancybox=True, shadow=True, ncol=4, prop={'size': 12})

        fig.tight_layout()
        plt.xlim([0, limit])
        plt.ylim([0, jump])
        plt.tick_params(axis='both', labelsize=14)
        plt.savefig(self.path+('%sHist-Advance.png'%self.project))
        
        plt.show()
    
    def get_fails_and_grouped_fails(self):
        groups_of_fails = []
        fails = []
        current_group = []
        for k,v in self.csvDict.items():
            if v['build'] == "SUCCESS" and len(current_group)>0:
                groups_of_fails.append(current_group)
                current_group = []
            if v['build'] == "FAIL":
                current_group.append(v)
                fails.append(v)
        if len(current_group)>0:
            groups_of_fails.append(current_group)

        logs_path = self.path+'/logs/'
        for fail in fails:
            logs = [f for f in os.listdir(logs_path) if re.match(r'%s-%s-attempt-\d.log'%(fail['id'], fail['commit']), f)]
            selected_log = self.selectLog(logs, fail) 
            if selected_log is "indeterminate":
                fail['log'] = "Can't determine log"
            else:
                with open(logs_path+selected_log) as f: 
                    r_data = f.read()
                    fail['log'] = r_data
        return (fails, groups_of_fails)

    def cleanLog(self, text):
        return text.replace('\n', ' ').replace('\t', ' ')

    def selectLog(self,logs, fail):
        if len(logs) == 1:
            return logs[0]
        elif len(logs) == 2:
            # MAVEN OR GRADLE
            first_log = [l for l in logs if l.endswith('-1.log')][0]
            # ANT
            second_log = [l for l in logs if l.endswith('-2.log')][0]
            forward_build_success = None
            past_build_success    = None
            all_commits = self.data.values.tolist()
            
            # SEARCH NEWEST-NEARLY COMMIT THAT WORKS
            forward_aux = int(fail['id']) - 1
            while(forward_aux > 0):
                current_commit = all_commits[forward_aux]
                logs_path=self.path+"/build_files/%d-%s-build.json"%(forward_aux, current_commit[1])
                with open(logs_path) as f: 
                    data = json.load(f)
                if data['works']:
                    forward_build_success = data['build_system']
                    break
                forward_aux = forward_aux - 1
            
            # SEARCH OLDER-NEARLY COMMIT THAT WORKS
            back_aux = int(fail['id']) + 1
            while(back_aux < 0):
                current_commit = all_commits[back_aux]
                logs_path=self.path+"/build_files/%d-%s-build.json"%(back_aux, current_commit[1])
                with open(logs_path) as f: 
                    data = json.load(f)
                if data['works']:
                    past_build_success = data['build_system']
                    break
                back_aux = back_aux + 1
            
            if forward_build_success == "Ant":
                return second_log
            else: # forward_aux == MAVEN OR GRADLE
                if past_build_success == "Ant":
                    return "indeterminate"
                else:
                    return first_log
        else:
            raise Exception("3 build system")

    def addError(self, errors, error_text, commit, error_type="NOT_DETECTED"):
        hash_object = hashlib.md5(error_text.encode())
        hash_key = hash_object.hexdigest()
        if hash_key in errors:
            errors[hash_key]['count'] +=1
            errors[hash_key]['commits'].append(commit)
        else:
            errors[hash_key] = {
                'key': hash_key,
                'trace': self.cleanLog(error_text),
                'commits': [commit],
                'count': 1,
                'type': error_type
            }
        return hash_key

    def group_errors_by_log(self, fails, common_errors):

        errors=dict()

        for fail in fails:
            
            detected = False
            
            for error_tuple in common_errors:
                
                groups = [0]

                if len(error_tuple)== 3:
                    log_template, error_type, groups = error_tuple 
                else:
                    log_template, error_type         = error_tuple

                s = re.search(log_template, fail['log'])
                if s is not None:
                    text = ""
                    for g in groups:
                        text += s.group(g)
                    hash_key = self.addError(errors, text, fail['commit'], error_type)
                    fail['type'] = error_type
                    self.csvDict[fail['commit']]['type'] = error_type
                    self.csvDict[fail['commit']]['hash'] = hash_key
                    detected = True
                    break

            if not detected:
                fail['type'] = "NOT_DETECTED"
                self.csvDict[fail['commit']]['type'] = "NOT_DETECTED"
                self.csvDict[fail['commit']]['hash'] = "a895d834a1be13e5923f9d07b534b2bb"
                if len(fail['log']) > 300:
                    self.addError(errors, fail['log'][0:300]+" ... <LOG TOO LONG> ...", fail['commit'])
                else:
                    self.addError(errors, fail['log'], fail['commit'])

        return errors

    def view_log_by_hash(self, errors, hash_id, n=0):
        total = len(errors[hash_id]["commits"])
        commit = self.csvDict[errors[hash_id]["commits"][n]]['commit']
        log = self.csvDict[errors[hash_id]["commits"][n]]['log']
        # self.csvDict[errors[hash_id]["commits"][n]]['log']
        print("Total commits: %d | Current commit: %s | Log: \n\n%s "%(total, commit, log))
    
    def save_failed_commits(self, errors, hash_id):
        file_path = '%sfailed_commits_%s.pkl'%(self.path, hash_id)
        with open(file_path, 'wb') as f:
            pickle.dump(errors[hash_id]["commits"], f)
        print("Saved at '%s'"%file_path)

    def save_success_commits(self):
        success_commits = []
        for _,v in self.csvDict.items():
            if v['build'] == "SUCCESS":
                success_commits.append(v['commit'])
        with open(self.path+'success_commits.txt', 'w') as f:
            for commit in success_commits:
                f.write("%s\n" % commit)
        print("Saved at '%s'"%(self.path+'success_commits.txt'))
    
if __name__ == "__main__":
    with open('analysis/Mockito/experiment_1/logs/290-8da01ae0-attempt-1.log') as f: 
        log = f.read()
    #log = "[ERROR] /home/bugs/projects/zerocode/src/main/java/org/jsmart/zerocode/core/domain/reports/ZerocodeResult.java:[11,8] class ZeroCodeResult is public, should be declared in a file named ZeroCodeResult.java"
    a = re.search('unable to resolve class (.*)', log)
    print(len(a.groups()))
    print(a.groups())