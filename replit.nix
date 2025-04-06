{pkgs}: {
  deps = [
    pkgs.imagemagick
    pkgs.python311Packages.xvfbwrapper
    pkgs.chromium
    pkgs.glibcLocales
    pkgs.postgresql
    pkgs.openssl
  ];
}
