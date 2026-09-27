"""Build the VoxLabs desktop app for this computer's operating system:

    uv run build          (the `build` command from [project.scripts]; same as uv run scripts/build.py)

1. PyInstaller bundles the app: dist/VoxLabs/ (Windows, Linux) or dist/VoxLabs.app (macOS).
2. The bundle is started once with `--self-test` (offscreen) to prove it runs.
3. It is packaged for download, as a portable package and as installers:
       Windows  VoxLabs-Windows-x64.zip, VoxLabs-Windows-x64-Setup.exe (Inno Setup), VoxLabs-Windows-x64.msi (WiX)
       macOS    VoxLabs-macOS-arm64.dmg, VoxLabs-macOS-arm64.pkg (pkgbuild)
       Linux    VoxLabs-Linux-x86_64.tar.gz, VoxLabs-Linux-x86_64.deb (dpkg-deb), VoxLabs-Linux-x86_64.rpm (rpmbuild)
   An installer whose tool is missing is skipped with a hint (--require-installers makes that an error).

PyInstaller cannot cross-compile: build the .exe on Windows, the .dmg on macOS and the Linux
archive on Linux (.github/workflows/desktop.yml builds all three). Engines installed in the
environment are bundled too, e.g. `uv sync --extra piper --extra kokoro` first.

The app icon is rendered from the same logo the app draws at runtime (app/ui/icons.py), as .ico
on Windows and .icns on macOS; Linux reads the window icon at runtime.
"""

import argparse
import os
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
DIST = ROOT / "dist"
ICON_DIR = BUILD / "icon"
HOMEPAGE = "https://github.com/nishanth-kj/VoxLabs"
SUMMARY = "Local-first voice cloning, text-to-speech and audio studio"
DESCRIPTION = ("VoxLabs clones voices with recorded consent, turns text and scripts into speech and "
               "edits audio, all on this computer.")


def _png(pixels: int) -> bytes:
    from PySide6.QtCore import QBuffer, QIODevice
    from PySide6.QtGui import QImageWriter

    from app.ui.icons import logo_image

    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    QImageWriter(buffer, b"PNG").write(logo_image(pixels))
    return bytes(buffer.data().data())


def _write_ico(path: Path) -> Path:
    """A multi-size .ico with PNG entries (supported since Windows Vista)."""
    images = [(size, _png(size)) for size in (16, 24, 32, 48, 64, 128, 256)]
    offset = 6 + 16 * len(images)
    header = struct.pack("<HHH", 0, 1, len(images))
    entries, data = b"", b""
    for size, png in images:
        side = 0 if size >= 256 else size  # 0 means 256 in the ICO directory
        entries += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(png), offset + len(data))
        data += png
    path.write_bytes(header + entries + data)
    return path


def _write_icns(path: Path) -> Path:
    iconset = ICON_DIR / "VoxLabs.iconset"
    iconset.mkdir(parents=True, exist_ok=True)
    for size in (16, 32, 128, 256, 512):
        (iconset / f"icon_{size}x{size}.png").write_bytes(_png(size))
        (iconset / f"icon_{size}x{size}@2x.png").write_bytes(_png(size * 2))
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(path)], check=True)
    return path


def app_icon_file() -> Path | None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    sys.path.insert(0, str(ROOT))
    from PySide6.QtGui import QGuiApplication

    _app = QGuiApplication.instance() or QGuiApplication([])  # noqa: F841 - SVG rendering needs one
    shutil.rmtree(ICON_DIR, ignore_errors=True)
    ICON_DIR.mkdir(parents=True)
    if sys.platform == "win32":
        return _write_ico(ICON_DIR / "VoxLabs.ico")
    if sys.platform == "darwin":
        return _write_icns(ICON_DIR / "VoxLabs.icns")
    (ICON_DIR / "VoxLabs.png").write_bytes(_png(256))  # for the .deb/.rpm menu entry
    return None


