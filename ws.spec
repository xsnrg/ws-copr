# WS (formerly WSJT-X Improved) Qt6 for Fedora Copr.
# Source is the standard GUI Qt6 tarball:
#   WS_vVERSION/Source code/ws-VERSION_YYMMDD.tgz   (3.2.1+, Qt6-only tree)
#   WS_vVERSION/Source code/Qt6/ws-VERSION_YYMMDD_qt6.tgz  (3.2.0)
# Version / snapshot below are the last-known drop and a fallback if
# SourceForge cannot be queried. .copr/Makefile rewrites them before the SRPM.

%define snapshot 260926
%define oname    ws

# Fortran trampolines still need an executable stack on gfortran
%undefine _hardened_linker_errors

Name:           ws
Version:        3.2.1
Release:        1.%{snapshot}%{?dist}
Summary:        WS (formerly WSJT-X Improved) by DG2YCB (weak-signal amateur radio)

License:        GPL-3.0-or-later
URL:            https://sourceforge.net/projects/wsjt-x-improved
Source0:        https://downloads.sourceforge.net/project/wsjt-x-improved/WS_v%{version}/Source%%20code/%{oname}-%{version}_%{snapshot}.tgz

ExcludeArch:    i686

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  gcc-gfortran
BuildRequires:  make
BuildRequires:  desktop-file-utils
BuildRequires:  dos2unix
BuildRequires:  pkgconfig
# Copr builds should resolve this from xsnrg/hamlib. Bundled hamlib is deleted.
BuildRequires:  hamlib-devel >= 4.7.2
BuildRequires:  fftw-devel
BuildRequires:  libusbx-devel
BuildRequires:  systemd-devel
BuildRequires:  boost-devel
BuildRequires:  portaudio-devel
BuildRequires:  qt6-qtbase-devel
BuildRequires:  qt6-qttools-devel
BuildRequires:  qt6-qtserialport-devel
BuildRequires:  qt6-qtmultimedia-devel
BuildRequires:  qt6-qtwebsockets-devel
BuildRequires:  qt6-qtsvg-devel

Requires:       hamlib >= 4.7.2
Requires:       hicolor-icon-theme

%description
WS, formerly WSJT-X Improved, is an enhanced edition of WSJT-X published by
Uwe Risse, DG2YCB. It keeps the familiar WSJT-X workflow and adds
features such as CQ/73 highlighting, mode buttons, band hopping,
DX-oriented FT8/FT4 decoding, False Decodes Reduction, Wait and
Reply/Call, audible alerts, and Cloudlog support.

This package is built from the Qt6 source tarball. The program is
/usr/bin/ws, so it does not replace Fedora's wsjtx.

Modes include FST4, FST4W, FT4, FT8, FT2, JT4, JT9, JT65, Q65,
MSK144, WSPR, and Echo.

%prep
%autosetup -n %{oname}-%{version} -p1

# Always use system hamlib
rm -f src/hamlib*.tgz* src/hamlib*.tar.gz*

# Real sources live in the nested tarball
tar -xzf src/%{oname}.tgz
rm -f src/%{oname}.tgz*

find . -type f -exec chmod a-x {} +
cd %{oname}
dos2unix -k -q *.ui *.txt AUTHORS BUGS NEWS README THANKS *.desktop 2>/dev/null || true

# Re-enable message_aggregator install (commented in upstream CMakeLists)
sed -i -e 's@#install (TARGETS udp_daemon message_aggregator wsjtx_app_version@install (TARGETS udp_daemon message_aggregator wsjtx_app_version@g' CMakeLists.txt
sed -i -e '/^install (TARGETS udp_daemon wsjtx_app_version$/d' CMakeLists.txt

# Sounds can live in datadir. ALLCALL7.TXT must stay next to jt9:
# lib/ft8var/cwfilter.f90 opens it as a relative name, and the GUI
# launches jt9 with -e /usr/bin. status='unknown' would otherwise
# try to create /usr/bin/ALLCALL7.TXT (permission denied).
sed -i -z -e 's@install (DIRECTORY\n  ${PROJECT_SOURCE_DIR}/sounds\n  DESTINATION ${CMAKE_INSTALL_BINDIR}@install (DIRECTORY\n  ${PROJECT_SOURCE_DIR}/sounds\n  DESTINATION ${CMAKE_INSTALL_DATADIR}/${WS_DATA_DIR_NAME}@g' CMakeLists.txt
sed -i -e "s@open(24,file='ALLCALL7.TXT',status='unknown')@open(24,file=trim(exe_dir)//'/ALLCALL7.TXT',status='old',action='read',err=20)@" \
    lib/ft8var/cwfilter.f90

# Upstream CMake appends -Wl,-z,noexecstack and -Xassembler --noexecstack
# AFTER our LDFLAGS, so GNU_STACK stays RW and jt9 SIGSEGVs on decode.
sed -i -e 's/-Wl,-z,noexecstack/-Wl,-z,execstack/g' \
       -e 's/-Xassembler --noexecstack/-Xassembler --execstack/g' \
    CMakeLists.txt

%build
# Fortran in this tree is not LTO-safe
%define _lto_cflags %{nil}

