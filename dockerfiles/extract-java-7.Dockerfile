# Pull base image.
FROM openjdk:7

RUN apt-get update
RUN apt-get -y install build-essential

# Install python 3

RUN apt-get -y install python3

# Install Maven

RUN apt -y install maven

# Install Defects4J

RUN echo Y | perl -MCPAN -e 'install DBI'
RUN git clone https://github.com/rjust/defects4j
RUN ./defects4j/init.sh
ENV PATH="/defects4j/framework/bin:${PATH}"

# Download projects

RUN mkdir bugs/
RUN mkdir bugs/projects/
RUN defects4j checkout -p Lang -v 1b -w bugs/projects/Lang/
RUN defects4j checkout -p Math -v 1b -w bugs/projects/Math/
RUN defects4j checkout -p Closure -v 1b -w bugs/projects/Closure/
RUN defects4j checkout -p Time -v 1b -w bugs/projects/Time/

# Copy source files

COPY py/ bugs/py/

# Copy config files

COPY configFiles/ bugs/configFiles/

CMD ["bash"]

# BUILD docker build -f dockerfiles/extract-java-7.Dockerfile -t buildableprojects/extract_process:java-7 .
# RUN docker run --rm -v $PWD/analysis:/bugs/analysis -w /bugs buildableprojects/extract_process:java-7 python3 py/checkBuildHistory.py configFiles/CheckBuildHistoryFiles/Lang-experiment1-config.json