def bundle() -> int:
    """Run PyInstaller; the bundle lands in dist/."""
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name", "VoxLabs",
        "--paths", str(ROOT),
        "--specpath", str(BUILD),
        "--workpath", str(BUILD / "pyinstaller"),
        "--distpath", str(DIST),
        "--collect-data", "librosa",
        "--collect-submodules", "app",
    ]
    icon = app_icon_file()
    if icon:
        command += ["--icon", str(icon)]
    if sys.platform == "darwin":
        command += ["--osx-bundle-identifier", "app.voxlabs.desktop"]
    command.append(str(ROOT / "app" / "main.py"))
    print(" ".join(command), flush=True)
    return subprocess.call(command, cwd=ROOT)


def executable() -> Path:
    if sys.platform == "win32":
        return DIST / "VoxLabs" / "VoxLabs.exe"
    if sys.platform == "darwin":
        return DIST / "VoxLabs.app" / "Contents" / "MacOS" / "VoxLabs"
    return DIST / "VoxLabs" / "VoxLabs"


def self_test() -> int:
    """Start the built app offscreen with a throwaway data folder; it builds every page and quits.

    On failure the app's crash report (the traceback a windowed app cannot print) is shown.
    """
    with tempfile.TemporaryDirectory(prefix="voxlabs-selftest-") as data:
        report = Path(data) / "crash.txt"
        env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "VOXLABS_DATA_DIR": data,
               "VOXLABS_CRASH_REPORT": str(report)}
        # On Windows, start it detached like a double-click: no console, so sys.stdout/stderr are None
        # inside, which is how users run it (and what breaks libraries that print).
        flags = subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0
        try:
            result = subprocess.run([str(executable()), "--self-test"], env=env, timeout=300, creationflags=flags)
        except subprocess.TimeoutExpired:
            print("Self-test timed out: the built app did not quit.", file=sys.stderr)
            return 1
        if result.returncode == 0:
            print("Self-test passed.", flush=True)
            return 0
        print(f"Self-test failed (exit {result.returncode}).", file=sys.stderr)
        if report.exists():
            print(report.read_text(encoding="utf-8"), file=sys.stderr)
        return result.returncode or 1


def _pyproject() -> dict:
    with open(ROOT / "pyproject.toml", "rb") as file:
        return tomllib.load(file)


def version() -> str:
    return _pyproject()["project"]["version"]


def build_engines() -> list[str]:
    return list(_pyproject().get("tool", {}).get("voxlabs", {}).get("build-engines", []))


def sync_engines(engines: list[str]) -> int:
    """Put the bundled engines into the environment at their uv.lock versions.

    `uv run` first syncs the environment without extras, which also moves libraries the engines
    share with the app (numpy, librosa, ...) to the no-extras versions; Chatterbox needs other ones.
    Syncing the engines again (keeping everything else) makes the bundle match the lock.
    """
    if not engines:
        return 0
    uv = shutil.which("uv")
    if not uv:
        print("uv not found: bundling whatever engines are installed.", file=sys.stderr)
        return 0
    command = [uv, "sync", "--frozen", "--inexact"] + [arg for engine in engines for arg in ("--extra", engine)]
    print(" ".join(command), flush=True)
    return subprocess.call(command, cwd=ROOT)


def artifact_names(system: str = sys.platform, machine: str | None = None) -> list[str]:
    """Every file one build makes: the portable package first, then the installers."""
    base = package_name(system, machine).rsplit(".", 2 if system not in ("win32", "darwin") else 1)[0]
    if system == "win32":
        return [package_name(system, machine), f"{base}-Setup.exe", f"{base}.msi"]
    if system == "darwin":
        return [package_name(system, machine), f"{base}.pkg"]
    return [package_name(system, machine), f"{base}.deb", f"{base}.rpm"]


def _tool(name: str, *fallbacks: Path) -> str | None:
    found = shutil.which(name)
    return found or next((str(path) for path in fallbacks if path.exists()), None)


