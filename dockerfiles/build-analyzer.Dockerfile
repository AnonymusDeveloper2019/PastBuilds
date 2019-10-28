# Pull base image.
FROM openjdk:8

# Install Docker

RUN apt-get update && \
    apt-get -y install apt-transport-https \
    ca-certificates \
    curl \
    gnupg2 \
    software-properties-common && \
    curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg > /tmp/dkey; apt-key add /tmp/dkey && \
    add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") \
    $(lsb_release -cs) \
    stable" && \
    apt-get update && \
    apt-get -y install docker-ce

# Install conda
RUN wget --quiet https://repo.anaconda.com/archive/Anaconda3-5.3.0-Linux-x86_64.sh -O ~/anaconda.sh && \
    /bin/bash ~/anaconda.sh -b -p /opt/conda && \
    rm ~/anaconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

ENV PATH /opt/conda/bin:$PATH

RUN /opt/conda/bin/conda install jupyter -y --quiet 

# Install Defects4J

RUN apt-get -y install build-essential
RUN sudo apt-get install unzip
RUN echo Y | perl -MCPAN -e 'install DBI'
RUN git clone https://github.com/rjust/defects4j
RUN ./defects4j/init.sh
ENV PATH="/defects4j/framework/bin:${PATH}"

WORKDIR /home/bugs/


RUN mkdir projects/

# Download projects (Defects4J)
RUN defects4j checkout -p Mockito -v 1b -w projects/Mockito/
RUN defects4j checkout -p Lang -v 1b -w projects/Lang/
RUN defects4j checkout -p Math -v 1b -w projects/Math/
RUN defects4j checkout -p Closure -v 1b -w projects/Closure/
RUN defects4j checkout -p Time -v 1b -w projects/Time/

# Download projects (GitHub)
RUN git clone https://github.com/rnewson/couchdb-lucene.git projects/couchdb-lucene/
RUN git clone https://github.com/nodebox/nodebox.git projects/nodebox/
RUN git clone https://github.com/apache/mina.git projects/mina/
RUN git clone https://github.com/apache/shiro.git projects/shiro/
RUN git clone https://github.com/dropwizard/metrics.git projects/metrics/
RUN git clone https://github.com/AsyncHttpClient/async-http-client.git projects/async-http-client/
RUN git clone https://github.com/cometd/cometd.git projects/cometd/
RUN git clone https://github.com/mvel/mvel.git projects/mvel/

VOLUME ["/home/bugs/projects/"]

RUN echo "PS1='\[\033[1;36m\]BuildAnalycer \[\033[1;34m\]\w\[\033[0;35m\] \[\033[1;36m\]# \[\033[0m\]'" >> ~root/.bashrc

CMD ["bash"]

# BUILD docker build -f dockerfiles/build-analyzer.Dockerfile -t  build-analyzer:0.2-dev .
# RUN   docker run -it -p 8888:8888 -v $PWD/analysis:/home/bugs/analysis -v $PWD/py:/home/bugs/py -v $PWD/configFiles:/home/bugs/configFiles -v /var/run/docker.sock:/var/run/docker.sock --privileged=true build-analyzer:0.2-dev

