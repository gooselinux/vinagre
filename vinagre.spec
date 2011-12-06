%define with_telepathy 1
%if 0%{?rhel:%{?rhel} <= 6}
%define with_telepathy 0
%endif

Name:		vinagre
Version:	2.28.1
Release:	7%{?dist}
Summary:	VNC client for GNOME

Group:		Applications/System
License:	GPLv2+
URL:		http://projects.gnome.org/vinagre/
Source0:	http://download.gnome.org/sources/vinagre/2.28/%{name}-%{version}.tar.bz2

BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:	gtk-vnc-devel >= 0.3.5
BuildRequires:	glib2-devel >= 2.15.3
BuildRequires:	gtk2-devel >= 2.12.0
BuildRequires:	GConf2-devel >= 2.16.0
BuildRequires:	avahi-ui-devel >= 0.6.18
BuildRequires:	avahi-gobject-devel >= 0.6.18
BuildRequires:	gettext intltool
BuildRequires:	desktop-file-utils
BuildRequires:	gnome-keyring-devel
BuildRequires:	gnome-doc-utils
BuildRequires:	gnome-panel-devel
%if %{with_telepathy}
BuildRequires:	telepathy-glib-devel
%endif

# for /usr/share/dbus-1/services
Requires: dbus

# for /usr/bin/update-desktop-database
Requires: desktop-file-utils

# https://bugzilla.gnome.org/show_bug.cgi?id=606072
Patch0: vinagre-history-crash.patch

# https://bugzilla.gnome.org/show_bug.cgi?id=614026
Patch1: vinagre-dir-prefix.patch

# https://bugzilla.redhat.com/show_bug.cgi?id=588725
Patch2: vinagre-translation.patch

%description
Vinagre is a VNC client for the GNOME desktop.

With Vinagre you can have several connections open simultaneously, bookmark
your servers thanks to the Favorites support, store the passwords in the
GNOME keyring, and browse the network to look for VNC servers.


%package devel
Summary: Development files for vinagre
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}
Requires: pkgconfig

%description devel
Vinagre is a VNC client for the GNOME desktop.

This package allows you to develop plugins that add new functionality
to vinagre.


%prep
%setup -q
%patch0 -p1 -b .history-crash
%patch1 -p1 -b .dir-prefix
%patch2 -p1 -b .translation

%build
%configure --enable-avahi=yes --disable-static \
%if %{with_telepathy}
    --enable-telepathy
%else
    --disable-telepathy
%endif
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
export GCONF_DISABLE_MAKEFILE_SCHEMA_INSTALL=1
make install DESTDIR=$RPM_BUILD_ROOT

# Remove text files installed by vinagre, we install them in a versioned
# directory in the files section
rm -rf $RPM_BUILD_ROOT%{_datadir}/doc/vinagre/

desktop-file-install						\
	--remove-category=Application				\
	--add-category=GTK					\
	--delete-original					\
	--dir=$RPM_BUILD_ROOT%{_datadir}/applications		\
	$RPM_BUILD_ROOT%{_datadir}/applications/vinagre.desktop