# ---------------------------------------------------------------- Windows: Setup.exe (Inno Setup)

INNO_SCRIPT = r"""
[Setup]
AppId={{7C6F2B84-3E0B-4D1A-9E67-2F1B5A0C9D41}
AppName=VoxLabs
AppVersion=@VERSION@
AppVerName=VoxLabs @VERSION@
AppPublisher=VoxLabs
AppPublisherURL=@HOMEPAGE@
AppSupportURL=@HOMEPAGE@/issues
DefaultDirName={autopf}\VoxLabs
DefaultGroupName=VoxLabs
DisableProgramGroupPage=yes
; Per-user by default (no admin prompt); the first page offers an install for all users.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=@DIST@
OutputBaseFilename=@NAME@
SetupIconFile=@ICON@
UninstallDisplayIcon={app}\VoxLabs.exe
LicenseFile=@LICENSE@
Compression=lzma2/fast
SolidCompression=no
ArchitecturesAllowed=@ARCH@
ArchitecturesInstallIn64BitMode=@ARCH@
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "@APP@\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\VoxLabs"; Filename: "{app}\VoxLabs.exe"; AppUserModelID: "VoxLabs.Desktop"
Name: "{autodesktop}\VoxLabs"; Filename: "{app}\VoxLabs.exe"; Tasks: desktopicon; AppUserModelID: "VoxLabs.Desktop"

[Run]
Filename: "{app}\VoxLabs.exe"; Description: "{cm:LaunchProgram,VoxLabs}"; Flags: nowait postinstall skipifsilent
"""


def windows_setup(name: str) -> Path | None:
    iscc = _tool("iscc", Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
                 Path(os.environ.get("ProgramFiles(x86)", "")) / "Inno Setup 6" / "ISCC.exe",
                 Path(os.environ.get("ProgramFiles", "")) / "Inno Setup 6" / "ISCC.exe")
    if not iscc:
        print("Skipping Setup.exe: Inno Setup is not installed (winget install JRSoftware.InnoSetup).", file=sys.stderr)
        return None
    script = BUILD / "VoxLabs.iss"
    values = {"@VERSION@": version(), "@HOMEPAGE@": HOMEPAGE, "@DIST@": str(DIST), "@NAME@": Path(name).stem,
              "@ICON@": str(ICON_DIR / "VoxLabs.ico"), "@LICENSE@": str(ROOT / "LICENSE"),
              "@APP@": str(DIST / "VoxLabs"), "@ARCH@": "arm64" if arch() == "arm64" else "x64compatible"}
    text = INNO_SCRIPT
    for key, value in values.items():
        text = text.replace(key, value)
    script.write_text(text, encoding="utf-8")
    subprocess.run([iscc, "/Q", str(script)], check=True)
    return DIST / name


# ---------------------------------------------------------------- Windows: .msi (WiX 5)

WIX_SOURCE = r"""<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">
  <Package Name="VoxLabs" Manufacturer="VoxLabs" Version="@VERSION@"
           UpgradeCode="3F2C1E6A-8B7D-4C59-A1E0-5D9B7C4F2A18" Compressed="yes">
    <MajorUpgrade DowngradeErrorMessage="A newer version of VoxLabs is already installed." />
    <!-- Several embedded cabinets: one cabinet cannot hold more than 2 GB. -->
    <MediaTemplate EmbedCab="yes" MaximumUncompressedMediaSize="1024" />
    <Icon Id="VoxLabsIcon" SourceFile="@ICON@" />
    <Property Id="ARPPRODUCTICON" Value="VoxLabsIcon" />
    <Property Id="ARPURLINFOABOUT" Value="@HOMEPAGE@" />
    <StandardDirectory Id="ProgramFiles64Folder">
      <Directory Id="INSTALLFOLDER" Name="VoxLabs" />
    </StandardDirectory>
    <StandardDirectory Id="ProgramMenuFolder">
      <Component Id="StartMenuShortcut">
        <Shortcut Id="VoxLabsShortcut" Name="VoxLabs" Target="[INSTALLFOLDER]VoxLabs.exe"
                  WorkingDirectory="INSTALLFOLDER" Icon="VoxLabsIcon" />
        <RegistryValue Root="HKCU" Key="Software\VoxLabs" Name="StartMenuShortcut" Type="integer" Value="1"
                       KeyPath="yes" />
      </Component>
    </StandardDirectory>
    <Feature Id="Main" Title="VoxLabs">
      <Files Directory="INSTALLFOLDER" Include="!(bindpath.App)\**" />
      <ComponentRef Id="StartMenuShortcut" />
    </Feature>
  </Package>
</Wix>
"""


