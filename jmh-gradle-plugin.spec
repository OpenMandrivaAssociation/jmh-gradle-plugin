Name:		jmh-gradle-plugin
Version:	0.7.3
Release:	1
Summary:	Gradle plugin that runs JMH benchmarks
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/melix/jmh-gradle-plugin
# Tag RELEASE_0_7_3. The Gradle wrapper jar is not in this archive.
# Java sources are compiled with javac. The Groovy plugin class is
# compiled with Groovy's FileSystemCompiler. The Gradle tool is not invoked.
Source0:	jmh-gradle-plugin-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-21-openjdk-devel
BuildRequires:	gradle
BuildRequires:	apache-groovy
BuildRequires:	antlr4
BuildRequires:	objectweb-asm
BuildRequires:	picocli
BuildRequires:	jansi
BuildRequires:	mvn(javax.inject:javax.inject)
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem

%description
Gradle plugin id me.champeau.jmh. The catalog pin is
me.champeau.jmh:jmh-gradle-plugin 0.7.3. The Java sources are
compiled with javac. The plugin class is compiled with the system
Groovy 4.0.33 compiler. The Gradle tool is not invoked. Applying
the plugin on a ProjectBuilder project sets the JMH version
convention to 1.36 and the result format to text.

%prep
%autosetup -n jmh-gradle-plugin-%{version} -p1
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
find . -type d -name '*.jar' -print >> binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
find src/main/java -name '*.java' | sort > java.list
find src/main/groovy -name '*.groovy' | sort > groovy.list
test "$(wc -l < java.list)" -eq 7
test "$(wc -l < groovy.list)" -eq 1

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
CP=$(find %{_datadir}/gradle -name '*.jar' | sort | paste -sd: -)
for extra in \
	%{_javadir}/atinject.jar \
	%{_javadir}/apache-groovy.jar
do
	test -s "$extra"
	CP="$CP:$extra"
done
mkdir -p classes
javac -encoding UTF-8 --release 11 -Xlint:-options -proc:none -cp "$CP" -d classes @java.list
GROOVY_CP=%{_javadir}/apache-groovy.jar
for extra in \
	%{_javadir}/antlr4-runtime.jar \
	%{_javadir}/asm.jar \
	%{_javadir}/asm-commons.jar \
	%{_javadir}/asm-tree.jar \
	%{_javadir}/asm-util.jar \
	%{_javadir}/picocli.jar \
	/usr/lib/java/jansi/jansi.jar
do
	test -s "$extra"
	GROOVY_CP="$GROOVY_CP:$extra"
done
GROOVY_CP="$GROOVY_CP:$CP:classes"
java -Dgroovy.target.bytecode=11 -cp "$GROOVY_CP" org.codehaus.groovy.tools.FileSystemCompiler \
	--classpath "$GROOVY_CP" -d classes @groovy.list
test "$(find classes -name '*.class' | wc -l)" -eq 46
for cls in \
	me.champeau.jmh.JmhParameters \
	me.champeau.jmh.DefaultsConfigurer \
	me.champeau.jmh.JMHPlugin
do
	javap -v -classpath classes "$cls" | grep -F -q 'major version: 55'
done
mkdir -p classes/META-INF/gradle-plugins
printf '%s\n' 'implementation-class=me.champeau.jmh.JMHPlugin' \
	> classes/META-INF/gradle-plugins/me.champeau.jmh.properties
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: me.champeau.jmh' > manifest.mf
jar cfm jmh-gradle-plugin.jar manifest.mf -C classes .
jar i jmh-gradle-plugin.jar
jar tf jmh-gradle-plugin.jar | grep -F -q 'me/champeau/jmh/JMHPlugin.class'
jar tf jmh-gradle-plugin.jar | grep -F -q 'META-INF/gradle-plugins/me.champeau.jmh.properties'
desc=$(jar --describe-module --file jmh-gradle-plugin.jar)
printf '%s\n' "$desc" | grep -F -q 'me.champeau.jmh'
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	printf '%s\n' "$desc"
	exit 1
fi

cat > jmh-gradle-plugin.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>me.champeau.jmh</groupId>
  <artifactId>jmh-gradle-plugin</artifactId>
  <version>%{version}</version>
  <name>jmh-gradle-plugin</name>
  <description>Gradle plugin that runs JMH benchmarks.</description>
  <url>https://github.com/melix/jmh-gradle-plugin</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.apache.groovy</groupId>
      <artifactId>groovy</artifactId>
      <version>4.0.33</version>
    </dependency>
    <dependency>
      <groupId>javax.inject</groupId>
      <artifactId>javax.inject</artifactId>
      <version>1.0.5</version>
    </dependency>
  </dependencies>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact jmh-gradle-plugin.pom:jmh-gradle-plugin.jar \
	--file-name jmh-gradle-plugin \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/me.champeau.jmh/jmh-gradle-plugin.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "jmh-gradle-plugin"' "$idx"
test -s %{buildroot}%{_javadir}/jmh-gradle-plugin.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
JAR=%{buildroot}%{_javadir}/jmh-gradle-plugin.jar
test -s "$JAR"
CP=$(find %{_datadir}/gradle -name '*.jar' | sort | paste -sd: -)
for extra in \
	%{_javadir}/atinject.jar \
	%{_javadir}/apache-groovy.jar
do
	test -s "$extra"
	CP="$CP:$extra"
done
mkdir -p check
cat > check/Smoke.java << 'EOF'
import me.champeau.jmh.JMHPlugin;
import me.champeau.jmh.JmhParameters;
import org.gradle.api.Project;
import org.gradle.testfixtures.ProjectBuilder;

public class Smoke {
	public static void main(String[] args) {
		int code = 1;
		try {
			Project project = ProjectBuilder.builder().build();
			project.getPluginManager().apply(JMHPlugin.class);
			JmhParameters params = project.getExtensions().getByType(JmhParameters.class);
			String version = params.getJmhVersion().get();
			String format = params.getResultFormat().get();
			if (!"1.36".equals(version) || !"text".equals(format)) {
				throw new AssertionError(version + " " + format);
			}
			System.out.println(args[0] + " " + version + " " + format);
			code = 0;
		} catch (Throwable t) {
			t.printStackTrace();
		}
		Runtime.getRuntime().halt(code);
	}
}
EOF
javac -encoding UTF-8 --release 11 -Xlint:-options -proc:none -cp "$JAR:$CP" -d check check/Smoke.java
"$JAVA_HOME/bin/java" \
	--add-opens=java.base/java.lang=ALL-UNNAMED \
	--add-opens=java.base/java.lang.invoke=ALL-UNNAMED \
	--add-opens=java.base/java.util=ALL-UNNAMED \
	--add-opens=java.prefs/java.util.prefs=ALL-UNNAMED \
	--add-opens=java.base/java.nio.charset=ALL-UNNAMED \
	--add-opens=java.base/java.net=ALL-UNNAMED \
	--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED \
	--add-opens=java.xml/javax.xml.namespace=ALL-UNNAMED \
	--add-exports=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED \
	--add-exports=jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED \
	-cp "check:$JAR:$CP" Smoke jmh_plugin_ok > check/out.txt
cat check/out.txt
grep -qx 'jmh_plugin_ok 1.36 text' check/out.txt

%files -f .mfiles
%doc README.adoc
%license LICENSE
