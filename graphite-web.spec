Summary:	A Django webapp for enterprise scalable realtime graphing
Name:		graphite-web
Version:	0.9.10
Release:	0.2
License:	Apache v2.0
Group:		Applications/WWW
Source0:	https://github.com/downloads/graphite-project/graphite-web/%{name}-%{version}.tar.gz
Source1:	apache.conf
Source2:	%{name}.logrotate
Patch0:		%{name}-0.9.10-fhs-thirdparty.patch
URL:		https://launchpad.net/graphite/
BuildRequires:	python-devel
BuildRequires:	rpm-pythonprov
BuildRequires:	rpmbuild(macros) >= 1.658
Requires:	apache-mod_wsgi
Requires:	fonts-TTF-DejaVu
Requires:	python-django
Requires:	python-django_tagging
Requires:	python-pycairo
Requires:	python-pyparsing
Requires:	python-pytz
Requires:	python-simplejson
Requires:	python-whisper
Requires:	webapps
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
# Patch for Filesystem Hierarchy Standard
# Remove thridparty libs
# https://github.com/hggh/graphite-web-upstream/commit/47361a2707f904a8b817ca96deeddabcdbaaa534.patch
%patch0 -p1

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install \
	--skip-build \
	--optimize=2 \
	--root=$RPM_BUILD_ROOT

%py_postclean -x manage.py

# Create directories
install -d $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}
install -d $RPM_BUILD_ROOT%{_localstatedir}/log/%{name}
install -d $RPM_BUILD_ROOT%{_sysconfdir}

# Install some default configurations and wsgi
install -Dp conf/dashboard.conf.example $RPM_BUILD_ROOT%{_sysconfdir}/dashboard.conf
mv $RPM_BUILD_ROOT{%{py_sitescriptdir}/graphite/local_settings.py.example,%{_sysconfdir}/local_settings.py}
touch $RPM_BUILD_ROOT%{_sysconfdir}/local_settings.py{c,o}
install -Dp conf/graphite.wsgi.example $RPM_BUILD_ROOT%{_datadir}/graphite/%{name}.wsgi
install -Dp %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/httpd.conf
install -Dp %{SOURCE2} $RPM_BUILD_ROOT/etc/logrotate.d/%{name}

# Configure django /media/ location
sed -i 's|##PYTHON_SITELIB##|%{py_sitescriptdir}|' $RPM_BUILD_ROOT%{_sysconfdir}/httpd.conf

# Create local_settings symlink
ln -s %{_sysconfdir}/local_settings.py $RPM_BUILD_ROOT%{py_sitescriptdir}/graphite

# Don't ship bins that are not needed for prodcution
%{__rm} $RPM_BUILD_ROOT%{_bindir}/{build-index.sh,run-graphite-devel-server.py}

# Fix permissions
%{__chmod} 0755 $RPM_BUILD_ROOT%{py_sitescriptdir}/graphite/manage.py

# Don't ship thirdparty
rm -r $RPM_BUILD_ROOT%{py_sitescriptdir}/graphite/thirdparty

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
%ghost %{_sysconfdir}/local_settings.pyc
%ghost %{_sysconfdir}/local_settings.pyo

%dir %{py_sitescriptdir}/graphite
%{py_sitescriptdir}/graphite/*.py[co]
%{py_sitescriptdir}/graphite/local_settings.py
%attr(755,root,root) %{py_sitescriptdir}/graphite/manage.py
%{py_sitescriptdir}/graphite/account
%{py_sitescriptdir}/graphite/browser
%{py_sitescriptdir}/graphite/cli
%{py_sitescriptdir}/graphite/composer
%{py_sitescriptdir}/graphite/dashboard
%{py_sitescriptdir}/graphite/events
%{py_sitescriptdir}/graphite/graphlot
%{py_sitescriptdir}/graphite/metrics
%{py_sitescriptdir}/graphite/render
%{py_sitescriptdir}/graphite/templates
%{py_sitescriptdir}/graphite/version
%{py_sitescriptdir}/graphite/whitelist
%{py_sitescriptdir}/graphite_web-%{version}-py*.egg-info

%dir %{_datadir}/graphite
%attr(755,root,root) %{_datadir}/graphite/graphite-web.wsgi
%{_datadir}/graphite/webapp

%attr(775,root,http) %dir %{_localstatedir}/log/%{name}
%attr(775,root,http) %dir %{_sharedstatedir}/%{name}
