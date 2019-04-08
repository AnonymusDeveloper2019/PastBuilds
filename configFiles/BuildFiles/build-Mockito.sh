rm -rf .gradle/
rm -rf build/
rm -rf buildSrc/.gradle/
rm -rf buildSrc/build/
rm -rf subprojects/extTest/build/
rm -rf subprojects/testng/build/
rm -rf buildSrc/src/test/groovy/
sed -i "s/test {/test { exclude \"\*\*\/\*Test\.class\"/g" buildSrc/build.gradle
./gradlew build -x test -x mockitoJavadoc