def windows_msi(name: str) -> Path | None:
    home = Path.home()
    wix = _tool("wix", home / ".dotnet" / "tools" / "wix.exe")
    if not wix:
        print("Skipping .msi: WiX is not installed (dotnet tool install --global wix --version 5.0.2).",
              file=sys.stderr)
        return None
    env = dict(os.environ)
    user_dotnet = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "dotnet"
    if "DOTNET_ROOT" not in env and (user_dotnet / "dotnet.exe").exists():
        env["DOTNET_ROOT"] = str(user_dotnet)  # a per-user .NET install, which the wix tool cannot find alone
    source = BUILD / "VoxLabs.wxs"
    text = WIX_SOURCE
    for key, value in {"@VERSION@": version(), "@ICON@": str(ICON_DIR / "VoxLabs.ico"), "@HOMEPAGE@": HOMEPAGE}.items():
        text = text.replace(key, value)
    source.write_text(text, encoding="utf-8")
    target = DIST / name
    subprocess.run([wix, "build", str(source), "-arch", "arm64" if arch() == "arm64" else "x64",
                    "-bindpath", f"App={DIST / 'VoxLabs'}", "-o", str(target)], check=True, env=env)
    target.with_suffix(".wixpdb").unlink(missing_ok=True)  # debug symbols, not for download
    return target


# ---------------------------------------------------------------- macOS: .pkg

def mac_pkg(name: str) -> Path | None:
    if not shutil.which("pkgbuild"):
        print("Skipping .pkg: pkgbuild is part of the Xcode command line tools.", file=sys.stderr)
        return None
    target = DIST / name
    subprocess.run(["pkgbuild", "--component", str(DIST / "VoxLabs.app"), "--install-location", "/Applications",
                    "--identifier", "app.voxlabs.desktop", "--version", version(), str(target)], check=True)
    return target


# ---------------------------------------------------------------- Linux: .deb and .rpm

DESKTOP_ENTRY = """[Desktop Entry]
Type=Application
Name=VoxLabs
Comment=@SUMMARY@
Exec=/opt/voxlabs/VoxLabs
Icon=voxlabs
Terminal=false
Categories=AudioVideo;Audio;
StartupWMClass=VoxLabs
"""


def _linux_tree(root: Path) -> None:
    """The installed layout: the app in /opt/voxlabs, a `voxlabs` command, a menu entry and an icon."""
    shutil.copytree(DIST / "VoxLabs", root / "opt" / "voxlabs", symlinks=True)
    (root / "usr" / "bin").mkdir(parents=True)
    (root / "usr" / "bin" / "voxlabs").symlink_to("/opt/voxlabs/VoxLabs")
    menu = root / "usr" / "share" / "applications"
    menu.mkdir(parents=True)
    (menu / "voxlabs.desktop").write_text(DESKTOP_ENTRY.replace("@SUMMARY@", SUMMARY), encoding="utf-8")
    icons = root / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
    icons.mkdir(parents=True)
    shutil.copy(ICON_DIR / "VoxLabs.png", icons / "voxlabs.png")


