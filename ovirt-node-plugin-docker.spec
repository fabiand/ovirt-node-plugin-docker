
Name:           ovirt-node-plugin-docker
Version:        0.1.0
Release:        0.1
URL:            https://github.com/fabiand/ovirt-node-plugin-docker
Source0:        https://github.com/fabiand/%{name}/archive/master/%{name}-%{version}-master.tar.gz
License:        GPLv2+
Group:          Applications/System
Summary:        Docker plugin for oVirt Node
Requires:       docker-io

Requires:       fedora-release > 19

Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
BuildRequires: systemd

BuildArch:      noarch
BuildRequires:  python2-devel


%description
This package provides some TUI packages for monitoring docker.


%prep
%setup


%build
echo Nothing


%install
DSTDIR=%{buildroot}/%{python_sitelib}/ovirt/node/setup/docker
cp src/*.py $DSTDIR


%post
%systemd_post apache-httpd.service


%preun
%systemd_preun apache-httpd.service


%postun
%systemd_postun_with_restart apache-httpd.service 


%files
%{python_sitelib}/ovirt/node/setup/hostedengine/__init__.py*
%{python_sitelib}/ovirt/node/setup/hostedengine/hosted_engine_page.py*



%files
%{python_sitelib}/ovirt/node/setup/hostedengine
#%{_sysconfdir}/ovirt-plugins.d

%files recipe
%{recipe_root}

%changelog
* Fri Jul 25 2014 Joey Boggs <jboggs@redhat.com> 0.0.1
- initial commit