export CFLAGS="%{optflags} -fcommon -Wno-error=deprecated-declarations -Wno-error=unused-result -Wno-error=format-security -Wno-error=maybe-uninitialized"
export CXXFLAGS="%{optflags} -Wno-error=deprecated-declarations -Wno-error=unused-result -Wno-error=format-security -Wno-error=maybe-uninitialized"
# Nested Fortran functions use trampolines. Fedora's hardened
# -z noexecstack makes jt9 SIGSEGV/SIGBUS as soon as decode starts.
# Heap trampolines avoid needing an executable stack; -z execstack
# is the fallback if an object still requests one.
export FFLAGS="%{optflags} -fPIC -fallow-argument-mismatch -std=legacy -ftrampoline-impl=heap"
export FCFLAGS="%{optflags} -fPIC -fallow-argument-mismatch -std=legacy -ftrampoline-impl=heap"
export LDFLAGS="%{?build_ldflags} -Wl,-z,execstack"
export FC=/usr/bin/gfortran
export PKG_CONFIG_ALLOW_SYSTEM_LIBS=1

cd %{oname}
%cmake \
    -Dhamlib_STATIC=FALSE \
    -DWSJT_GENERATE_DOCS=OFF \
    -DWSJT_SKIP_MANPAGES=ON \
    -DBoost_NO_SYSTEM_PATHS=FALSE \
    -DBOOST_INCLUDEDIR=%{_includedir}/boost \
    -DBOOST_LIBRARYDIR=%{_libdir} \
    -DCMAKE_EXE_LINKER_FLAGS="%{?build_ldflags} -Wl,-z,execstack"

%cmake_build

%install
cd %{oname}
%cmake_install

# Drop bundled hamlib helper binaries; use system hamlib
rm -f %{buildroot}%{_bindir}/rigctl*-ws

# Drop CMake test helper if it got installed
rm -f %{buildroot}%{_bindir}/inhibit-test

# Keep ALLCALL7.TXT in bindir (see %prep). Move only leftover TSV data.
mkdir -p %{buildroot}%{_datadir}/%{oname}
if [ -f %{buildroot}%{_bindir}/callsign_states.tsv ]; then
    mv %{buildroot}%{_bindir}/callsign_states.tsv %{buildroot}%{_datadir}/%{oname}/
fi
if [ -f %{buildroot}%{_bindir}/ALLCALL7.TXT ]; then
    cp -a %{buildroot}%{_bindir}/ALLCALL7.TXT %{buildroot}%{_datadir}/%{oname}/
fi

if [ -f %{buildroot}%{_datadir}/applications/%{oname}.desktop ]; then
    desktop-file-edit --set-key=Exec --set-value="ws --style=fusion" \
        %{buildroot}%{_datadir}/applications/%{oname}.desktop
    desktop-file-validate %{buildroot}%{_datadir}/applications/%{oname}.desktop
fi
if [ -f %{buildroot}%{_datadir}/applications/message_aggregator.desktop ]; then
    desktop-file-validate %{buildroot}%{_datadir}/applications/message_aggregator.desktop
fi

mkdir -p %{buildroot}%{_datadir}/doc/%{name}
echo "WS %{version} snapshot %{snapshot} (Qt6)" \
    > %{buildroot}%{_datadir}/doc/%{name}/PLUS_VERSION.txt

%files
%license %{oname}/COPYING
%doc %{oname}/NEWS %{oname}/README %{oname}/THANKS
%doc %{_datadir}/doc/%{name}
%{_bindir}/*
%{_datadir}/applications/ws.desktop
%{_datadir}/applications/message_aggregator.desktop
%{_datadir}/pixmaps/ws_icon.png
%{_datadir}/%{oname}/

%changelog
* Tue Sep 29 2026 Jim Howard <xsnrg@users.noreply.github.com> - 3.2.1-1.260926
- Track WS 3.2.1 snapshot 260926
- Source layout changed: WS_vVERSION/Source code/ws-VERSION_SNAPSHOT.tgz

* Sun Sep 27 2026 Jim Howard <xsnrg@users.noreply.github.com> - 3.2.0-7.260924
- Install sounds under /usr/share/ws, not /usr/share/wsjtx

* Sun Sep 27 2026 Jim Howard <xsnrg@users.noreply.github.com> - 3.2.0-6.260924
- Rename the package from wsjtx-improved to ws

* Sun Sep 27 2026 Jim Howard <xsnrg@users.noreply.github.com> - 3.2.0-5.260924
- Track upstream WS rename: ws-3.2.0_260924_qt6.tgz

* Tue Sep 08 2026 Jim Howard <xsnrg@users.noreply.github.com> - 3.2.0-5.260908
- Always resolve the newest Qt6 PLUS tarball when generating the SRPM
- Rebuild against PLUS snapshot 260908

* Wed Aug 26 2026 Jim Howard <xsnrg@users.noreply.github.com> - 3.2.0-4.260818
- Override CMake -z noexecstack / as --noexecstack so jt9 is RWE

* Sat Aug 22 2026 Jim Howard <xsnrg@users.noreply.github.com> - 3.2.0-3.260818
- jt9 decode crash: -ftrampoline-impl=heap and -Wl,-z,execstack

* Sat Aug 22 2026 Jim Howard <xsnrg@users.noreply.github.com> - 3.2.0-2.260818
- Keep ALLCALL7.TXT in bindir and open it read-only via exe_dir (jt9 -e)

* Sat Aug 22 2026 Jim Howard <xsnrg@users.noreply.github.com> - 3.2.0-1.260818
- Initial Copr package of WSJT-X Improved PLUS 3.2.0 (260818, Qt6)
- Conflicts with official Fedora wsjtx
- Use xsnrg/hamlib (>= 4.7.2), drop bundled hamlib and rigctl-wsjtx helpers
- Skip manpages (a2x) for the initial Copr builds
- Package map65 and cmake-installed data; create docdir before PLUS_VERSION.txt