def linux_deb(name: str) -> Path | None:
    if not shutil.which("dpkg-deb"):
        print("Skipping .deb: dpkg-deb is not installed.", file=sys.stderr)
        return None
    shutil.rmtree(BUILD / "deb", ignore_errors=True)
    root = BUILD / "deb" / "voxlabs"
    _linux_tree(root)
    size_kb = sum(f.stat().st_size for f in (root / "opt").rglob("*") if f.is_file() and not f.is_symlink()) // 1024
    (root / "DEBIAN").mkdir()
    (root / "DEBIAN" / "control").write_text(
        f"Package: voxlabs\nVersion: {version()}\nSection: sound\nPriority: optional\n"
        f"Architecture: {'arm64' if arch() == 'aarch64' else 'amd64'}\nInstalled-Size: {size_kb}\n"
        "Depends: libc6 (>= 2.35), libegl1, libxkbcommon-x11-0, libxcb-cursor0, libfontconfig1, libpulse0\n"
        f"Maintainer: VoxLabs <privacy@voxlabs.ai>\nHomepage: {HOMEPAGE}\n"
        f"Description: {SUMMARY}\n {DESCRIPTION}\n", encoding="utf-8")
    target = DIST / name
    subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(root), str(target)], check=True)
    return target


def linux_rpm(name: str) -> Path | None:
    if not shutil.which("rpmbuild"):
        print("Skipping .rpm: rpmbuild is not installed (Debian/Ubuntu: apt install rpm).", file=sys.stderr)
        return None
    top = BUILD / "rpm"
    shutil.rmtree(top, ignore_errors=True)
    stage = top / "stage"
    _linux_tree(stage)
    spec = top / "voxlabs.spec"
    # The bundle ships its own libraries: no dependency scan, no stripping, no debug package.
    spec.write_text(f"""Name: voxlabs
Version: {version()}
Release: 1
Summary: {SUMMARY}
License: MIT
URL: {HOMEPAGE}
AutoReqProv: no
Requires: fontconfig, libxkbcommon-x11, xcb-util-cursor, mesa-libEGL, pulseaudio-libs
%global debug_package %{{nil}}
%global __os_install_post %{{nil}}
%global _build_id_links none

%description
{DESCRIPTION}

%install
cp -a {stage}/. %{{buildroot}}/

%files
/opt/voxlabs
/usr/bin/voxlabs
/usr/share/applications/voxlabs.desktop
/usr/share/icons/hicolor/256x256/apps/voxlabs.png
""", encoding="utf-8")
    subprocess.run(["rpmbuild", "-bb", "--define", f"_topdir {top}", "--target", arch(), str(spec)], check=True)
    target = DIST / name
    shutil.move(next((top / "RPMS").rglob("*.rpm")), target)
    return target


def installers(require: bool) -> list[Path]:
    """This OS's installers; a missing tool skips its installer (or fails with `require`)."""
    names = artifact_names()[1:]
    if sys.platform == "win32":
        makers = [windows_setup, windows_msi]
    elif sys.platform == "darwin":
        makers = [mac_pkg]
    else:
        makers = [linux_deb, linux_rpm]
    built = [made for make, name in zip(makers, names) if (made := make(name))]
    if require and len(built) < len(names):
        raise SystemExit("Not every installer could be built (see the messages above).")
    return built


LOCK = BUILD / ".build.lock"


def _pid_alive(pid: int) -> bool:
    if sys.platform == "win32":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def bundle_in_use() -> bool:
    """Windows cannot replace an app that is running; building then fails halfway through."""
    if sys.platform != "win32" or not executable().exists():
        return False
    try:
        with open(executable(), "r+b"):
            return False
    except PermissionError:
        return True


