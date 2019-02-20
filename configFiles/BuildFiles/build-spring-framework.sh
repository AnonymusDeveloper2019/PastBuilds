rm -rf **/build/
./gradlew build \
    -x test \
    -x javadoc \
    -x javadocJar \
    -x api \
    -x check \
    -x distZip \
    -x depsZip \
    -x docsZip \
    -x schemaZip \
    -x check