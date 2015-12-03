# TODO:
# - Test it.
# NOTE:
# - consider split sqlite and apache to separate packages? Or only suggest them?

Summary:	A Django webapp for enterprise scalable realtime graphing
Name:		graphite-web
Version:	0.9.15
Release:	1
License:	Apache v2.0
Group:		Applications/WWW
Source0:	https://github.com/graphite-project/graphite-web/archive/0.9.15/%{name}-%{version}.tar.gz
# Source0-md5:	f81c50b8b57672fc15a1cfe7bbae1c52
Source1:	apache.conf
Source2:	%{name}.logrotate
Source3:	local_settings.py
Patch0:		%{name}-kill-thirdparty-modules.patch
URL:		https://launchpad.net/graphite/
BuildRequires:	rpm-pythonprov
BuildRequires:	python-devel
BuildRequires:	rpmbuild(macros) >= 1.710
Requires:	apache-mod_alias
Requires:	apache-mod_authz_host
Requires:	apache-mod_log_config
Requires:	apache-mod_wsgi
Requires:	fonts-TTF-DejaVu
Requires:	python-django
Requires:	python-django_tagging >= 0.3
Requires:	python-modules-sqlite
Requires:	python-pycairo
Requires:	python-pyparsing
Requires:	python-pytz
Requires:	python-simplejson
Requires:	python-whisper >= %{version}
Requires:	webapps
Conflicts:	logrotate < 3.8.0
BuildArch:	noarch
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_webapps	/etc/webapps
%define		_webapp		%{name}
%define		_sysconfdir	%{_webapps}/%{_webapp}
%define		_appdir		%{_datadir}/%{_webapp}

%description
Graphite consists of a storage backend and a web-based visualization
frontend. Client applications send streams of numeric time-series data
to the Graphite backend (called carbon), where it gets stored in
fixed-size database files similar in design to RRD. The web frontend
provides user interfaces for visualizing this data in graphs as well
as a simple URL-based API for direct graph generation.

Graphite's design is focused on providing simple interfaces (both to
users and applications), real-time visualization, high-availability,
and enterprise scalability.

%prep
%setup -q
# Kill strict use of thidparty subdir copies of python modules
%patch0 -p1

%build
%py_build %{?with_tests:test}

%install
rm -rf $RPM_BUILD_ROOT
# http://graphite.readthedocs.org/en/latest/install-source.html#installing-in-the-default-location
%py_install   \
--prefix %{_prefix} \
  --install-lib %{py_sitescriptdir}   \
  --install-data %{_datadir}/graphite

%py_postclean -x manage.py

# Create directories
install -d $RPM_BUILD_ROOT{%{_sysconfdir},/etc/logrotate.d,%{_localstatedir}/{lib,log}/%{name}}

# Install some default configurations and wsgi
install -Dp conf/dashboard.conf.example $RPM_BUILD_ROOT%{_sysconfdir}/dashboard.conf
# mv $RPM_BUILD_ROOT{%{py_sitescriptdir}/graphite/local_settings.py.example,%{_sysconfdir}/local_settings.py}
cp -p %{SOURCE3} $RPM_BUILD_ROOT%{_sysconfdir}/local_settings.py

touch $RPM_BUILD_ROOT%{py_sitescriptdir}/graphite/local_settings.py{c,o}
cp -p conf/graphite.wsgi.example $RPM_BUILD_ROOT%{_datadir}/graphite/%{name}.wsgi
cp -p %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/httpd.conf
cp -p %{SOURCE2} $RPM_BUILD_ROOT/etc/logrotate.d/%{name}

# Configure django /media/ location
sed -i 's|##PYTHON_SITELIB##|%{py_sitescriptdir}|' $RPM_BUILD_ROOT%{_sysconfdir}/httpd.conf

# Create local_settings symlink
ln -s %{_sysconfdir}/local_settings.py $RPM_BUILD_ROOT%{py_sitescriptdir}/graphite

# Don't ship bins that are not needed for prodcution
%{__rm} $RPM_BUILD_ROOT%{_bindir}/{build-index.sh,run-graphite-devel-server.py}

# Add graphite-manage to PATH for easy access
install -d $RPM_BUILD_ROOT%{_sbindir}
ln -s %{py_sitescriptdir}/graphite/manage.py $RPM_BUILD_ROOT%{_sbindir}/graphite-manage

# Don't ship thirdparty
rm -r $RPM_BUILD_ROOT%{py_sitescriptdir}/graphite/thirdparty

# Install django/httpd accessible DB
touch $RPM_BUILD_ROOT/var/lib/graphite-web/graphite.db

%clean
rm -rf $RPM_BUILD_ROOT

%triggerin -- apache < 2.2.0, apache-base
%webapp_register httpd %{_webapp}

%triggerun -- apache < 2.2.0, apache-base
%webapp_unregister httpd %{_webapp}

%files
%defattr(644,root,root,755)
%doc conf/* examples/*
%config(noreplace) %verify(not md5 mtime size) /etc/logrotate.d/%{name}
%dir %attr(750,root,http) %{_sysconfdir}
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/httpd.conf
%attr(640,root,http) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/dashboard.conf
%attr(640,root,http) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/local_settings.py
%attr(755,root,root) %{_sbindir}/graphite-manage

%dir %{py_sitescriptdir}/graphite
%{py_sitescriptdir}/graphite/[^l]*.py[co]
%{py_sitescriptdir}/graphite/logger.py[co]
%{py_sitescriptdir}/graphite/local_settings.py
%ghost %{py_sitescriptdir}/graphite/local_settings.py[co]
%attr(755,root,root) %{py_sitescriptdir}/graphite/manage.py
%{py_sitescriptdir}/graphite/account
%{py_sitescriptdir}/graphite/browser
%{py_sitescriptdir}/graphite/cli
%{py_sitescriptdir}/graphite/composer
%{py_sitescriptdir}/graphite/dashboard
%{py_sitescriptdir}/graphite/events
%{py_sitescriptdir}/graphite/metrics
%{py_sitescriptdir}/graphite/render
%{py_sitescriptdir}/graphite/templates
%{py_sitescriptdir}/graphite/version
%{py_sitescriptdir}/graphite/url_shortener
%{py_sitescriptdir}/graphite/whitelist
%{py_sitescriptdir}/graphite_web-%{version}-py*.egg-info

%dir %{_datadir}/graphite
%attr(755,root,root) %{_datadir}/graphite/graphite-web.wsgi
%{_datadir}/graphite/webapp

%attr(775,root,http) %dir %{_localstatedir}/log/%{name}
%attr(775,root,http) %dir %{_sharedstatedir}/%{name}
%attr(640,http,http) %config(noreplace) %verify(not md5 mtime size) /var/lib/graphite-web/graphite.db
