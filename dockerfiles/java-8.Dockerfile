FROM openjdk:8
RUN apt-get update
RUN apt -y install maven
CMD ["bash"]

# BUILD docker build -f dockerfiles/java-8.Dockerfile -t java-maven:8 .
# RUN docker run --rm -it java-maven:8 bash
