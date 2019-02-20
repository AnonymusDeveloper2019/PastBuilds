if [[ ! -f pom.xml ]]; then
	cp -a JodaTime/. .
fi
rm -rf target/
mvn install -Dmaven.test.skip=true