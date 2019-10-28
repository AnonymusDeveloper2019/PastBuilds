# Reproducing open-projects software builds experiment

Research on reproducing software builds in past commits

##### **IMPORTANT**: The experiment for each project can take several hours or days, depending of your machine. All results to realize the analysis are provided in this repo.

## Introduction

We will build the projects in all the versions that repository provides to check the status of the project and analyze the cases in which it is not possible to carry out the construction. The proyects selected for this experiment are the following:

| Identifier       	| Project             	| # of commits 	|
|------------------	|---------------------	|--------------	|
| Closure          	| Closure compiler    	| 2858         	|
| Lang             	| Apache commons-lang 	| 3570         	|
| Math             	| Apache commons-math 	| 4878         	|
| Mockito          	| Mockito             	| 2639         	|
| Time             	| Joda-Time           	| 1717         	|


## Check build process

### SetUp

#### :whale: Using Docker

*Pre-requisites*

- Git 2.17.1
- Docker 18.06.1-ce

Clone the project repo:

```
  git clone https://gitlab.com/urjc-softdev/bugs.git
  cd bugs/
```

Build local images:

```
docker build -f dockerfiles/build-analyzer.Dockerfile -t  build-analyzer:0.2-dev .
docker build -f dockerfiles/java-8.Dockerfile -t java-maven:8 .
```

Run container:

```
docker run -it -p 8888:8888 \
    -v $PWD/analysis:/home/bugs/analysis \
    -v $PWD/py:/home/bugs/py \
    -v $PWD/configFiles:/home/bugs/configFiles \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --privileged=true build-analyzer:0.2-dev
```

#### :hammer: Manually 

*Pre-requisites*

- Git 2.17.1
- Conda 4.5.3
- [Defects4J 1.2.0](https://github.com/rjust/defects4j/tree/v1.2.0) (install as indicate in README.md)
- Java 8

Clone the project repo:

```
  git clone https://gitlab.com/urjc-softdev/bugs.git
  cd bugs/
```

Download repos from git and Defects4J:

```
  ./projects/downloadAllProjects.sh
```

## Start the experiment

To check build history from a project (using bash terminal on your machine or inside docker container):

```
python py/checkBuildHistory.py configFiles/experiment_<n>/<project>-config.json
```

For example (assuming analysis/Lang/experiment_1/ doesn't exist):

```
python py/checkBuildHistory.py configFiles/experiment_1/Lang-config.json
```

This will create new folder `analysis/Lang/experiment_1/` with the following files/subfolders:
- `build_files` include build files used in each commit
- `general_logs/` include the logs from the script `checkBuildHistory.py`
- `logs/` include the logs from each build/commit
- `report_experiment_1.csv` a table in csv format with the results of experiment for this project

The `report_experiment_1.csv` file follows this format:

```
id,commit,build,exec_time,comment,fix
0,687b2e62,SUCCESS,6,LANG-747 NumberUtils does not handle Long Hex numbers
```

- `id` is the identifier, and also shows how much commits are checked from latest commit.
- `commit` hash id from the commit to identify it in Git
- `build` status of the build. Could be 'SUCCESS', 'FAIL' or 'NO' (not already checked)
- `exec_time` time in seconds that the builds take 
- `comment` git comment of the commit

## Analyce results

Once all commits was checked, we could analyce the results using a JupyterNotebook:

### SetUp

#### :whale: Using Docker 

Inside container, run:
```
 nohup jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --NotebookApp.token=Saturn > error.log &
```

#### :hammer: Manually 

*Pre-requisites*

- All requisites from check build process
- Conda 4.5.3

Run at console (in project directory):

```
jupyter-notebook
```

## Run

Open yout browser at `localhost:8888`. Use token 'Saturn' if use Docker.

# Use of available notebooks for analysis

- `ProjectAnalysis.ipynb` -> Allow us to perform a deep analysis on each project. Changes values in cell 2 to select differents projects/experiments.
- `LogUnifier.ipynb`      -> Allow us to unify all errors from all projects (need to previously run last notebook to generate errors) 