{pkgs}: {
  deps = [
    pkgs.python311Packages.xvfbwrapper
    pkgs.chromium
    pkgs.glibcLocales
    pkgs.postgresql
    pkgs.openssl
  ];
}