def take_lock() -> bool:
    """One build at a time: two builds write the same build/ and dist/ folders and break each other."""
    BUILD.mkdir(parents=True, exist_ok=True)
    try:
        owner = int(LOCK.read_text(encoding="utf-8").strip() or 0)
    except (OSError, ValueError):
        owner = 0
    if owner and owner != os.getpid() and _pid_alive(owner):
        print(f"Another build is running (process {owner}). Wait for it to finish.", file=sys.stderr)
        return False
    LOCK.write_text(str(os.getpid()), encoding="utf-8")  # free, or left behind by a build that was killed
    return True


def arch(system: str = sys.platform, machine: str | None = None) -> str:
    machine = (machine or platform.machine()).lower()
    if machine in ("amd64", "x86_64", "x64"):
        return "x64" if system == "win32" else "x86_64"
    if machine in ("arm64", "aarch64"):
        return "aarch64" if system.startswith("linux") else "arm64"
    return machine


def package_name(system: str = sys.platform, machine: str | None = None) -> str:
    """The download's file name; it matches the GitHub release assets the website links to."""
    name = {"win32": "Windows", "darwin": "macOS"}.get(system, "Linux")
    extension = {"win32": "zip", "darwin": "dmg"}.get(system, "tar.gz")
    return f"VoxLabs-{name}-{arch(system, machine)}.{extension}"


def package() -> Path:
    """The download for this operating system (named like the GitHub release assets)."""
    target = DIST / package_name()
    target.unlink(missing_ok=True)
    if sys.platform == "win32":
        shutil.make_archive(str(target.with_suffix("")), "zip", DIST, "VoxLabs")
    elif sys.platform == "darwin":
        stage = BUILD / "dmg"
        shutil.rmtree(stage, ignore_errors=True)
        stage.mkdir(parents=True)
        shutil.copytree(DIST / "VoxLabs.app", stage / "VoxLabs.app", symlinks=True)
        (stage / "Applications").symlink_to("/Applications")  # drag-to-install
        subprocess.run(["hdiutil", "create", "-volname", "VoxLabs", "-srcfolder", str(stage), "-ov",
                        "-format", "UDZO", str(target)], check=True)
    else:
        shutil.make_archive(str(target).removesuffix(".tar.gz"), "gztar", DIST, "VoxLabs")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the VoxLabs desktop app for this operating system.")
    parser.add_argument("--no-package", action="store_true", help="stop after the bundle in dist/ (no .zip/.dmg/.tar.gz)")
    parser.add_argument("--skip-self-test", action="store_true", help="do not start the built app to check it")
    parser.add_argument("--no-installer", action="store_true", help="make only the portable package")
    parser.add_argument("--engines", help="comma-separated engines to bundle (default: [tool.voxlabs] "
                        "build-engines in pyproject.toml); 'none' bundles only the base engines")
    parser.add_argument("--package-only", action="store_true",
                        help="reuse the bundle already in dist/: skip PyInstaller and the self-test")
    parser.add_argument("--require-installers", action="store_true",
                        help="fail when an installer's tool is missing (CI)")
    args = parser.parse_args()

    if not take_lock():
        return 1
    if bundle_in_use():
        print(f"VoxLabs is running from {executable().parent}: close it first, the build replaces that folder.",
              file=sys.stderr)
        LOCK.unlink(missing_ok=True)
        return 1
    try:
        if args.package_only:
            if not executable().exists():
                print(f"No bundle to package: {executable()} is missing. Run without --package-only.",
                      file=sys.stderr)
                return 1
            app_icon_file()  # the installers use the icon files
        else:
            engines = build_engines() if args.engines is None else \
                [e.strip() for e in args.engines.split(",") if e.strip() and e.strip() != "none"]
            code = sync_engines(engines) or bundle()
            if code:
                return code
            if not args.skip_self_test:
                code = self_test()
                if code:
                    return code
        if not args.no_package:
            built = [package()]
            if not args.no_installer:
                built += installers(args.require_installers)
            for target in built:
                print(f"Built {target} ({target.stat().st_size / 1_048_576:.0f} MB)", flush=True)
        return 0
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
