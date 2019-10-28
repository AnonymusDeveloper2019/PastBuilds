docker run -it -p 8888:8888 \
    -v $PWD/analysis:/home/bugs/analysis \
    -v $PWD/py:/home/bugs/py \
    -v $PWD/projects:/home/bugs/projects \
    -v $PWD/configFiles:/home/bugs/configFiles \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --privileged=true build-analyzer:0.2-dev

# JUPYTER nohup jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --NotebookApp.token=Saturn > output.log &