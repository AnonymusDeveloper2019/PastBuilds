
# coding: utf-8

import csv
import pandas as pd
import matplotlib.pyplot as plt
import re
import hashlib
import numpy as np
from matplotlib import rc

class ProjectAnalysis():

    def __init__(self, project, n):
        self.project= project
        self.path= "../%s/experiment_%d/"%(self.project, n)
        self.report="%s/report_experiment_%d.csv"%(self.path, n)
        self.data= pd.read_csv(self.report)
        with open(self.report) as csvfile:
            reader = csv.DictReader(csvfile)
            self.csvDict = dict()
            for row in reader:
                self.csvDict[row['commit']] = row

    def df(self):
        return self.data

    def plot_and_save_histogram(self, jump):
        total_commits = len(self.df())+jump
        limit = len(self.df())

        data = self.df()
        fails_list=[]
        success_list=[]
        for index, row in data.iterrows():
            if row['build'] == "SUCCESS":
                success_list.append(len(data)-row['id']-1)
            else:
                fails_list.append(len(data)-row['id']-1)

        bins = np.arange(0,total_commits,jump)

        fig, ax = plt.subplots(figsize=(16, 4))
        _, bins, patches = plt.hist([np.clip(success_list, bins[0], bins[-1]),
                                    np.clip(fails_list, bins[0], bins[-1])],
                                    #normed=1,  # normed is deprecated; replace with density
                                    stacked=True,
                                    #density=True,
                                    bins=bins, color=['#4b8869', '#a82e2e'], label=['SUCCESS', 'FAIL'])
        
        if jump > 100:
            xlabels = bins[1:].astype(str)
            xlabels[-1] += '+'
            plt.xticks(rotation=45)
            N_labels = len(xlabels)
            plt.xticks(jump * np.arange(N_labels) + jump/2)
            ax.set_xticklabels(xlabels)
        
        #ax.set_xlabel("Commits from beginning of project to last commit")
        

        plt.yticks([])
        #plt.title(title, fontsize=20)
        plt.setp(patches, linewidth=0)
        plt.legend(loc='upper left', prop={'size': 24})

        fig.tight_layout()
        plt.xlim([0, limit])
        plt.ylim([0, jump])
        plt.tick_params(axis='both', labelsize=14)
        
        plt.savefig(self.path+('%sHist.png'%self.project))
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
        
        for fail in fails:
            with open(self.path+"logs/%s-%s.log"%(fail['id'], fail['commit'])) as f: 
                r_data = f.read()
                fail['log'] = r_data
        return (fails, groups_of_fails)

    def cleanLog(self, text):
        return text.replace('\n', ' ').replace('\t', ' ')


    def addError(self, errors, error_text, commit):
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
                'count': 1
            }

    def group_errors_by_log(self, fails, common_errors):

        errors=dict()

        for fail in fails:
            
            detected = False
            
            for log_template in common_errors:
                
                for e in re.finditer(log_template, fail['log']):
                    self.addError(errors, e.group(0), fail['commit'])
                    detected = True
                    break
                if detected: break
            if detected: continue
                
            if not detected:
                self.addError(errors, fail['log'], fail['commit'])

        return errors

    def view_log_by_hash(self, errors, hash_id, n=0):
        total = len(errors[hash_id]["commits"])
        commit = self.csvDict[errors[hash_id]["commits"][n]]['commit']
        log = self.csvDict[errors[hash_id]["commits"][n]]['log']
        # self.csvDict[errors[hash_id]["commits"][n]]['log']
        print("Total commits: %d | Current commit: %s | Log: \n\n%s "%(total, commit, log))
        
        

    def save_success_commits(self):
        success_commits = []
        for k,v in self.csvDict.items():
            if v['build'] == "SUCCESS":
                success_commits.append(v['commit'])
        with open(self.path+'success_commits.txt', 'w') as f:
            for commit in success_commits:
                f.write("%s\n" % commit)
        print("Saved at '%s'"%(self.path+'success_commits.txt'))
    