# save some space
helpdir=$RPM_BUILD_ROOT%{_datadir}/gnome/help/%{name}
for f in $helpdir/C/figures/*.png; do
	b="$(basename $f)"
	for d in $helpdir/*; do
		if [ -d "$d" -a "$d" != "$helpdir/C" ]; then
			g="$d/figures/$b"
			if [ -f "$g" ]; then
				if cmp -s $f $g; then
					rm "$g"; ln -s "../../C/figures/$b" "$g"
				fi
			fi
		fi
	done
done

# drop unwanted stuff
rm $RPM_BUILD_ROOT%{_libdir}/vinagre-1/plugins/*.la
rm $RPM_BUILD_ROOT%{_libdir}/vinagre-1/plugin-loaders/*.la

%find_lang vinagre --with-gnome

%clean
rm -rf $RPM_BUILD_ROOT

%post
update-desktop-database -q
export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
gconftool-2 --makefile-install-rule %{_sysconfdir}/gconf/schemas/vinagre.schemas > /dev/null || :
touch %{_datadir}/icons/hicolor
if [ -x /usr/bin/gtk-update-icon-cache ]; then
  /usr/bin/gtk-update-icon-cache --quiet %{_datadir}/icons/hicolor
fi


%pre
if [ "$1" -gt 1 -a -f %{_sysconfdir}/gconf/schemas/vinagre.schemas ]; then
  export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
  gconftool-2 --makefile-uninstall-rule %{_sysconfdir}/gconf/schemas/vinagre.schemas > /dev/null || :
fi

%preun
if [ "$1" -eq 0 ]; then
  export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
  gconftool-2 --makefile-uninstall-rule %{_sysconfdir}/gconf/schemas/vinagre.schemas > /dev/null || :
fi

%postun
update-desktop-database -q
update-mime-database %{_datadir}/mime >/dev/null
touch %{_datadir}/icons/hicolor
if [ -x /usr/bin/gtk-update-icon-cache ]; then
  /usr/bin/gtk-update-icon-cache --quiet %{_datadir}/icons/hicolor
fi


%files -f vinagre.lang
%defattr(-,root,root,-)
%{_bindir}/*
%{_sysconfdir}/gconf/schemas/vinagre.schemas
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/*/*/*
%{_datadir}/mime/packages/vinagre-mime.xml
%{_datadir}/%{name}/
%{_libdir}/bonobo/servers/GNOME_VinagreApplet.server
%{_libexecdir}/vinagre-applet
%dir %{_libdir}/vinagre-1
%dir %{_libdir}/vinagre-1/plugin-loaders
%dir %{_libdir}/vinagre-1/plugins
%{_libdir}/vinagre-1/plugin-loaders/*.so
%{_libdir}/vinagre-1/plugins/*.so
%{_libdir}/vinagre-1/plugins/*.vinagre-plugin
%if %{with_telepathy}
%{_datadir}/dbus-1/services/org.gnome.Empathy.StreamTubeHandler.rfb.service
%endif


%doc %{_mandir}/man1/vinagre.1.gz
%doc README NEWS COPYING AUTHORS

%files devel
%defattr(-,root,root,-)
%doc ChangeLog
%{_includedir}/vinagre-1.0
%{_libdir}/pkgconfig/vinagre-1.0.pc


%changelog
* Tue May 18 2010 Marek Kasik <mkasik@redhat.com> 2.28.1-7
- Add requirement of desktop-file-utils
- Resolves: #593059

* Wed May  5 2010 Marek Kasik <mkasik@redhat.com> 2.28.1-6
- Update translations
- Resolves: #588725

* Fri Mar 26 2010 Ray Strode <rstrode@redhat.com> 2.28.1-5
- Support relocatable .gnome2
  Resolves: #577286

* Wed Jan 13 2010 Owen Taylor <otaylor@redhat.com> - 2.28.1-4
- Build without telepathy support
  Resolves: #554517

* Mon Jan  8 2010 Marek Kasik <mkasik@redhat.com> 2.28.1-2
- Don't crash when the history file is empty (#552076)
- Fix mixed use of spaces and tabs in spec file
- Set %%defattr for devel subpackage
- Add ChangeLog to docs of devel subpackage
- Related: #543948

* Mon Oct 19 2009 Matthias Clasen <mclasen@redhat.com> 2.28.1-1
- Update to 2.28.1

* Wed Sep 23 2009 Matthias Clasen <mclasen@redhat.com> 2.28.0.1-1
- Update to 2.28.0.1

* Fri Sep 18 2009 Bastien Nocera <bnocera@redhat.com> 2.27.92-3
- Update mDNS patch

* Fri Sep 18 2009 Bastien Nocera <bnocera@redhat.com> 2.27.92-2
- Fix mDNS bookmarks activation

* Mon Sep  7 2009 Matthias Clasen <mclasen@redhat.com> - 2.27.92-1
- Update to 2.27.92

* Sat Sep  5 2009 Matthias Clasen <mclasen@redhat.com> - 2.27.91-3
- Fix warnings at startup (#521382)

* Thu Sep  3 2009 Matthias Clasen <mclasen@redhat.com> - 2.27.91-2
- Make ids unique

* Tue Aug 25 2009 Matthias Clasen <mclasen@redhat.com> - 2.27.91-1
- Update to 2.27.91

* Tue Aug 11 2009 Matthias Clasen <mclasen@redhat.com> - 2.27.90-1
- 2.27.90

* Tue Aug 04 2009 Bastien Nocera <bnocera@redhat.com> 2.27.5-2
- Fix pkg-config requires

* Tue Jul 28 2009 Matthisa Clasen <mclasen@redhat.com> - 2.27.5-1
- Update to 2.27.5
- Split off a -devel package

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.26.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Apr 13 2009 Matthias Clasen <mclasen@redhat.com> - 2.26.1-1
- Update to 2.26.1
- See http://download.gnome.org/sources/vinagre/2.26/vinagre-2.26.1.news

* Mon Mar 16 2009 Matthias Clasen <mclasen@redhat.com> - 2.26.0-1
- Update to 2.26.0

* Mon Mar  2 2009 Matthias Clasen <mclasen@redhat.com> - 2.25.92-1
- Update to 2.25.92

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.25.91-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Wed Feb 18 2009 Matthias Clasen <mclasen@redhat.com> - 2.25.91-1
- Update to 2.25.91

* Tue Feb  3 2009 Matthias Clasen <mclasen@redhat.com> - 2.25.90-1
- Update to 2.25.90

* Fri Jan 23 2009 Matthias Clasen <mclasen@redhat.com> - 2.25.5-1
- Update to 2.25.5

* Tue Jan  6 2009 Matthias Clasen <mclasen@redhat.com> - 2.25.4-1
- Update to 2.25.4

* Wed Dec 17 2008 Matthias Clasen <mclasen@redhat.com> - 2.25.3-1
- Update to 2.25.3

* Sat Nov 22 2008 Matthias Clasen <mclasen@redhat.com> - 2.24.1-2
- Better URL
- Tweak %%description

* Mon Oct 20 2008 Matthias Clasen <mclasen@redhat.com> - 2.24.1-1
- Update to 2.24.1

* Thu Oct  9 2008 Matthias Clasen <mclasen@redhat.com> - 2.24.0-2
- Save some space

* Mon Sep 22 2008 Matthias Clasen <mclasen@redhat.com> - 2.24.0-1
- Update to 2.24.0

* Mon Sep  8 2008 Matthias Clasen <mclasen@redhat.com> - 2.23.92-1
- Update to 2.23.92

* Tue Sep  2 2008 Matthias Clasen <mclasen@redhat.com> - 2.23.91-1
- Update to 2.23.91

* Fri Aug 22 2008 Matthias Clasen <mclasen@redhat.com> - 2.23.90-1
- Update to 2.23.90

* Wed Jun 25 2008 - Bastien Nocera <bnocera@redhat.com> - 2.23.4-2
- Rebuild

* Tue Jun 17 2008 - Bastien Nocera <bnocera@redhat.com> - 2.23.4-1
- Update to 2.23.4
- Fix URL (#451746)

* Wed Jun  4 2008 Matthias Clasen <mclasen@redhat.com> - 2.23.3.1-1
- Update to 2.23.3.1

* Fri Apr 25 2008 Matthias Clasen <mclasen@redhat.com> - 2.23.1-1
- Update to 2.23.1

* Mon Apr  7 2008 Matthias Clasen <mclasen@redhat.com> - 0.5.1-1
- Update to 0.5.1

* Mon Mar 10 2008 Matthias Clasen <mclasen@redhat.com> - 0.5.0-1
- Update to 0.5.0

* Mon Feb 25 2008 Matthias Clasen <mclasen@redhat.com> - 0.4.92-1
- Update to 0.4.92

* Mon Feb 18 2008 Matthias Clasen <mclasen@redhat.com> - 0.4.91-2
- Spec file fixes

* Tue Feb 12 2008 Matthias Clasen <mclasen@redhat.com> - 0.4.91-1
- Update to 0.4.91

* Tue Jan 29 2008 Matthias Clasen <mclasen@redhat.com> - 0.4.90-1
- Update to 0.4.90

* Thu Dec 13 2007 - Bastien Nocera <bnocera@redhat.com> - 0.4-1
- Update to 0.4 and drop obsolete patches

* Fri Nov 23 2007 - Bastien Nocera <bnocera@redhat.com> - 0.3-3
- Fix crasher when passing broken options on the command-line (#394671)

* Thu Oct 25 2007 - Bastien Nocera <bnocera@redhat.com> - 0.3-2
- Fix crasher when setting a favourite with no password (#352371)

* Mon Sep 24 2007 - Bastien Nocera <bnocera@redhat.com> - 0.3-1
- Update to 0.3

* Wed Aug 22 2007 - Bastien Nocera <bnocera@redhat.com> - 0.2-1
- First version
- Fix plenty of comments from Ray Strode as per review
- Have work-around for BZ #253734

