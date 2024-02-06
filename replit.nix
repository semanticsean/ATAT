{ pkgs }: {
  deps = [
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.rustc
    ];
  };
}