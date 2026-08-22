# WSJT-X Improved PLUS (DG2YCB) for Fedora Copr
# Source is the official Qt6 PLUS tarball from SourceForge.
# Bump Version / snapshot together when a newer PLUS drop appears.

%define snapshot 260818
%define oname    wsjtx

# Fortran trampolines still need an executable stack on gfortran
%undefine _hardened_linker_errors

Name:           wsjtx-improved
Version:        3.2.0
Release:        1.%{snapshot}%{?dist}
Summary:        WSJT-X Improved PLUS by DG2YCB (weak-signal amateur radio)

License:        GPL-3.0-or-later
URL:            https://sourceforge.net/projects/wsjt-x-improved
Source0:        https://downloads.sourceforge.net/project/wsjt-x-improved/WSJT-X_v%{version}/Source%%20code/Qt6/%{oname}-%{version}_improved_PLUS_%{snapshot}_qt6.tgz

ExcludeArch:    i686

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  gcc-gfortran
BuildRequires:  make
BuildRequires:  desktop-file-utils
BuildRequires:  dos2unix
BuildRequires:  pkgconfig
# Copr builds should resolve this from xsnrg/hamlib. 3.2.0 PLUS tracks 4.7.2.
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

Conflicts:      wsjtx
Provides:       wsjtx = %{version}-%{release}

%description
WSJT-X Improved PLUS is an enhanced edition of WSJT-X published by
Uwe Risse, DG2YCB. It keeps the familiar WSJT-X workflow and adds
features such as CQ/73 highlighting, mode buttons, band hopping,
DX-oriented FT8/FT4 decoding, False Decodes Reduction, Wait and
Reply/Call, audible alerts, and Cloudlog support.

This package is built from the Qt6 PLUS source tarball and conflicts
with Fedora's official wsjtx package because both install /usr/bin/wsjtx.

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

# Keep data files out of bindir
sed -i -z -e 's@install (DIRECTORY\n  ${PROJECT_SOURCE_DIR}/sounds\n  DESTINATION ${CMAKE_INSTALL_BINDIR}@install (DIRECTORY\n  ${PROJECT_SOURCE_DIR}/sounds\n  DESTINATION ${CMAKE_INSTALL_DATADIR}/${CMAKE_PROJECT_NAME}@g' CMakeLists.txt
sed -i -z -e 's@install (FILES\n  ALLCALL7.TXT\n  DESTINATION ${CMAKE_INSTALL_BINDIR}@install (FILES\n  ALLCALL7.TXT\n  DESTINATION ${CMAKE_INSTALL_DATADIR}/${CMAKE_PROJECT_NAME}@g' CMakeLists.txt

%build
# Fortran in this tree is not LTO-safe
%define _lto_cflags %{nil}

export CFLAGS="%{optflags} -fcommon -Wno-error=deprecated-declarations -Wno-error=unused-result -Wno-error=format-security -Wno-error=maybe-uninitialized"
export CXXFLAGS="%{optflags} -Wno-error=deprecated-declarations -Wno-error=unused-result -Wno-error=format-security -Wno-error=maybe-uninitialized"
export FFLAGS="%{optflags} -fPIC -fallow-argument-mismatch -std=legacy"
export FCFLAGS="%{optflags} -fPIC -fallow-argument-mismatch -std=legacy"
export FC=/usr/bin/gfortran
export PKG_CONFIG_ALLOW_SYSTEM_LIBS=1

cd %{oname}
%cmake \
    -Dhamlib_STATIC=FALSE \
    -DWSJT_GENERATE_DOCS=OFF \
    -DBoost_NO_SYSTEM_PATHS=FALSE \
    -DBOOST_INCLUDEDIR=%{_includedir}/boost \
    -DBOOST_LIBRARYDIR=%{_libdir}

%cmake_build

%install
cd %{oname}
%cmake_install

# Drop bundled hamlib helper binaries; use system hamlib
rm -f %{buildroot}%{_bindir}/rigctl*-wsjtx

# Drop CMake test helper if it got installed
rm -f %{buildroot}%{_bindir}/inhibit-test

if [ -f %{buildroot}%{_datadir}/applications/%{oname}.desktop ]; then
    desktop-file-edit --set-key=Exec --set-value="wsjtx --style=fusion" \
        %{buildroot}%{_datadir}/applications/%{oname}.desktop
    desktop-file-validate %{buildroot}%{_datadir}/applications/%{oname}.desktop
fi
if [ -f %{buildroot}%{_datadir}/applications/message_aggregator.desktop ]; then
    desktop-file-validate %{buildroot}%{_datadir}/applications/message_aggregator.desktop
fi

install -p -m 0644 -t %{buildroot}%{_datadir}/doc/%{name} \
    GUIcontrols.txt jt9.txt v1.7_Features.txt wsjtx_changelog.txt NEWS README THANKS 2>/dev/null || :
echo "WSJT-X Improved PLUS %{version} snapshot %{snapshot} (Qt6)" > %{buildroot}%{_datadir}/doc/%{name}/PLUS_VERSION.txt

%files
%license COPYING
%doc %{_datadir}/doc/%{name}
%{_bindir}/cablog
%{_bindir}/EchoCallSim
%{_bindir}/echosim
%{_bindir}/fcal
%{_bindir}/fmeasure
%{_bindir}/fmtave
%{_bindir}/fst4sim
%{_bindir}/ft8code
%{_bindir}/ft8sim
%{_bindir}/hash22calc
%{_bindir}/jt4code
%{_bindir}/jt65code
%{_bindir}/jt9
%{_bindir}/jt9code
%{_bindir}/message_aggregator
%{_bindir}/msk144code
%{_bindir}/q65code
%{_bindir}/q65sim
%{_bindir}/qmap
%{_bindir}/testEchoCall
%{_bindir}/udp_daemon
%{_bindir}/wsjtx
%{_bindir}/wsjtx_app_version
%{_bindir}/wsprd
%{_datadir}/applications/wsjtx.desktop
%{_datadir}/applications/message_aggregator.desktop
%{_datadir}/pixmaps/wsjtx_icon.png
%{_datadir}/%{oname}

%changelog
* Sat Aug 22 2026 Jim Howard <xsnrg@users.noreply.github.com> - 3.2.0-1.260818
- Initial Copr package of WSJT-X Improved PLUS 3.2.0 (260818, Qt6)
- Conflicts with official Fedora wsjtx
- Use xsnrg/hamlib (>= 4.7.2), drop bundled hamlib and rigctl-wsjtx helpers
