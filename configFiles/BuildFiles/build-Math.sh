sed -i "s/<fileset dir=\"target\/test-classes\"//g" pom.xml
sed -i "s/includes=\"org\/apache\/commons\/math3\/PerfTestUtils\*\" \/>//g" pom.xml
mvn clean install -Dmaven.test.skip=true

